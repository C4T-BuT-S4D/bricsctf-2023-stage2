use crate::repository;

use anyhow::{Context, Result};
use std::time::Duration;
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

pub struct Notifier {
    repository: repository::Repository,
    interval: Duration,
    email: String,
    domain: String,
    server_name: String,
}

impl Notifier {
    pub async fn new(
        repository: repository::Repository,
        interval: Duration,
        username: String,
        domain: String,
        server_name: String,
    ) -> Result<Self> {
        repository
            .reset_notification_queue()
            .await
            .with_context(|| "resetting current notification queue")?;

        Ok(Self {
            repository,
            interval,
            email: format!("{}@{}", username, domain),
            domain,
            server_name,
        })
    }

    pub async fn run(self, cancel_token: CancellationToken) {
        loop {
            tokio::select! {
              _ = cancel_token.cancelled() => {
                info!("notifier shutting down due to cancellation");
                break;
              }

              _ = tokio::time::sleep(self.interval) => {
                if let Err(e) = self.iteration().await {
                  error!(error=format!("{:#}", e), "unexpected error occurred during notifier iteration");
                }
              }
            }
        }
    }

    async fn iteration(&self) -> Result<()> {
        let batch = self
            .repository
            .reserve_notification_queue_batch()
            .await
            .with_context(|| "reserving batch in notification queue")?;

        info!("reserved {} elements", batch.len());

        Ok(())
    }
}
