use anyhow::{Context, Result};
use std::env;
use std::net::SocketAddr;

/// API configuration read from the available environment variables.
pub struct Config {
    pub listen_addr: SocketAddr,
    pub cookie_key_path: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let listen_addr: SocketAddr = env::var("LISTEN_ADDR")
            .map_err(anyhow::Error::new)
            .and_then(|v| v.parse().map_err(anyhow::Error::new))
            .with_context(|| "failed to read LISTEN_ADDR from env")?;

        let cookie_key_path = env::var("COOKIE_KEY_PATH")
            .with_context(|| "failed to read COOKIE_KEY_PATH from env")?;

        Ok(Self {
            listen_addr,
            cookie_key_path,
        })
    }
}
