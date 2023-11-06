use crate::repository;
use crate::rng::APP_RNG;

use std::future::Future;
use std::{sync::Arc, time::Duration};

use anyhow::{Context, Result};
use base64::Engine;
use rand::seq::SliceRandom;
use time::OffsetDateTime;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{tcp, TcpStream};
use tokio::time::timeout;
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

pub struct NotifierOpts<'a> {
    pub request_timeout: Duration,
    pub interval: Duration,
    pub server_addr: &'a str,
    pub server_name: &'a str,
    pub email_domain: &'a str,
    pub notifier_username: &'a str,
    pub notifier_password: &'a str,
}

#[derive(Clone)]
pub struct Notifier {
    repository: repository::Repository,
    request_timeout: Duration,
    interval: Duration,
    server_name: Arc<str>,
    server_addr: Arc<str>,
    email_domain: Arc<str>,
    notifier_email: Arc<str>,
    notifier_credentials: Arc<str>,
}

impl Notifier {
    pub async fn new(repository: repository::Repository, opts: NotifierOpts<'_>) -> Result<Self> {
        repository
            .reset_notification_queue()
            .await
            .context("resetting current notification queue")?;

        let notifier_email = format_email(opts.notifier_username, opts.email_domain);
        let notifier_credentials = base64::engine::general_purpose::STANDARD.encode(format!(
            "\x00{}\x00{}",
            opts.notifier_username, opts.notifier_password
        ));

        Ok(Self {
            repository,
            request_timeout: opts.request_timeout,
            interval: opts.interval,
            server_name: opts.server_name.into(),
            server_addr: opts.server_addr.into(),
            email_domain: opts.email_domain.into(),
            notifier_email: notifier_email.into(),
            notifier_credentials: notifier_credentials.into(),
        })
    }

    pub async fn run(self, cancel_token: CancellationToken) {
        loop {
            tokio::select! {
              () = cancel_token.cancelled() => {
                info!("notifier shutting down due to cancelation");
                break;
              }

              () = tokio::time::sleep(self.interval) => {
                if let Err(e) = self.launch_iteration().await {
                  error!(error=format!("{:#}", e), "unexpected error occurred during notifier iteration");
                }
              }
            }
        }
    }

    async fn launch_iteration(&self) -> Result<()> {
        let batch = self
            .repository
            .reserve_notification_queue_batch()
            .await
            .context("reserving batch in notification queue")?;

        if !batch.is_empty() {
            tokio::spawn(self.clone().iteration(batch));
        }

        Ok(())
    }

    async fn iteration(self, batch: Vec<repository::NotificationQueueElement>) -> Result<()> {
        info!("notifier processing batch of {} elements", batch.len());

        let mut connection = Connection::connect(
            self.request_timeout,
            self.server_addr.clone(),
            self.server_name.clone(),
            self.notifier_credentials.clone(),
        )
        .await?;

        // Fairly sort batch so that all elements get sent in the order they are planned
        let mut batch = batch.clone();
        batch.sort_unstable_by_key(|el| (el.planned_at, el.id));

        // Shuffle to avoid any possible skew in selecting the order when multiple elements should be sent at once
        let mut block_start: usize = 0;
        let mut block_end: usize = 0;
        for i in 0..=batch.len() {
            if i == batch.len() || batch[i].planned_at != batch[block_start].planned_at {
                APP_RNG.with_borrow_mut(|rng| batch[block_start..block_end].shuffle(rng));
                block_start = i;
            }
            block_end = i + 1;
        }

        for notification in batch {
            let send_result = match connection
                .send_mail(
                    &self.notifier_email,
                    &format_email(&notification.username, &self.email_domain),
                    &notification.title,
                    &notification.content,
                    5,
                )
                .await
            {
                Ok(v) => v,
                Err(e) => {
                    error!(
                        error = format!("{e:#}"),
                        "encountered fatal error while sending mail"
                    );
                    None
                }
            };

            info!(
                notification_id = notification.id.to_string(),
                result = send_result.map_or("failed".into(), |t| t.to_string()),
                "notifier processed notification"
            );

            if let Err(e) = self
                .repository
                .save_notification_result(&notification.id, notification.planned_at, send_result)
                .await
            {
                error!(
                    error = format!("{e:#}"),
                    notification_id = notification.id.to_string(),
                    "failed to save notification processing results to repository"
                );
            }
        }

        Ok(())
    }
}

