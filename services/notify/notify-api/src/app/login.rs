use crate::app::{self, JsonError, LoggedError};
use crate::session::Session;

use anyhow::Context;
use axum::{extract::State, http::StatusCode, Extension, Json};
use serde::Deserialize;

const INVALID_CREDENTIALS: &str =
    "Invalid credentials supplied, please validate the username and password.";

#[derive(Clone, Deserialize)]
pub(super) struct LoginRequest {
    username: String,
    password: String,
}

/// Handler implementing the POST /login API endpoint.
pub(super) async fn handler(
    State(state): State<app::State>,
    Json(request): Json<LoginRequest>,
) -> Result<(StatusCode, Result<Extension<Session>, JsonError>), LoggedError> {
    let Some(password_hash) = state
        .repository
        .get_account_password_hash(&request.username)
        .await
        .context(format!("getting account {}", &request.username))?
    else {
        return Ok((
            StatusCode::UNAUTHORIZED,
            Err(JsonError::new(INVALID_CREDENTIALS)),
        ));
    };

    // The ordering here is deliberate so that password verification always takes
    if bcrypt::verify(request.password.as_bytes(), &password_hash).is_err() {
        return Ok((
            StatusCode::UNAUTHORIZED,
            Err(JsonError::new(INVALID_CREDENTIALS)),
        ));
    }

    Ok((
        StatusCode::OK,
        Ok(Extension(Session {
            username: request.username,
        })),
    ))
}
