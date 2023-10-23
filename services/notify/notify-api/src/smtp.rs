use std::time::Duration;
use tokio_util::sync::CancellationToken;
use tracing::info;

pub async fn notifier(cancel_token: CancellationToken, interval: Duration, email: String) {
    loop {
        tokio::select! {
          _ = cancel_token.cancelled() => {
            info!("canceled");
            break;
          }
          _ = tokio::time::sleep(interval) => {
            info!("woken up");
            cancel_token.cancel()
          }
        }
    }
}
