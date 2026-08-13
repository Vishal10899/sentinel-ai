mod cache;
mod circuit_breaker;
mod dlp;
mod proxy;

use axum::{
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use std::sync::Arc;
use tower_http::cors::CorsLayer;
use tracing_subscriber::layer::SubscriberExt;
use tracing_subscriber::util::SubscriberInitExt;

use crate::cache::ProxyCacheEngine;
use crate::circuit_breaker::CircuitBreakerManager;
use crate::dlp::DlpEngine;
use crate::proxy::{handle_openai_chat_completions, AppState};

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new("info"))
        .with(tracing_subscriber::fmt::layer())
        .init();

    let dlp = DlpEngine::new();
    let circuit_breaker = CircuitBreakerManager::new();
    let cache = ProxyCacheEngine::new(
        std::env::var("REDIS_URL").unwrap_or_else(|_| "redis://localhost:6379".to_string()),
        std::env::var("QDRANT_URL").unwrap_or_else(|_| "http://localhost:6333".to_string()),
    );
    let control_plane_url = std::env::var("CONTROL_PLANE_URL").unwrap_or_else(|_| "http://localhost:8000".to_string());

    let state = Arc::new(AppState {
        dlp,
        circuit_breaker,
        cache,
        control_plane_url,
    });

    let app = Router::new()
        .route("/health", get(|| async { "SENTINEL_RUST_DATAPLANE_HEALTHY" }))
        .route("/v1/chat/completions", post(handle_openai_chat_completions))
        .layer(CorsLayer::permissive())
        .with_state(state);

    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("🛡️ Sentinel AI Rust Data Plane Proxy listening on http://{}", addr);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}
