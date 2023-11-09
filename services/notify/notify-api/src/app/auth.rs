use crate::app::{self, JsonError, LoggedError, Validate, ValidatedJson};
use crate::rng::APP_RNG;
use crate::session::Session;

use anyhow::{Context, Result};
use axum::{extract::State, http::StatusCode, Extension, Json};
use base64::Engine;
use once_cell::sync::Lazy;
use pwhash::md5_crypt;
use rand::RngCore;
use regex::Regex;
use serde::Deserialize;

static USERNAME_RE: Lazy<Regex> = Lazy::new(|| {
    Regex::new(r"^[a-z][a-z0-9_-]+[a-z0-9]$").expect("failed to construct username regex")
});

const SALT_BASE64_ENGINE: base64::engine::GeneralPurpose = base64::engine::GeneralPurpose::new(
    &base64::alphabet::CRYPT,
    base64::engine::general_purpose::NO_PAD,
);

#[derive(Clone, Deserialize)]
pub(super) struct RegistrationRequest {
    username: String,
    password: String,
}

impl Validate for RegistrationRequest {
    fn validate(&self) -> Result<(), String> {
        if !USERNAME_RE.is_match(&self.username) {
            return Err("We currently allow usernames consisting only of lowercase english letters, numbers, and dashes/underscores in between the rest! Sorry!".into());
        } else if self.username.len() < 5 {
            return Err(
                "Your username is too short! Please make it at least 5 characters long.".into(),
            );
        } else if self.username.len() > 15 {
            return Err(
                "Your username is too long! Please shorten it to 15 characters or less.".into(),
            );
        }

        if self.password.len() < 8 {
            return Err("Please lengthen your password to at least 8 characters, it is dangerously short right now!".into());
        } else if self.password.len() > 30 {
            return Err(
                "Your password is very long, please shorten it to 30 characters or less.".into(),
            );
        }

        Ok(())
    }
}

/// Handler implementing the POST /register API endpoint.
pub(super) async fn register_handler(
    State(state): State<app::State>,
    ValidatedJson(request): ValidatedJson<RegistrationRequest>,
) -> Result<(StatusCode, Result<Extension<Session>, JsonError>), LoggedError> {
    let salt = {
        let mut s = [0u8; 6];
        APP_RNG.with_borrow_mut(|rng| rng.fill_bytes(&mut s));
        format!("$1${}$", SALT_BASE64_ENGINE.encode(s))
    };

    #[allow(deprecated)]
    let password_hash = md5_crypt::hash_with(&*salt, request.password.as_bytes())
        .map_err(anyhow::Error::new)
        .context("hashing password")?;

    let created = state
        .repository
        .create_account(&request.username, &password_hash.to_string())
        .await
        .context("creating account")?;

    if created {
        Ok((
            StatusCode::CREATED,
            Ok(Extension(Session {
                username: request.username,
                expire: false,
            })),
        ))
    } else {
        Ok((StatusCode::CONFLICT, Err(JsonError::new("Sorry, but someone has beaten you to the punch and taken your username! You should choose another one."))))
    }
}

const INVALID_CREDENTIALS: &str =
    "Invalid credentials supplied, please validate the username and password.";

#[derive(Clone, Deserialize)]
pub(super) struct LoginRequest {
    username: String,
    password: String,
}

/// Handler implementing the POST /login API endpoint.
pub(super) async fn login_handler(
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

    if !md5_crypt::verify(request.password.as_bytes(), &password_hash) {
        return Ok((
            StatusCode::UNAUTHORIZED,
            Err(JsonError::new(INVALID_CREDENTIALS)),
        ));
    }

    Ok((
        StatusCode::OK,
        Ok(Extension(Session {
            username: request.username,
            expire: false,
        })),
    ))
}

/// Handler implementing the POST /logout API endpoint.
pub(super) async fn logout_handler() -> Extension<Session> {
    Extension(Session {
        username: String::new(),
        expire: true,
    })
}
