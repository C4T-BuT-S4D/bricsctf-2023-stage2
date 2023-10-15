mod app;

use std::net::SocketAddr;
use std::process;
use std::sync::Arc;
use std::{env, fs, io};

use anyhow::Context;
use axum::{extract, response, routing, Router};
use tower_cookies::{Cookie, CookieManagerLayer, Cookies};
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

async fn run() -> anyhow::Result<()> {
    let listen_addr: SocketAddr = env::var("LISTEN_ADDR")
        .map_err(anyhow::Error::new)
        .and_then(|v| v.parse().map_err(anyhow::Error::new))
        .with_context(|| "failed to read LISTEN_ADDR from env")?;

    let cookie_key_path =
        env::var("COOKIE_KEY_PATH").with_context(|| "failed to read COOKIE_KEY_PATH from env")?;
    let cookie_key = load_or_generate_cookie_key(&cookie_key_path)?;

    let app_state = Arc::new(app::State { cookie_key });

    let app = Router::new()
        .route("/", routing::get(handler))
        .layer(CookieManagerLayer::new())
        .layer(
            TraceLayer::new_for_http()
                .make_span_with(DefaultMakeSpan::new().level(Level::INFO))
                .on_request(DefaultOnRequest::new().level(Level::INFO))
                .on_response(DefaultOnResponse::new().level(Level::INFO)),
        )
        .with_state(app_state);

    info!("serving API on {}", listen_addr);

    let server = axum::Server::bind(&listen_addr).serve(app.into_make_service());
    let graceful = server.with_graceful_shutdown(shutdown_signal());

    graceful.await.with_context(|| "gracefully serving API")?;

    Ok(())
}

async fn shutdown_signal() {
    tokio::signal::ctrl_c()
        .await
        .expect("failed to install graceful shutdown signal handler");

    warn!("performing graceful shutdown");
}

fn load_or_generate_cookie_key(filepath: &str) -> anyhow::Result<tower_cookies::Key> {
    match fs::read_to_string(filepath) {
        Ok(data) => match tower_cookies::Key::try_from(data.as_bytes()) {
            Ok(key) => return Ok(key),
            Err(e) => error!(
                error = e.to_string(),
                "invalid cookie key stored in {}, will regenerate it", filepath
            ),
        },
        Err(e) => {
            if e.kind() != io::ErrorKind::NotFound {
                return Err(e).with_context(|| format!("unable to read cookie file {}", filepath));
            }

            info!(
                "cookie file {} not found, will generate cookie key",
                filepath
            );
        }
    };

    let key =
        tower_cookies::Key::try_generate().with_context(|| "failed to generate new cookie key")?;
    fs::write(filepath, key.master())
        .with_context(|| format!("failed to save generated cookie key to file {}", filepath))?;

    Ok(key)
}

async fn handler(
    extract::State(state): extract::State<Arc<app::State>>,
    cookies: Cookies,
) -> response::Json<&'static str> {
    let signed_cookies = cookies.signed(&state.cookie_key);

    info!(
        "cookie {}",
        signed_cookies
            .get("aboba")
            .map_or("novalue".to_owned(), |c| c.value().to_owned())
    );

    signed_cookies.add(Cookie::new("aboba", "sus"));

    response::Json("aboba")
}
