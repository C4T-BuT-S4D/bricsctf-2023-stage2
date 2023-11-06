use crate::repository;

use anyhow::{Context, Result};
use std::time::Duration;
use time::OffsetDateTime;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{tcp, TcpStream};
use tokio_util::sync::CancellationToken;
use tracing::{error, info};

pub struct NotifierOpts {
    pub interval: Duration,
    pub server_addr: String,
    pub server_name: String,
    pub email_domain: String,
    pub notifier_username: String,
    pub notifier_password: String,
}

#[derive(Clone)]
pub struct Notifier {
    repository: repository::Repository,
    interval: Duration,
    server_name: String,
    server_addr: String,
    email_domain: String,
    notifier_email: String,
    notifier_password: String,
}

impl Notifier {
    pub async fn new(repository: repository::Repository, opts: NotifierOpts) -> Result<Self> {
        repository
            .reset_notification_queue()
            .await
            .context("resetting current notification queue")?;

        let notifier_email = format_email(&opts.notifier_username, &opts.email_domain);

        Ok(Self {
            repository,
            interval: opts.interval,
            server_name: opts.server_name,
            server_addr: opts.server_addr,
            email_domain: opts.email_domain,
            notifier_email,
            notifier_password: opts.notifier_password,
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

    // :TODO: limit batch size to avoid SMTP server's mails per connection
    async fn iteration(self, batch: Vec<repository::NotificationQueueElement>) -> Result<()> {
        info!("notifier processing batch of {} elements", batch.len());

        let mut connection =
            Connection::connect(self.server_addr.clone(), self.server_name.clone()).await?;

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
            .context(format!("connecting to SMTP server {}", &server_addr))?;

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
            .context("sending HELO")?;

        // connection.send_message(format!(), expected_lines)

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
        self.tcp_write
            .write_all((msg + Self::LINE_ENDING).as_bytes())
            .await
            .context("writing request message")?;

        for i in 0..expected_lines {
            let mut buf = String::new();
            self.tcp_read
                .read_line(&mut buf)
                .await
                .context(format!("reading response line {i}"))?;
        }

        Ok(())
    }

    async fn reconnect(&mut self) -> Result<()> {
        let new_connection =
            Self::connect(self.server_addr.clone(), self.server_name.clone()).await?;

        *self = new_connection;

        Ok(())
    }
}

fn format_email(username: &str, domain: &str) -> String {
    format!("{username}@{domain}")
}
