use rand_chacha::{
    rand_core::{OsRng, SeedableRng},
    ChaCha12Rng,
};
use std::cell::RefCell;

thread_local! {
  pub static APP_RNG: RefCell<ChaCha12Rng> = RefCell::new(ChaCha12Rng::from_rng(&mut OsRng).expect("failed to initialize app rng"));
}
