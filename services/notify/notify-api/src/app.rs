pub mod login;
pub mod register;

use axum::extract::rejection::JsonRejection;
use axum::extract::FromRequest;
use axum::http::{Request, StatusCode};
use axum::{async_trait, Json};
use serde::Serialize;

trait Validate {
    fn validate(&self) -> Result<(), String>;
}

pub struct ValidatedJson<T>(pub T);

#[derive(Serialize)]
pub struct JsonError {
    error: String,
}

#[async_trait]
impl<T, S, B> FromRequest<S, B> for ValidatedJson<T>
where
    T: Validate,
    S: Send + Sync,
    B: Send + 'static,
    Json<T>: FromRequest<S, B, Rejection = JsonRejection>,
{
    type Rejection = (StatusCode, Json<JsonError>);

    async fn from_request(req: Request<B>, state: &S) -> Result<Self, Self::Rejection> {
        let Json(data) = Json::<T>::from_request(req, state)
            .await
            .map_err(|rejection| {
                (
                    rejection.status(),
                    Json(JsonError {
                        error: rejection.body_text(),
                    }),
                )
            })?;

        data.validate().map_err(|e| {
            (
                StatusCode::UNPROCESSABLE_ENTITY,
                Json(JsonError { error: e }),
            )
        })?;

        Ok(Self(data))
    }
}
