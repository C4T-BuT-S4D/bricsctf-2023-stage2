use crate::app::{self, LoggedError};
use crate::session::Session;

use anyhow::Context;
use axum::{extract::State, Extension, Json};
use serde::Serialize;

#[derive(Clone, Serialize)]
pub(super) struct UserResponse {
    username: String,
    notifications: Vec<app::notification::Notification>,
}

/// Handler implementing the GET /user API endpoint.
pub(super) async fn handler(
    State(state): State<app::State>,
    Extension(session): Extension<Session>,
) -> Result<Json<UserResponse>, LoggedError> {
    let notifications = state
        .repository
        .list_user_notifications(&session.username)
        .await
        .with_context(|| format!("listing user {} notifications", &session.username))?;

    Ok(Json(UserResponse {
        username: session.username,
        notifications: notifications.into_iter().map(Into::into).collect(),
    }))
}
