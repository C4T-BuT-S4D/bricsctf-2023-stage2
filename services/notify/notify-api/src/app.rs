mod login;
mod notification;
mod register;
mod user;

use crate::repository::Repository;
use crate::session::Session;

use axum::extract::{rejection::JsonRejection, FromRequest};
use axum::http::{Request, StatusCode};
use axum::middleware::{self, Next};
use axum::response::{IntoResponse, Response};
use axum::{async_trait, routing, Extension, Json, Router};
use serde::Serialize;
use tracing::error;

trait Validate {
    fn validate(&self) -> Result<(), String>;
}

struct ValidatedJson<T>(pub T);

#[derive(Clone, Serialize)]
struct JsonError {
    error: String,
}

impl JsonError {
    fn new(err: &str) -> Self {
        Self { error: err.into() }
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

        (StatusCode::INTERNAL_SERVER_ERROR, JsonError{error: "Unexpected internal error has occurred! The admins are already working to fix it...".into()}).into_response()
    }
}

#[derive(Clone)]
pub struct State {
    pub repository: Repository,
}

async fn authentication_layer<B>(
    Extension(session): Extension<Option<Session>>,
    mut request: Request<B>,
    next: Next<B>,
) -> Response {
    if session.is_none() {
        return (StatusCode::UNAUTHORIZED, JsonError::new("Please reauthenticate using the login functionality or create a new account in order to proceed.")).into_response();
    }

    request.extensions_mut().insert(session.unwrap());

    next.run(request).await
}

/// Build and return the API router itself, to be merged with the middlewares and other layers.
pub fn router() -> Router<State> {
    let unauthenticated_router = Router::new()
        .route("/register", routing::post(register::handler))
        .route("/login", routing::post(login::handler))
        .route(
            "/notification/:notification_id",
            routing::get(notification::get_handler),
        );

    let authenticated_router = Router::new()
        .route("/user", routing::get(user::handler))
        .route(
            "/notifications",
            routing::post(notification::create_handler),
        )
        .layer(middleware::from_fn(authentication_layer));

    unauthenticated_router.merge(authenticated_router)
}
