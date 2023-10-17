use crate::session::Session;

use axum::http::StatusCode;
use axum::{Extension, Json};
use serde::Deserialize;

#[derive(Clone, Deserialize)]
pub struct LoginRequest {
    username: String,
    password: String,
}

/// Handler implementing the /login API endpoint.
pub async fn handler(
    Json(request): Json<LoginRequest>,
) -> (Option<Extension<Session>>, StatusCode) {
    (
        Some(Extension(Session {
            username: request.username,
        })),
        StatusCode::OK,
    )
}
