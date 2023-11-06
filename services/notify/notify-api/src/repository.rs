use std::future::Future;

use anyhow::Result;
use sqlx::{postgres::PgPoolOptions, query, query_as, PgPool};
use time::{Duration, OffsetDateTime};
use tokio::time::{timeout, Timeout};
use uuid::Uuid;

pub struct NotificationCreationRepetitions {
    pub count: u32,
    pub interval: Duration,
}

pub struct NotificationCreationOpts<'a> {
    pub title: &'a str,
    pub content: &'a str,
    pub notify_at: OffsetDateTime,
    pub repetitions: Option<NotificationCreationRepetitions>,
}

struct RepoNotification {
    id: Uuid,
    title: String,
    content: String,
    plan: Vec<(OffsetDateTime, Option<OffsetDateTime>)>,
}

pub struct NotificationPlan {
    pub planned_at: OffsetDateTime,
    pub sent_at: Option<OffsetDateTime>,
}

pub struct Notification {
    pub id: Uuid,
    pub title: String,
    pub content: String,
    pub plan: Vec<NotificationPlan>,
}

pub struct NotificationQueueElement {
    pub id: Uuid,
    pub username: String,
    pub title: String,
    pub content: String,
    pub planned_at: OffsetDateTime,
}

#[derive(sqlx::Type)]
#[sqlx(type_name = "notification_state", rename_all = "lowercase")]
enum NotificationState {
    Planned,
    InProgress,
    Sent,
    Failed,
}

impl From<RepoNotification> for Notification {
    fn from(value: RepoNotification) -> Self {
        Self {
            id: value.id,
            title: value.title,
            content: value.content,
            plan: value
                .plan
                .iter()
                .map(|(planned_at, sent_at)| NotificationPlan {
                    planned_at: *planned_at,
                    sent_at: *sent_at,
                })
                .collect(),
        }
    }
}

/// Repository implementation on top of sqlx' postgres pool.
#[derive(Clone)]
pub struct Repository {
    pool: PgPool,
    request_timeout: std::time::Duration,
}

impl Repository {
    pub async fn connect(
        url: &str,
        connect_timeout: std::time::Duration,
        request_timeout: std::time::Duration,
        max_connections: u32,
    ) -> Result<Self> {
        let pool = timeout(
            connect_timeout,
            PgPoolOptions::new()
                .max_connections(max_connections)
                .connect(url),
        )
        .await??;

        Ok(Self {
            pool,
            request_timeout,
        })
    }

    pub async fn close(&self) {
        self.pool.close().await;
    }

    /// Create a new account, returning true if an account with such username already exists.
    pub async fn create_account(&self, username: &str, password_hash: &str) -> Result<bool> {
        let q = query!(
            r#"INSERT INTO account (username, password_hash)
            VALUES ($1, $2)"#,
            &username,
            &password_hash
        );

        match self.timeout(q.execute(&self.pool)).await? {
            Ok(_) => Ok(true),
            Err(sqlx::Error::Database(db_error)) if db_error.is_unique_violation() => Ok(false),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    /// Get the password hash of an account by its username, returning None, if no account with such username exists.
    pub async fn get_account_password_hash(&self, username: &str) -> Result<Option<String>> {
        let q = query!(
            r#"SELECT password_hash
            FROM account
            WHERE username = $1"#,
            username
        );

        match self.timeout(q.fetch_one(&self.pool)).await? {
            Ok(acc) => Ok(Some(acc.password_hash)),
            Err(sqlx::Error::RowNotFound) => Ok(None),
            Err(e) => Err(anyhow::Error::new(e)),
        }
    }

    /// Create new notification entry and add all the required notification plans to the queue.
    pub async fn create_notification<'a>(
        &self,
        username: &'a str,
        notification: NotificationCreationOpts<'a>,
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

    /// Get notification by its ID.
    pub async fn get_notification(&self, notification_id: &Uuid) -> Result<Option<Notification>> {
        let q = query_as!(
            RepoNotification,
            r#"SELECT
                n.id,
                n.title,
                n.content,
                ARRAY_AGG(ROW(nq.planned_at, nq.sent_at) ORDER BY nq.planned_at) AS "plan!: Vec<(OffsetDateTime, Option<OffsetDateTime>)>"
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

        Ok(Some(notification_info.into()))
    }

    /// List notifications belonging to the specified user.
    pub async fn list_user_notifications(&self, username: &str) -> Result<Vec<Notification>> {
        let q = query_as!(
            RepoNotification,
            r#"SELECT
                n.id,
                n.title,
                n.content,
                ARRAY_AGG(ROW(nq.planned_at, nq.sent_at) ORDER BY nq.planned_at) AS "plan!: Vec<(OffsetDateTime, Option<OffsetDateTime>)>"
            FROM notification n
            JOIN notification_queue nq ON nq.notification_id = n.id
            WHERE n.username = $1
            GROUP BY n.id"#,
            username
        );

        let notifications = self.timeout(q.fetch_all(&self.pool)).await??;

        Ok(notifications.into_iter().map(Into::into).collect())
    }

    /// Reset the "inprogress" entries of the notification queue in order to retry them.
    pub async fn reset_notification_queue(&self) -> Result<()> {
        let q = query!(
            r#"UPDATE notification_queue
            SET state = 'planned'
            WHERE state = 'inprogress'"#
        );

        self.timeout(q.execute(&self.pool)).await??;

        Ok(())
    }

    /// Reserve the next batch of enqueued notifications which should've been sent by now.
    pub async fn reserve_notification_queue_batch(&self) -> Result<Vec<NotificationQueueElement>> {
        let q = query_as!(
            NotificationQueueElement,
            r#"WITH batch_elements AS (
              SELECT notification_id
              FROM notification_queue
              WHERE planned_at < NOW()
                AND state = 'planned'
              LIMIT 100
            )
            UPDATE notification_queue nq
            SET state = 'inprogress'
            FROM notification n
            WHERE nq.notification_id = n.id
              AND nq.notification_id IN (SELECT notification_id FROM batch_elements)
            RETURNING n.id, n.username, n.title, n.content, nq.planned_at"#
        );

        let queue_elements = self.timeout(q.fetch_all(&self.pool)).await??;

        Ok(queue_elements)
    }

    /// Save the result for a processed notification.
    pub async fn save_notification_result(
        &self,
        id: &Uuid,
        planned_at: OffsetDateTime,
        result: Option<OffsetDateTime>,
    ) -> Result<()> {
        let (state, sent_at) = result.map_or((NotificationState::Failed, None), |t| {
            (NotificationState::Sent, Some(t))
        });

        let q = query!(
            r#"UPDATE notification_queue
            SET state = $3, sent_at = $4
            WHERE notification_id = $1 AND planned_at = $2"#,
            id,
            planned_at,
            state as NotificationState,
            sent_at
        );

        self.timeout(q.execute(&self.pool)).await??;

        Ok(())
    }

    fn timeout<F>(&self, f: F) -> Timeout<F>
    where
        F: Future,
    {
        timeout(self.request_timeout, f)
    }
}
