use anyhow::{Context, Result};
use std::env;
use std::net::SocketAddr;

/// API configuration read from the available environment variables.
pub struct Config {
    pub listen_addr: SocketAddr,
    pub database_url: String,
    pub cookie_key_path: String,
    pub notifier_secret_path: String,
    pub notifier_server_addr: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let listen_addr: SocketAddr = env::var("LISTEN_ADDR")
            .map_err(anyhow::Error::new)
            .and_then(|v| v.parse().map_err(anyhow::Error::new))
            .context("failed to read LISTEN_ADDR from env")?;

        let database_url =
            env::var("DATABASE_URL").context("failed to read DATABASE_URL from env")?;

        let cookie_key_path =
            env::var("COOKIE_KEY_PATH").context("failed to read COOKIE_KEY_PATH from env")?;

        let notifier_secret_path = env::var("NOTIFIER_SECRET_PATH")
            .context("failed to read NOTIFIER_SECRET_PATH from env")?;

        let notifier_server_addr = env::var("NOTIFIER_SERVER_ADDR")
            .context("failed to read NOTIFIER_SERVER_ADDR from env")?;

        Ok(Self {
            listen_addr,
            database_url,
            cookie_key_path,
            notifier_secret_path,
            notifier_server_addr,
        })
    }
}
