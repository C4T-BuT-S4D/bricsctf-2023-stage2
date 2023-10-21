use crate::app::{self, JsonError, LoggedError};
use crate::session::Session;

use anyhow::Context;
use argon2::{Argon2, PasswordHash, PasswordVerifier};
use axum::extract::State;
use axum::http::StatusCode;
use axum::{Extension, Json};
use once_cell::sync::Lazy;
use serde::Deserialize;

/// Argon2 hash of "password", used for verification when the username is invalid
/// in order to avoid user enumeration attacks based on the response timing.
static DUMMY_PASSWORD_HASH: Lazy<PasswordHash> = Lazy::new(|| {
    PasswordHash::new("$argon2id$v=19$m=19456,t=2,p=1$XG+qmZeu708R/snDBX2U+Q$bygPbDQBbBx3wQl3MvMdK7WVWoK/+LMK8Vsh6brpo/I").expect("failed to parse dummy password hash")
});

static INVALID_CREDENTIALS_ERROR: &str =
    "Invalid credentials supplied, please validate the username and password.";

#[derive(Clone, Deserialize)]
pub struct LoginRequest {
    username: String,
    password: String,
}

/// Handler implementing the /login API endpoint.
pub async fn handler(
    State(state): State<app::State>,
    Json(request): Json<LoginRequest>,
) -> Result<(StatusCode, Result<Extension<Session>, JsonError>), LoggedError> {
    let account = state
        .repository
        .get_account(&request.username)
        .await
        .with_context(|| format!("getting account {}", &request.username))?;

    // Use dummy hash if user wasn't found to avoid user enumeration by response timing.
    let password_hash = match account {
        Some(ref acc) => PasswordHash::new(&acc.password_hash)
            .map_err(anyhow::Error::msg)
            .with_context(|| format!("parsing account {} hash", &acc.username))?,
        None => (*DUMMY_PASSWORD_HASH).clone(),
    };

    // The ordering here is deliberate so that password verification always takes
    if Argon2::default()
        .verify_password(request.password.as_bytes(), &password_hash)
        .is_err()
        || account.is_none()
    {
        return Ok((
            StatusCode::UNAUTHORIZED,
            Err(JsonError {
                error: INVALID_CREDENTIALS_ERROR.to_owned(),
            }),
        ));
    }

    Ok((
        StatusCode::OK,
        Ok(Extension(Session {
            username: request.username,
        })),
    ))
}
