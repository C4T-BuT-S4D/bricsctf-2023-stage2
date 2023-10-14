use std::env;
use std::net::SocketAddr;
use std::sync::{Arc, Mutex};

use axum::{response::Json, routing::get, Router};
use slog::{error, info, o, Drain, Logger};

#[tokio::main]
async fn main() {
    let json_drain = Mutex::new(slog_json::Json::default(std::io::stderr()));
    let async_drain = slog_async::Async::default(json_drain.fuse());
    let log_root = Arc::new(Logger::root(async_drain.fuse(), o!()));

    let listen_addr: SocketAddr = match env::var("LISTEN_ADDR")
        .map_err(anyhow::Error::new)
        .and_then(|v| v.parse().map_err(anyhow::Error::new))
    {
        Ok(a) => a,
        Err(e) => {
            error!(log_root, "failed to read LISTEN_ADDR from env"; "error" => e.to_string());
            return;
        }
    };

    let app = Router::new().route("/", get(handler));

    info!(log_root, "serving API on {}", listen_addr);

    let server = axum::Server::bind(&listen_addr).serve(app.into_make_service());
    let graceful = server.with_graceful_shutdown(shutdown_signal(log_root.clone()));

    if let Err(e) = graceful.await {
        error!(log_root, "encountered fatal server error, shutting down"; "error" => e.to_string());
    }
}

async fn shutdown_signal(log_root: Arc<Logger>) {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install graceful shutdown signal handler");

    info!(log_root, "performing graceful shutdown");
}

async fn handler() -> Json<&'static str> {
    Json("aboba")
}
