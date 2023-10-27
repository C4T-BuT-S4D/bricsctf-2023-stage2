FROM rust:1.73.0 AS builder

RUN --mount=type=cache,target=/usr/local/rustup \
  rustup toolchain install nightly-2023-10-01 && \
  rustup default nightly-2023-10-01

WORKDIR /build
RUN mkdir dir

COPY Cargo.lock Cargo.toml .
COPY src src
COPY .sqlx .sqlx

RUN \
  --mount=type=cache,target=/usr/local/cargo/registry \
  --mount=type=cache,target=/build/target \
  cargo build --release && \
  cp target/release/notify-api .

FROM ubuntu:22.04

RUN echo "nobody:x:1000:1000:::" > /etc/passwd
RUN echo "nobody::1000:nobody" > /etc/group

COPY --from=builder --chown=nobody:nobody --chmod=500 /build/notify-api /notifier/notify-api
COPY --from=builder --chown=nobody:nobody --chmod=600 /build/dir /notifier/cookie-key

WORKDIR /notifier
USER nobody

ENTRYPOINT [ "/notifier/notify-api" ]
