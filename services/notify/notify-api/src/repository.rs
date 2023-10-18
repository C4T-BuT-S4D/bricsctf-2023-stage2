use anyhow::Result;
use sqlx::{postgres::PgPoolOptions, query, PgPool};
use std::time::Duration;
use tokio::time::timeout;

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
        match timeout(
            self.request_timeout,
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
}
