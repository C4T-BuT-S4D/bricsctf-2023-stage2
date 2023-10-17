use crate::app::{Validate, ValidatedJson};
use crate::session::Session;

use axum::http::StatusCode;
use axum::Extension;
use lazy_static::lazy_static;
use regex::Regex;
use serde::Deserialize;

lazy_static! {
    static ref USERNAME_RE: Regex =
        Regex::new(r"^[a-z0-9][a-z0-9_-]+[a-z0-9]$").expect("failed to construct username regex");
}

#[derive(Clone, Deserialize)]
pub struct RegistrationRequest {
    username: String,
    password: String,
}

impl Validate for RegistrationRequest {
    fn validate(&self) -> Result<(), String> {
        if !USERNAME_RE.is_match(&self.username) {
            return Err("We currently allow usernames consisting only of lowercase english letters, numbers, and dashes/underscores in between the rest! Sorry!".to_owned());
        } else if self.username.len() < 5 {
            return Err(
                "Your username is too short! Please make it at least 5 characters long.".to_owned(),
            );
        } else if self.username.len() > 15 {
            return Err(
                "Your username is too long! Please shorten it to 15 characters or less.".to_owned(),
            );
        }

        if self.password.len() < 8 {
            return Err("Please lengthen your password to at least 8 characters, it is dangerously short right now!".to_owned());
        } else if self.password.len() > 30 {
            return Err(
                "Your password is very long, please shorten it to 30 characters or less."
                    .to_owned(),
            );
        }

        Ok(())
    }
}

/// Handler implementing the /register API endpoint.
pub async fn handler(
    ValidatedJson(request): ValidatedJson<RegistrationRequest>,
) -> (Option<Extension<Session>>, StatusCode) {
    (
        Some(Extension(Session {
            username: request.username,
        })),
        StatusCode::CREATED,
    )
}
