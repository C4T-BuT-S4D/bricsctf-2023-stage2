use std::convert::Infallible;
use std::fmt::Display;
use std::fs;
use std::io;

use anyhow::{Context, Result};
use axum::middleware::{self, Next};
use axum::{body::HttpBody, http::Request, response::Response, routing::Route};
use axum_extra::extract::PrivateCookieJar;
use cookie::{Cookie, Key, SameSite};
use serde::{Deserialize, Serialize};
use time::{Duration, OffsetDateTime};
use tower::{Layer, Service};
use tracing::{error, info};

const SESSION_COOKIE_NAME: &str = "notify_session";
const SESSION_COOKIE_AGE: Duration = Duration::minutes(30);

/// Session contains the session information accessible by the app handlers.
#[derive(Clone, Deserialize, Serialize)]
pub struct Session {
    pub username: String,
}

#[derive(Clone, Deserialize, Serialize)]
struct WrappedSession {
    inner: Session,
    expires_at: OffsetDateTime,
}

/// Returns a tower Layer that adds session extraction & saving to a private cookie jar using a key,
/// which will either be retrieved from the specified file, or generated and saved to it.
/// Handlers can then receive the Session by accepting Extension<Option<Session>>,
/// and save a new session by returning Extension<Session>.
pub fn layer<B: HttpBody + Send + 'static>(
    cookie_key_path: &str,
) -> Result<
    impl Layer<
            Route<B>,
            Service = impl Service<
                Request<B>,
                Response = Response,
                Error = impl Into<Infallible> + Display + 'static,
                Future = impl Send + 'static,
            > + Clone
                          + Send
                          + 'static,
        > + Clone
        + Send
        + 'static,
> {
    let cookie_key = load_or_generate_key(cookie_key_path)?;

    Ok(middleware::from_fn(
        move |mut request: Request<B>, next: Next<B>| {
            let cookie_key = cookie_key.clone();
            async move {
                let mut jar = PrivateCookieJar::from_headers(request.headers(), cookie_key);

                let session = jar
                    .get(SESSION_COOKIE_NAME)
                    .and_then(|x| serde_json::from_str::<WrappedSession>(x.value()).ok())
                    .and_then(|s| {
                        if s.expires_at < OffsetDateTime::now_utc() {
                            None
                        } else {
                            Some(s)
                        }
                    });

                request.extensions_mut().insert(session.map(|ws| ws.inner));

                let response = next.run(request).await;

                if let Some(session) = response.extensions().get::<Session>() {
                    let expires_at = OffsetDateTime::now_utc() + SESSION_COOKIE_AGE;

                    let serialized_session = serde_json::to_string(&WrappedSession {
                        inner: session.clone(),
                        expires_at,
                    })
                    .expect("failed to serialize session data");

                    jar = jar.add(
                        Cookie::build(SESSION_COOKIE_NAME, serialized_session)
                            .expires(expires_at)
                            .http_only(true)
                            .same_site(SameSite::Lax)
                            .finish(),
                    );
                }

                (jar, response)
            }
        },
    ))
}

fn load_or_generate_key(filepath: &str) -> Result<Key> {
    match fs::read(filepath) {
        Ok(data) => match Key::try_from(&data[..]) {
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

    let key = Key::try_generate().with_context(|| "failed to generate new cookie key")?;
    fs::write(filepath, key.master())
        .with_context(|| format!("failed to save generated cookie key to file {}", filepath))?;

    Ok(key)
}
