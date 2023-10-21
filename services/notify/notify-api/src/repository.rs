use anyhow::Result;
use sqlx::{postgres::PgPoolOptions, query, query_as, PgPool};
use std::{future::Future, time::Duration};
use tokio::time::{timeout, Timeout};

pub struct Account {
    pub username: String,
    pub password_hash: String,
}

/// Repository implementation on top of sqlx' postgres pool.
#[derive(Clone)]
pub struct Repository {
    pool: PgPool,
    request_timeout: Duration,
}

impl Repository {
    pub async fn connect(
        url: &str,
        connection_timeout: Duration,
        request_timeout: Duration,
        max_connections: u32,
    ) -> Result<Repository> {
        let pool = timeout(
            connection_timeout,
            PgPoolOptions::new()
                .max_connections(max_connections)
                .connect(url),
        )
        .await??;

        Ok(Repository {
            pool,
            request_timeout,
        })
    }

    pub async fn create_account(&self, account: Account) -> Result<bool> {
        match self
            .timeout(
                query!(
                    "insert into account (username, password_hash) values ($1, $2)",
                    &account.username,
                    &account.password_hash
                )
                .execute(&self.pool),
            )
            .await?
        {
            Ok(_) => Ok(true),
            Err(sqlx::Error::Database(db_error)) if db_error.is_unique_violation() => Ok(false),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    pub async fn get_account(&self, username: &str) -> Result<Option<Account>> {
        match self
            .timeout(
                query_as!(
                    Account,
                    "select username, password_hash from account where username = $1",
                    username
                )
                .fetch_one(&self.pool),
            )
            .await?
        {
            Ok(acc) => Ok(Some(acc)),
            Err(sqlx::Error::RowNotFound) => Ok(None),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    fn timeout<F>(&self, f: F) -> Timeout<F>
    where
        F: Future,
    {
        timeout(self.request_timeout, f)
    }
}
