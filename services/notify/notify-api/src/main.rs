mod app;
mod cleaner;
mod config;
mod repository;
mod rng;
mod session;
mod smtp;

use std::future::Future;
use std::process;
use std::time::Duration;

use anyhow::{Context, Result};
use tokio_util::sync::CancellationToken;
use tower::ServiceBuilder;
use tower_http::catch_panic::CatchPanicLayer;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{error, info, warn, Level};

const REPOSITORY_CONNECT_TIMEOUT: Duration = Duration::from_secs(30);
const REPOSITORY_REQUEST_TIMEOUT: Duration = Duration::from_secs(10);
const REPOSITORY_MAX_CONNECTIONS: u32 = 64;
const SESSION_MAX_AGE: Duration = Duration::from_secs(10 * 60);
const NOTIFIER_REQUEST_TIMEOUT: Duration = Duration::from_millis(300);
const NOTIFIER_INTERVAL: Duration = Duration::from_secs(1);
const NOTIFIER_USERNAME: &str = "notifier";
const NOTIFIER_DOMAIN: &str = "notify";
const NOTIFIER_SERVER_NAME: &str = "mail.notify";
const CLEANER_REQUEST_TIMEOUT: Duration = Duration::from_secs(2);
const CLEANER_INTERVAL: Duration = Duration::from_secs(60);
const CLEANER_MAX_AGE: Duration = Duration::from_secs(10 * 60);

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
    let cfg = config::Config::read().await?;
    let cancel_token = CancellationToken::new();

    let repository = setup_repository(&cfg).await?;
    let notifier = setup_notifier(cancel_token.clone(), &cfg, &repository).await?;
    let api_server = setup_api_server(cancel_token.clone(), &cfg, &repository)?;
    let cleaner = setup_cleaner(cancel_token.clone(), &cfg, &repository)?;

    let notifier_handle = tokio::spawn(notifier);
    let api_server_handle = tokio::spawn(api_server);
    let cleaner_handle = tokio::spawn(cleaner);

    tokio::select! {
        () = cancel_token.cancelled() => {}
        () = shutdown_signal(cancel_token.clone()) => {}
    }

    warn!("received cancellation/shutdown signal, performing graceful shutdown");

    if let Err(e) = notifier_handle.await {
        error!(error = format!("{:#}", e), "failed to join notifier future");
    }

    match api_server_handle.await {
        Ok(r) => r.context("serving API")?,
        Err(e) => error!(error = format!("{:#}", e), "failed to join server future"),
    };

    if let Err(e) = cleaner_handle.await {
        error!(error = format!("{:#}", e), "failed to join cleaner future")
    }

    repository.close().await;

    Ok(())
}

async fn setup_repository(cfg: &config::Config) -> Result<repository::Repository> {
    repository::Repository::connect(
        &cfg.database_url,
        REPOSITORY_CONNECT_TIMEOUT,
        REPOSITORY_REQUEST_TIMEOUT,
        REPOSITORY_MAX_CONNECTIONS,
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
        smtp::NotifierOpts {
            request_timeout: NOTIFIER_REQUEST_TIMEOUT,
            interval: NOTIFIER_INTERVAL,
            server_addr: &cfg.notifier_server_addr,
            server_name: NOTIFIER_SERVER_NAME,
            email_domain: NOTIFIER_DOMAIN,
            notifier_username: NOTIFIER_USERNAME,
            notifier_password: &cfg.notifier_secret,
        },
    )
    .await
    .context("initializing notifier")?;

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
                .layer(session::layer(
                    &cfg.cookie_key_path,
                    SESSION_MAX_AGE.try_into().unwrap(),
                )?),
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

fn setup_cleaner(
    cancel_token: CancellationToken,
    cfg: &config::Config,
    repository: &repository::Repository,
) -> Result<impl Future<Output = ()>> {
    let cleaner = cleaner::Cleaner::new(
        repository.clone(),
        cleaner::CleanerOpts {
            timeout: CLEANER_REQUEST_TIMEOUT,
            interval: CLEANER_INTERVAL,
            admin_addr: &cfg.notifier_admin_addr,
            notifier_password: &cfg.notifier_secret,
            notifier_username: NOTIFIER_USERNAME,
            max_user_age: CLEANER_MAX_AGE,
        },
    )
    .context("initializing cleaner")?;

    let f = cleaner.run(cancel_token);
    Ok(async move {
        info!("running cleaner with a {:?} interval", CLEANER_INTERVAL);
        f.await;
    })
}

#[allow(clippy::redundant_pub_crate)]
#[cfg(target_family = "unix")]
async fn shutdown_signal(cancel_token: CancellationToken) {
    let mut sigterm =
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate()).unwrap();
    let sigint = tokio::signal::ctrl_c();

    tokio::select! {
        _ = sigterm.recv() => {}
        _ = sigint => {}
    }

    cancel_token.cancel();
}

#[cfg(target_family = "windows")]
async fn shutdown_signal(cancel_token: CancellationToken) {
    let _ = tokio::signal::ctrl_c().await;
    cancel_token.cancel();
}
