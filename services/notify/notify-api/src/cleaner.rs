use crate::repository;

use std::time::Duration;

use anyhow::{Context, Result};
use base64::Engine;
use reqwest::header;
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

pub struct CleanerOpts<'a> {
    pub timeout: Duration,
    pub interval: Duration,
    pub admin_addr: &'a str,
    pub notifier_username: &'a str,
    pub notifier_password: &'a str,
    pub max_user_age: Duration,
}

/// Cleaner periodically runs the DB & mail cleaning procedure in order to remove stale and unneeded users.
pub struct Cleaner {
    repository: repository::Repository,
    reqwest_client: reqwest::Client,
    interval: Duration,
    delete_url: String,
    max_user_age: Duration,
}

impl Cleaner {
    pub fn new(repository: repository::Repository, opts: CleanerOpts<'_>) -> Result<Self> {
        let notifier_credentials = base64::engine::general_purpose::STANDARD.encode(format!(
            "{}:{}",
            opts.notifier_username, opts.notifier_password
        ));

        let mut header_map = header::HeaderMap::new();
        header_map.insert(
            "Authorization",
            header::HeaderValue::from_str(&format!("Basic {notifier_credentials}"))
                .context("preparing reqwest client authorization")?,
        );

        let reqwest_client = reqwest::Client::builder()
            .timeout(opts.timeout)
            .default_headers(header_map)
            .build()
            .context("building reqwest client")?;

        let delete_url = format!("{}/admin/account/delete", opts.admin_addr);

        Ok(Self {
            repository,
            reqwest_client,
            interval: opts.interval,
            delete_url,
            max_user_age: opts.max_user_age,
        })
    }

    pub async fn run(self, cancel_token: CancellationToken) {
        loop {
            tokio::select! {
              () = cancel_token.cancelled() => {
                info!("cleaner shutting down due to cancellation");
                break;
              }

              () = tokio::time::sleep(self.interval) => {
                if let Err(e) = self.iteration_with_cancel(cancel_token.clone()).await {
                  error!(error=format!("{:#}", e), "unexpected error occurred during cleaner iteration");
                }
              }
            }
        }
    }

    async fn iteration_with_cancel(&self, cancel_token: CancellationToken) -> Result<()> {
        tokio::select! {
            () = cancel_token.cancelled() => {
                info!("cleaner iteration stopping due to cancellation");
                Ok(())
              }
            result = self.iteration() => {
                result
            }
        }
    }

    async fn iteration(&self) -> Result<()> {
        let old_account_usernames = self
            .repository
            .list_old_account_usernames(self.max_user_age)
            .await
            .context("retrieving batch of old accounts from repository")?;

        if !old_account_usernames.is_empty() {
            info!(
                "cleaner will delete {} old accounts",
                old_account_usernames.len()
            );
        }

        for username in &old_account_usernames {
            if let Err(e) = self.delete_user(username).await {
                error!(
                    error = format!("{:#}", e),
                    username = username,
                    "failed to delete old account"
                );
            }
        }

        Ok(())
    }

    async fn delete_user(&self, username: &str) -> Result<()> {
        let response = self
            .reqwest_client
            .get(format!("{}/{username}", self.delete_url))
            .send()
            .await
            .context("sending delete request to admin API")?;

        // OK if deleted now, can also be NOT_FOUND if deleted earlier but delete in the repo has failed.
        if response.status() != reqwest::StatusCode::OK
            && response.status() != reqwest::StatusCode::NOT_FOUND
        {
            anyhow::bail!(
                "delete request returned non-ok status code {}",
                response.status()
            );
        }

        self.repository
            .delete_account_by_username(username)
            .await
            .context("deleting account in the repository")?;

        Ok(())
    }
}
