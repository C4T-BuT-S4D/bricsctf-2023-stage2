use crate::app::{self, JsonError, LoggedError};
use crate::session::Session;

use anyhow::Context;
use axum::{extract::State, http::StatusCode, Extension, Json};
use serde::Serialize;

#[derive(Clone, Serialize)]
pub struct UserResponse {
    username: String,
}

/// Handler implementing the /user API endpoint.
pub async fn handler(
    State(state): State<app::State>,
    Extension(session): Extension<Session>,
) -> Result<(StatusCode, Result<Json<UserResponse>, JsonError>), LoggedError> {
    let account = state
        .repository
        .get_account(&session.username)
        .await
        .with_context(|| format!("getting account {}", &session.username))?
        .ok_or(anyhow::Error::msg(format!(
            "account {} for valid session not found",
            &session.username
        )))?;

    Ok((
        StatusCode::OK,
        Ok(Json(UserResponse {
            username: account.username,
        })),
    ))
}
