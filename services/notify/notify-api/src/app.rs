mod login;
mod register;

use crate::repository::Repository;

use axum::extract::rejection::JsonRejection;
use axum::extract::FromRequest;
use axum::http::{Request, StatusCode};
use axum::response::{IntoResponse, Response};
use axum::{async_trait, Json};
use axum::{routing, Router};
use serde::Serialize;
use tracing::error;

trait Validate {
    fn validate(&self) -> Result<(), String>;
}

struct ValidatedJson<T>(pub T);

#[derive(Serialize)]
struct JsonError {
    error: String,
}

impl JsonError {
    fn new(err: &str) -> Self {
        Self {
            error: err.to_owned(),
        }
    }
}

impl IntoResponse for JsonError {
    fn into_response(self) -> Response {
        Json(self).into_response()
    }
}

#[async_trait]
impl<T, S, B> FromRequest<S, B> for ValidatedJson<T>
where
    T: Validate,
    S: Send + Sync,
    B: Send + 'static,
    Json<T>: FromRequest<S, B, Rejection = JsonRejection>,
{
    type Rejection = (StatusCode, JsonError);

    async fn from_request(req: Request<B>, state: &S) -> Result<Self, Self::Rejection> {
        let Json(data) = Json::<T>::from_request(req, state)
            .await
            .map_err(|rejection| (rejection.status(), JsonError::new(&rejection.body_text())))?;

        data.validate()
            .map_err(|e| (StatusCode::UNPROCESSABLE_ENTITY, JsonError::new(&e)))?;

        Ok(Self(data))
    }
}

struct LoggedError(anyhow::Error);

impl From<anyhow::Error> for LoggedError {
    fn from(e: anyhow::Error) -> Self {
        Self(e)
    }
}

impl IntoResponse for LoggedError {
    fn into_response(self) -> Response {
        error!(
            error = format!("{:#}", self.0),
            "unexpected internal error while handling request"
        );

        (StatusCode::INTERNAL_SERVER_ERROR, JsonError{error: "Unexpected internal error has occurred! The admins are already working to fix it...".to_owned()}).into_response()
    }
}

#[derive(Clone)]
pub struct State {
    pub repository: Repository,
}

/// Build and return the API router itself, to be merged with the middlewares and other layers.
pub fn router() -> Router<State> {
    Router::new()
        .route("/register", routing::post(register::handler))
        .route("/login", routing::post(login::handler))
}
