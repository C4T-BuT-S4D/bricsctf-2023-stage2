use crate::app::{self, LoggedError};
use crate::session::Session;

use anyhow::{anyhow, Context};
use axum::{extract::State, Extension, Json};
use serde::Serialize;

#[derive(Clone, Serialize)]
pub struct UserResponse {
    username: String,
}

/// Handler implementing the /user API endpoint.
pub async fn handler(
    State(state): State<app::State>,
    Extension(session): Extension<Session>,
) -> Result<Json<UserResponse>, LoggedError> {
    let account = state
        .repository
        .get_account(&session.username)
        .await
        .with_context(|| format!("getting account {}", &session.username))?
        .ok_or(anyhow!(
            "account {} for valid session not found",
            &session.username
        ))?;

    Ok(Json(UserResponse {
        username: account.username,
    }))
}