struct Connection {
    request_timeout: Duration,
    server_addr: Arc<str>,
    server_name: Arc<str>,
    credentials: Arc<str>,
    tcp_write: tcp::OwnedWriteHalf,
    tcp_read: BufReader<tcp::OwnedReadHalf>,
}

impl Connection {
    const LINE_ENDING: &'static str = "\r\n";

    async fn connect(
        request_timeout: Duration,
        server_addr: Arc<str>,
        server_name: Arc<str>,
        credentials: Arc<str>,
    ) -> Result<Self> {
        let tcp_stream = TcpStream::connect(&*server_addr)
            .await
            .context(format!("connecting to SMTP server {}", &server_addr))?;

        let (tcp_read, tcp_write) = tcp_stream.into_split();

        let mut connection = Self {
            request_timeout,
            server_addr,
            server_name,
            credentials: credentials.clone(),
            tcp_write,
            tcp_read: BufReader::new(tcp_read),
        };

        connection
            .send_message(format!("HELO {}", &connection.server_name), 2)
            .await
            .context("sending HELO")?;

        connection
            .send_message(format!("AUTH PLAIN {credentials}",), 1)
            .await
            .context("authenticating in mail server")?;

        Ok(connection)
    }

    async fn send_mail(
        &mut self,
        from: &str,
        to: &str,
        subject: &str,
        content: &str,
        retries: i32,
    ) -> Result<Option<OffsetDateTime>> {
        for _ in 0..retries {
            if let Err(e) = self.try_send_mail_once(from, to, subject, content).await {
                error!(
                    error = format!("{e:#}"),
                    from = from,
                    to = to,
                    subject = subject,
                    "sending mail failed, will attempt to reconnect and retry"
                );

                self.reconnect()
                    .await
                    .context("failed to reconnect after botched mail send attempt")?;
            } else {
                return Ok(Some(OffsetDateTime::now_utc()));
            }
        }

        error!(
            from = from,
            to = to,
            subject = subject,
            "failed to send mail after {} retries",
            retries
        );

        Ok(None)
    }

    async fn try_send_mail_once(
        &mut self,
        from: &str,
        to: &str,
        subject: &str,
        content: &str,
    ) -> Result<()> {
        self.send_message(format!("MAIL FROM:<{from}>"), 1)
            .await
            .context("sending MAIL FROM")?;

        self.send_message(format!("RCPT TO:<{to}>"), 1)
            .await
            .context("sending RCPT TO")?;

        self.send_message("DATA".into(), 1)
            .await
            .context("sending DATA")?;

        self.send_message(
            format!(
                "From: {from}{CRLF}To: {to}{CRLF}Subject: {subject}{CRLF}{CRLF}{content}{CRLF}.",
                CRLF = Self::LINE_ENDING
            ),
            1,
        )
        .await
        .context("sending body")?;

        Ok(())
    }

    async fn send_message(&mut self, msg: String, expected_lines: u32) -> Result<()> {
        Self::timeout(
            self.request_timeout,
            self.tcp_write
                .write_all((msg + Self::LINE_ENDING).as_bytes()),
            "writing request message".into(),
        )
        .await?;

        for i in 0..expected_lines {
            let mut buf = String::new();
            Self::timeout(
                self.request_timeout,
                self.tcp_read.read_line(&mut buf),
                format!("reading response line {i}"),
            )
            .await?;
        }

        Ok(())
    }

    async fn reconnect(&mut self) -> Result<()> {
        let new_connection = Self::connect(
            self.request_timeout,
            self.server_addr.clone(),
            self.server_name.clone(),
            self.credentials.clone(),
        )
        .await?;

        *self = new_connection;

        Ok(())
    }

    async fn timeout<F, T, E>(request_timeout: Duration, f: F, context: String) -> Result<T>
    where
        F: Future<Output = Result<T, E>> + Send,
        E: 'static + std::error::Error + Send + Sync,
    {
        timeout(request_timeout, f)
            .await
            .map_err(anyhow::Error::new)
            .and_then(|r| r.map_err(anyhow::Error::new))
            .context(context)
    }
}

fn format_email(username: &str, domain: &str) -> String {
    format!("{username}@{domain}")
}
