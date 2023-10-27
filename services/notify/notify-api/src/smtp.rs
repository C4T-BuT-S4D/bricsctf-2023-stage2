use crate::repository;

use anyhow::{Context, Result};
use std::time::Duration;
use time::OffsetDateTime;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{tcp, TcpStream};
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

pub struct Notifier {
    repository: repository::Repository,
    interval: Duration,
    email: String,
    domain: String,
    server_name: String,
    server_addr: String,
}

impl Notifier {
    pub async fn new(
        repository: repository::Repository,
        interval: Duration,
        username: String,
        domain: String,
        server_name: String,
        server_addr: String,
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
            server_addr,
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

    // :TODO: limit batch size to avoid SMTP server's mails per connection
    // :TODO: launch concurrent futures for each iteration
    async fn iteration(&self) -> Result<()> {
        let batch = self
            .repository
            .reserve_notification_queue_batch()
            .await
            .with_context(|| "reserving batch in notification queue")?;

        if batch.is_empty() {
            return Ok(());
        }

        info!("notifier processing batch of {} elements", batch.len());

        let mut connection =
            Connection::connect(self.server_addr.clone(), self.server_name.clone()).await?;

        for notification in batch {
            let send_result = match connection
                .send_mail(
                    self.email.clone(),
                    format!("{}@{}", notification.username, self.domain),
                    notification.title,
                    notification.content,
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
    tcp_write: tcp::OwnedWriteHalf,
    tcp_read: BufReader<tcp::OwnedReadHalf>,
    server_addr: String,
    server_name: String,
}

// :TODO: add timeouts
// :TODO: use NOOP pings + concurrent reading future instead of the current
//        "await response for each message" mechanism, since it can be bypassed
// :TODO: prematurely reconnect when connection has lived for too long
impl Connection {
    const LINE_ENDING: &'static str = "\r\n";

    async fn connect(server_addr: String, server_name: String) -> Result<Self> {
        let tcp_stream = TcpStream::connect(&server_addr)
            .await
            .with_context(|| format!("connecting to SMTP server {}", &server_addr))?;

        let (tcp_read, tcp_write) = tcp_stream.into_split();

        let mut connection = Self {
            tcp_write,
            tcp_read: BufReader::new(tcp_read),
            server_addr,
            server_name,
        };

        connection
            .send_message(format!("HELO {}", &connection.server_name), 2)
            .await
            .with_context(|| "sending HELO")?;

        Ok(connection)
    }

    async fn send_mail(
        &mut self,
        from: String,
        to: String,
        subject: String,
        content: String,
        retries: i32,
    ) -> Result<Option<OffsetDateTime>> {
        for _ in 0..retries {
            if let Err(e) = self
                .try_send_mail_once(&from, &to, &subject, &content)
                .await
            {
                error!(
                    error = format!("{e:#}"),
                    from = from,
                    to = to,
                    subject = subject,
                    "sending mail failed, will attempt to reconnect and retry"
                );

                self.reconnect()
                    .await
                    .with_context(|| "failed to reconnect after botched mail send attempt")?;
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
            .with_context(|| "sending MAIL FROM")?;

        self.send_message(format!("RCPT TO:<{to}>"), 1)
            .await
            .with_context(|| "sending RCPT TO")?;

        self.send_message("DATA".into(), 1)
            .await
            .with_context(|| "sending DATA")?;

        self.send_message(
            format!(
                "From: {from}{CRLF}To: {to}{CRLF}Subject: {subject}{CRLF}{CRLF}{content}{CRLF}.",
                CRLF = Connection::LINE_ENDING
            ),
            1,
        )
        .await
        .with_context(|| "sending body")?;

        Ok(())
    }

    async fn send_message(&mut self, msg: String, expected_lines: u32) -> Result<()> {
        self.tcp_write
            .write_all((msg + Connection::LINE_ENDING).as_bytes())
            .await
            .with_context(|| "writing request message")?;

        for i in 0..expected_lines {
            let mut buf = String::new();
            self.tcp_read
                .read_line(&mut buf)
                .await
                .with_context(|| format!("reading response line {i}"))?;
        }

        Ok(())
    }

    async fn reconnect(&mut self) -> Result<()> {
        let new_connection =
            Connection::connect(self.server_addr.clone(), self.server_name.clone()).await?;

        *self = new_connection;

        Ok(())
    }
}
