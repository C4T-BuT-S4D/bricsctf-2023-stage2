mod app;
mod config;
mod session;

use std::process;

use anyhow::{Context, Result};
use axum::{routing, Router};
use tower::ServiceBuilder;
use tower_http::catch_panic::CatchPanicLayer;
use tower_http::trace::{DefaultMakeSpan, DefaultOnRequest, DefaultOnResponse, TraceLayer};
use tracing::{error, info, warn, Level};

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
    let router = build_router(&cfg)?;

    info!("serving API on {}", cfg.listen_addr);

    let server = axum::Server::bind(&cfg.listen_addr).serve(router.into_make_service());
    let graceful = server.with_graceful_shutdown(shutdown_signal());

    graceful.await.with_context(|| "gracefully serving API")?;

    Ok(())
}

fn build_router(cfg: &config::Config) -> Result<Router> {
    Ok(Router::new()
        .route("/register", routing::post(app::register::handler))
        .route("/login", routing::post(app::login::handler))
        .layer(
            ServiceBuilder::new()
                .layer(CatchPanicLayer::new())
                .layer(
                    TraceLayer::new_for_http()
                        .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                        .on_request(DefaultOnRequest::new().level(Level::INFO))
                        .on_response(DefaultOnResponse::new().level(Level::INFO)),
                )
                .layer(session::layer(&cfg.cookie_key_path)?),
        ))
}

async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install graceful shutdown signal handler");

    warn!("performing graceful shutdown");
}
