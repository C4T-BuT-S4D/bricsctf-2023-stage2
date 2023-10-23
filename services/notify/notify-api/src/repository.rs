use anyhow::{bail, Result};
use sqlx::{postgres::PgPoolOptions, query, query_as, PgPool};
use std::{future::Future, time::Duration};
use time::OffsetDateTime;
use tokio::time::{timeout, Timeout};
use uuid::Uuid;

pub struct Account {
    pub username: String,
    pub password_hash: String,
}

pub struct NotificationRepetitions {
    pub count: u32,
    pub interval: time::Duration,
}

pub struct Notification {
    pub title: String,
    pub content: String,
    pub notify_at: OffsetDateTime,
    pub repetitions: Option<NotificationRepetitions>,
}

pub struct NotificationPlan {
    pub planned_at: OffsetDateTime,
    pub sent_at: Option<OffsetDateTime>,
}

pub struct NotificationInfo {
    pub title: String,
    pub content: String,
    pub plan: Vec<NotificationPlan>,
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

    pub async fn create_account(&self, account: &Account) -> Result<bool> {
        let q = query!(
            r#"INSERT INTO account (username, password_hash)
            VALUES ($1, $2)"#,
            &account.username,
            &account.password_hash
        );

        match self.timeout(q.execute(&self.pool)).await? {
            Ok(_) => Ok(true),
            Err(sqlx::Error::Database(db_error)) if db_error.is_unique_violation() => Ok(false),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    pub async fn get_account(&self, username: &str) -> Result<Option<Account>> {
        let q = query_as!(
            Account,
            r#"SELECT username, password_hash
            FROM account
            WHERE username = $1"#,
            username
        );

        match self.timeout(q.fetch_one(&self.pool)).await? {
            Ok(acc) => Ok(Some(acc)),
            Err(sqlx::Error::RowNotFound) => Ok(None),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    pub async fn create_notification(
        &self,
        username: &str,
        notification: &Notification,
    ) -> Result<Uuid> {
        let mut notify_times = vec![notification.notify_at];
        notify_times.extend(&notification.repetitions.as_ref().map_or(vec![], |r| {
            (1..=r.count)
                .map(|i| notification.notify_at + i * r.interval)
                .collect()
        }));

        let mut tx = self.timeout(self.pool.begin()).await??;

        let q = query!(
            r#"INSERT INTO notification (username, title, content)
            VALUES ($1, $2, $3)
            RETURNING id"#,
            username,
            &notification.title,
            &notification.content
        );
        let notification_id = self.timeout(q.fetch_one(&mut *tx)).await??.id;

        let q = query!(
            r#"INSERT INTO notification_queue (notification_id, planned_at)
            SELECT $1, * FROM UNNEST($2::timestamptz[])"#,
            &notification_id,
            &notify_times,
        );
        self.timeout(q.execute(&mut *tx)).await??;

        self.timeout(tx.commit()).await??;

        Ok(notification_id)
    }

    pub async fn get_notification_info(
        &self,
        notification_id: &Uuid,
    ) -> Result<Option<NotificationInfo>> {
        let q = query!(
            r#"SELECT
                n.title,
                n.content,
                ARRAY_AGG(nq.planned_at ORDER BY nq.planned_at) AS "planned_at!",
                ARRAY_AGG(nq.sent_at ORDER BY nq.planned_at) AS "sent_at!: Vec<Option<OffsetDateTime>>"
            FROM notification n
            JOIN notification_queue nq ON nq.notification_id = n.id
            WHERE n.id = $1
            GROUP BY n.id"#,
            notification_id
        );

        let notification_info = match self.timeout(q.fetch_one(&self.pool)).await? {
            Ok(ni) => ni,
            Err(sqlx::Error::RowNotFound) => return Ok(None),
            Err(e) => return Err(anyhow::Error::new(e)),
        };

        if notification_info.planned_at.len() != notification_info.sent_at.len() {
            bail!(
                "planned_at ({} elements) and sent_at ({} elements) have different length",
                notification_info.planned_at.len(),
                notification_info.sent_at.len()
            );
        }

        Ok(Some(NotificationInfo {
            title: notification_info.title,
            content: notification_info.content,
            plan: notification_info
                .planned_at
                .iter()
                .zip(notification_info.sent_at.iter())
                .map(|(planned_at, sent_at)| NotificationPlan {
                    planned_at: *planned_at,
                    sent_at: *sent_at,
                })
                .collect(),
        }))
    }

    fn timeout<F>(&self, f: F) -> Timeout<F>
    where
        F: Future,
    {
        timeout(self.request_timeout, f)
    }
}
