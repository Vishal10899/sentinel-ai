use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct ProviderHealth {
    pub provider_id: String,
    pub total_calls: u64,
    pub failed_calls: u64,
    pub total_latency_ms: u128,
    pub last_failure: Option<Instant>,
    pub is_healthy: bool,
}

#[derive(Clone)]
pub struct CircuitBreakerManager {
    providers: Arc<Mutex<HashMap<String, ProviderHealth>>>,
    failure_threshold_percent: f64,
    latency_threshold_ms: u128,
}

impl CircuitBreakerManager {
    pub fn new() -> Self {
        Self {
            providers: Arc::new(Mutex::new(HashMap::new())),
            failure_threshold_percent: 5.0,
            latency_threshold_ms: 1500,
        }
    }

    pub fn record_call(&self, provider_id: &str, latency_ms: u128, is_success: bool) {
        let mut map = self.providers.lock().unwrap();
        let entry = map.entry(provider_id.to_string()).or_insert(ProviderHealth {
            provider_id: provider_id.to_string(),
            total_calls: 0,
            failed_calls: 0,
            total_latency_ms: 0,
            last_failure: None,
            is_healthy: true,
        });

        entry.total_calls += 1;
        entry.total_latency_ms += latency_ms;
        if !is_success {
            entry.failed_calls += 1;
            entry.last_failure = Some(Instant::now());
        }

        // Evaluate sliding window metrics
        let fail_rate = (entry.failed_calls as f64 / entry.total_calls as f64) * 100.0;
        let avg_latency = entry.total_latency_ms / entry.total_calls as u128;

        if fail_rate >= self.failure_threshold_percent || avg_latency > self.latency_threshold_ms {
            entry.is_healthy = false;
        } else {
            entry.is_healthy = true;
        }
    }

    pub fn is_healthy(&self, provider_id: &str) -> bool {
        let map = self.providers.lock().unwrap();
        if let Some(entry) = map.get(provider_id) {
            if !entry.is_healthy {
                // Auto-recover after 30s cooldonw
                if let Some(last_fail) = entry.last_failure {
                    if last_fail.elapsed() > Duration::from_secs(30) {
                        return true;
                    }
                }
                return false;
            }
        }
        true
    }
}
