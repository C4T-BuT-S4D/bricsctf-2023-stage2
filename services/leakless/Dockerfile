FROM golang:1.21.3-alpine3.18 AS server-builder

WORKDIR /build
COPY src/go.mod .
COPY src/go.sum .
RUN go mod download

COPY src .
RUN go build -o leakless cmd/leakless/main.go

FROM scratch
COPY front /front
COPY --from=server-builder /build/leakless /leakless
CMD ["/leakless"]
