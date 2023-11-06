mod app;
mod config;
mod repository;
mod rng;
mod session;
mod smtp;

use std::future::Future;
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

#[allow(clippy::cognitive_complexity, clippy::redundant_pub_crate)] // needed because of the tokio::select! macro which expands into something ungodly
async fn run() -> Result<()> {
    let cfg = config::Config::from_env()?;
    let cancel_token = CancellationToken::new();

    let repository = setup_repository(&cfg).await?;
    let notifier = setup_notifier(cancel_token.clone(), &cfg, &repository).await?;
    let api_server = setup_api_server(cancel_token.clone(), &cfg, &repository)?;

    let notifier_handle = tokio::spawn(notifier);
    let api_server_handle = tokio::spawn(api_server);

    tokio::select! {
        () = cancel_token.cancelled() => {}
        () = shutdown_signal(cancel_token.clone()) => {}
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

async fn setup_repository(cfg: &config::Config) -> Result<repository::Repository> {
    repository::Repository::connect(
        &cfg.database_url,
        std::time::Duration::from_secs(30),
        std::time::Duration::from_secs(10),
        64,
    )
    .await
}

async fn setup_notifier(
    cancel_token: CancellationToken,
    cfg: &config::Config,
    repository: &repository::Repository,
) -> Result<impl Future<Output = ()>> {
    let notifier = smtp::Notifier::new(
        repository.clone(),
        NOTIFIER_INTERVAL,
        NOTIFIER_USERNAME.into(),
        NOTIFIER_DOMAIN.into(),
        NOTIFIER_SERVER_NAME.into(),
        cfg.notifier_server_addr.clone(),
    )
    .await?;

    let f = notifier.run(cancel_token);
    Ok(async move {
        info!("running notifier with a {:?} interval", NOTIFIER_INTERVAL);
        f.await;
    })
}

fn setup_api_server(
    cancel_token: CancellationToken,
    cfg: &config::Config,
    repository: &repository::Repository,
) -> Result<impl Future<Output = Result<()>>> {
    let state = app::State {
        repository: repository.clone(),
    };

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

    let server = axum::Server::bind(&cfg.listen_addr).serve(router.into_make_service());
    let listen_addr = cfg.listen_addr;

    Ok(async move {
        info!("serving API on {}", listen_addr);
        server
            .with_graceful_shutdown(cancel_token.cancelled())
            .await
            .map_err(anyhow::Error::msg)
    })
}

async fn shutdown_signal(cancel_token: CancellationToken) {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install graceful shutdown signal handler");

    cancel_token.cancel();
}
