use axum::{
    body::Body,
    extract::State,
    http::{HeaderMap, StatusCode},
    response::Response,
    Json,
};
use serde_json::Value;
use std::sync::Arc;
use std::time::Instant;

use crate::circuit_breaker::CircuitBreakerManager;
use crate::dlp::DlpEngine;
use crate::cache::ProxyCacheEngine;

#[derive(Clone)]
pub struct AppState {
    pub dlp: DlpEngine,
    pub circuit_breaker: CircuitBreakerManager,
    pub cache: ProxyCacheEngine,
    pub control_plane_url: String,
}

pub async fn handle_openai_chat_completions(
    State(state): State<Arc<AppState>>,
    headers: HeaderMap,
    Json(mut payload): Json<Value>,
) -> Result<Response, (StatusCode, String)> {
    let start_time = Instant::now();

    // 1. Zero-copy / Inline DLP Redaction on Prompt Payload
    if let Some(messages) = payload.get_mut("messages") {
        if let Some(msg_arr) = messages.as_array_mut() {
            for msg in msg_arr {
                if let Some(content) = msg.get("content").and_then(|c| c.as_str()) {
                    let redacted = state.dlp.inspect_and_redact(content);
                    msg["content"] = Value::String(redacted);
                }
            }
        }
    }

    // 2. Health & Circuit Breaker Check - Distinguish requested vs actual model
    let requested_model = payload
        .get("model")
        .and_then(|m| m.as_str())
        .unwrap_or("gpt-4o")
        .to_string();

    let actual_model = if !state.circuit_breaker.is_healthy(&requested_model) {
        let fallback = "gpt-4o-mini".to_string();
        payload["model"] = Value::String(fallback.clone());
        fallback
    } else {
        requested_model.clone()
    };

    // 3. Forward to upstream LLM / Control Plane Proxy Engine
    let client = reqwest::Client::new();
    let upstream_resp = client
        .post(format!("{}/v1/chat/completions", state.control_plane_url))
        .headers(headers.clone())
        .json(&payload)
        .send()
        .await;

    let latency_ms = start_time.elapsed().as_millis();

    match upstream_resp {
        Ok(resp) => {
            let status = resp.status();
            let is_success = status.is_success();
            state.circuit_breaker.record_call(&actual_model, latency_ms, is_success);

            let body_bytes = resp.bytes().await.map_err(|e| {
                (StatusCode::INTERNAL_SERVER_ERROR, format!("Failed reading upstream response: {}", e))
            })?;

            let response = Response::builder()
                .status(status)
                .header("X-Sentinel-DataPlane-Latency-US", format!("{}", start_time.elapsed().as_micros()))
                .header("X-Sentinel-DataPlane-Status", "PROXY_OK")
                .header("X-Sentinel-Requested-Model", requested_model)
                .header("X-Sentinel-Actual-Model", &actual_model)
                .body(Body::from(body_bytes))
                .map_err(|e| (StatusCode::INTERNAL_SERVER_ERROR, e.to_string()))?;

            Ok(response)
        }
        Err(err) => {
            state.circuit_breaker.record_call(&actual_model, latency_ms, false);
            Err((StatusCode::BAD_GATEWAY, format!("Upstream Provider Proxy Error: {}", err)))
        }
    }
}

