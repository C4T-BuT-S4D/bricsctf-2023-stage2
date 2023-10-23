use crate::app::{self, JsonError, LoggedError, Validate, ValidatedJson};
use crate::repository;
use crate::session::Session;

use anyhow::Context;
use axum::extract::{Path, State};
use axum::{http::StatusCode, Extension, Json};
use serde::{Deserialize, Serialize};
use serde_with::{serde_as, DurationSeconds};
use time::{format_description::well_known::Iso8601, Duration, OffsetDateTime};
use uuid::Uuid;

#[serde_as]
#[derive(Clone, Deserialize)]
pub struct CreateNotificationRepetitions {
    count: u32,
    #[serde_as(as = "DurationSeconds<i64>")]
    interval: Duration,
}

#[serde_as]
#[derive(Clone, Deserialize)]
pub struct CreateNotificationRequest {
    title: String,
    content: String,
    #[serde_as(as = "Iso8601")]
    notify_at: OffsetDateTime,
    repetitions: Option<CreateNotificationRepetitions>,
}

#[derive(Clone, Serialize)]
pub struct CreateNotificationResponse {
    notification_id: Uuid,
}

impl Validate for CreateNotificationRequest {
    fn validate(&self) -> Result<(), String> {
        if self.title.is_empty() {
            return Err("Please add a title to be used as the subject of your notification".into());
        } else if self.title.len() > 100 {
            return Err("Sorry, but we can't store notifications with such long titles yet! Please shorten it.".into());
        }

        if self.content.is_empty() {
            return Err(
                "Please add the text which will be used as the body of your notification".into(),
            );
        } else if self.content.len() > 1000 {
            return Err("Sorry, but we can't store notifications with such long texts yet! Please shorten the notification's contents.".into());
        }

        if self.notify_at < OffsetDateTime::now_utc() {
            return Err("Please use a time in the future as the notification time.".into());
        }

        if let Some(ref repetitions) = self.repetitions {
            if repetitions.count < 1 {
                return Err(
                    "If repetitions are specified, then their count must be set to at least one."
                        .into(),
                );
            } else if repetitions.count > 10 {
                return Err("At the moment we allow repeating notifications only up to 10 additional times, sorry!".into());
            } else if repetitions.interval < Duration::SECOND {
                return Err(
                    "Please specify repetitions with at least a second as the interval between them.".into(),
                );
            } else if repetitions.interval > Duration::HOUR {
                return Err("Please use a repetition interval of an hour or less.".into());
            }
        }

        Ok(())
    }
}

pub async fn create_handler(
    State(state): State<app::State>,
    Extension(session): Extension<Session>,
    ValidatedJson(request): ValidatedJson<CreateNotificationRequest>,
) -> Result<Json<CreateNotificationResponse>, LoggedError> {
    let notification_id = state
        .repository
        .create_notification(
            &session.username,
            &repository::Notification {
                title: request.title,
                content: request.content,
                notify_at: request.notify_at,
                repetitions: request
                    .repetitions
                    .map(|r| repository::NotificationRepetitions {
                        count: r.count,
                        interval: r.interval,
                    }),
            },
        )
        .await
        .with_context(|| "creating notification")?;

    Ok(Json(CreateNotificationResponse { notification_id }))
}

#[serde_as]
#[derive(Clone, Serialize)]
pub struct GetNotificationPlan {
    #[serde_as(as = "Iso8601")]
    pub planned_at: OffsetDateTime,
    #[serde_as(as = "Option<Iso8601>")]
    pub sent_at: Option<OffsetDateTime>,
}

#[derive(Clone, Serialize)]
pub struct GetNotificationResponse {
    pub title: String,
    pub content: String,
    pub plan: Vec<GetNotificationPlan>,
}

pub async fn get_handler(
    State(state): State<app::State>,
    Path(notification_id): Path<String>,
) -> Result<(StatusCode, Result<Json<GetNotificationResponse>, JsonError>), LoggedError> {
    const NOTIFICATION_NOT_FOUND_ERROR: &str =
        "We weren't able to find notification you requested! Please check that the URL is correct.";

    // Manual parsing to return JSON error with 404 instead of 400
    let Ok(notification_id) = Uuid::try_parse(&notification_id) else {
        return Ok((
            StatusCode::NOT_FOUND,
            Err(JsonError::new(NOTIFICATION_NOT_FOUND_ERROR)),
        ));
    };

    let notification_info = state
        .repository
        .get_notification_info(&notification_id)
        .await
        .with_context(|| format!("getting notification {}", &notification_id))?;

    let Some(notification_info) = notification_info else {
        return Ok((
            StatusCode::NOT_FOUND,
            Err(JsonError::new(NOTIFICATION_NOT_FOUND_ERROR)),
        ));
    };

    Ok((
        StatusCode::OK,
        Ok(Json(GetNotificationResponse {
            title: notification_info.title,
            content: notification_info.content,
            plan: notification_info
                .plan
                .iter()
                .map(|ni| GetNotificationPlan {
                    planned_at: ni.planned_at,
                    sent_at: ni.sent_at,
                })
                .collect(),
        })),
    ))
}
