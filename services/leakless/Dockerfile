FROM golang:1.21-bookworm as builder

WORKDIR /app
COPY src/go.mod .
COPY src/go.sum .
RUN go mod download

COPY src .
RUN go build -o leakless cmd/leakless/main.go

FROM debian:bookworm
COPY --from=builder /app/leakless /app/
CMD ["/app/leakless"]
