FROM rust:alpine AS builder

RUN apk add --no-cache build-base pkgconfig openssl-dev openssl-libs-static


WORKDIR /app

COPY Cargo.toml ./
# Create dummy main.rs to cache dependency compilation
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src

COPY src ./src
# Touch main.rs to force cargo to rebuild our binary
RUN touch src/main.rs
RUN cargo build --release

FROM alpine:3.20

RUN apk add --no-cache ca-certificates libgcc

WORKDIR /app

COPY --from=builder /app/target/release/sentinel-data-plane /app/sentinel-data-plane

EXPOSE 8080

CMD ["/app/sentinel-data-plane"]
