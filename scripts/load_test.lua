-- Wrk load testing script for Sentinel AI Data Plane Proxy (v1/chat/completions)

wrk.method = "POST"
wrk.body   = '{"model":"gemini-2.0-flash","messages":[{"role":"user","content":"Ping benchmark payload"}]}'
wrk.headers["Content-Type"] = "application/json"
wrk.headers["Authorization"] = "Bearer sk-snt-live-sentinel-virtual-key-prod-01"
