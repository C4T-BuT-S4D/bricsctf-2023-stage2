mod app;
mod config;
mod repository;
mod rng;
mod session;
mod smtp;

use std::process;

use anyhow::{Context, Result};
use tokio_util::sync::CancellationToken;
use tower::ServiceBuilder;
use tower_http::catch_panic::CatchPanicLayer;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{error, info, warn, Level};

const MAX_USER_AGE: time::Duration = time::Duration::minutes(30);
const NOTIFIER_INTERVAL: std::time::Duration = std::time::Duration::from_secs(1);
const NOTIFIER_USERNAME: &str = "notifier";
const NOTIFIER_DOMAIN: &str = "notify";
const NOTIFIER_SERVER_NAME: &str = "mail.notify";

#[tokio::main]
async fn main() -> process::ExitCode {
    let json_subscriber = tracing_subscriber::fmt()
        .json()
        .with_max_level(Level::INFO)
        .flatten_event(true)
        .finish();
    tracing::subscriber::set_global_default(json_subscriber)
        .expect("failed to set default tracing subscriber");

    if let Err(e) = run().await {
        error!(
            error = format!("{:#}", e),
            "encountered fatal error, shutting down"
        );
        return process::ExitCode::FAILURE;
    }

    process::ExitCode::SUCCESS
}

async fn run() -> Result<()> {
    let cfg = config::Config::from_env()?;
    let cancel_token = CancellationToken::new();

    let repository = repository::Repository::connect(
        &cfg.database_url,
        std::time::Duration::from_secs(30),
        std::time::Duration::from_secs(10),
        64,
    )
    .await?;

    let notifier = smtp::Notifier::new(
        repository.clone(),
        NOTIFIER_INTERVAL,
        NOTIFIER_USERNAME.into(),
        NOTIFIER_DOMAIN.into(),
        NOTIFIER_SERVER_NAME.into(),
        cfg.notifier_server_addr.clone(),
    )
    .await?;

    let notifier = {
        let f = notifier.run(cancel_token.clone());
        async move {
            info!("running notifier with a {:?} interval", NOTIFIER_INTERVAL);
            f.await
        }
    };

    let state = app::State { repository };
    let router = app::router()
        .layer(
            ServiceBuilder::new()
                .layer(CatchPanicLayer::new())
                .layer(
                    TraceLayer::new_for_http()
                        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                        .on_request(DefaultOnRequest::new().level(Level::INFO))
                        .on_response(DefaultOnResponse::new().level(Level::INFO)),
                )
                .layer(session::layer(&cfg.cookie_key_path, MAX_USER_AGE)?),
        )
        .with_state(state);

    let api_server = {
        let server = axum::Server::bind(&cfg.listen_addr).serve(router.into_make_service());
        let cancel_token = cancel_token.clone();
        async move {
            info!("serving API on {}", &cfg.listen_addr);
            server
                .with_graceful_shutdown(cancel_token.cancelled())
                .await
        }
    };

    let notifier_handle = tokio::spawn(notifier);
    let api_server_handle = tokio::spawn(api_server);

    tokio::select! {
        _ = cancel_token.cancelled() => {}
        _ = shutdown_signal(cancel_token.clone()) => {}
    }

    warn!("received cancelation signal, performing graceful shutdown");

    if let Err(e) = notifier_handle.await {
        error!(
            error = format!("{:#}", e),
            "failed to join notifier processor future"
        );
    }

    match api_server_handle.await {
        Ok(r) => r.with_context(|| "serving API")?,
        Err(e) => error!(error = format!("{:#}", e), "failed to join server future"),
    };

    Ok(())
}

async fn shutdown_signal(cancel_token: CancellationToken) {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install graceful shutdown signal handler");

    cancel_token.cancel()
}
