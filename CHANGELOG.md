# CHANGELOG — Sentinel AI

## [v1.0.0] — 2026-07-26
### General Release — Enterprise AI Control Plane & Orchestration Platform

#### Added
- **Enterprise Model Registry & Provider Adapters**: OpenAI, Gemini, Anthropic, Ollama, Azure OpenAI, OpenRouter.
- **Streaming AI Gateway**: SSE token streaming, heartbeat telemetry, and automatic failover.
- **Employee AI Chat UI**: Premium dark glassmorphism chat interface with model switching, attachments, and markdown rendering.
- **File Context Engine**: Document intelligence (PDF, TXT, MD, Code) extraction and context injection.
- **Semantic Caching**: Sub-10ms exact and vector similarity cache.
- **Enterprise Policy Engine**: Rule-based governance evaluation.
- **AI Guardrails**: Sub-3.5ms prompt injection detection, jailbreak protection, and secret/PII redaction.
- **Virtual API Keys**: Scoped tokens (`sk-snt-live-...`) with HMAC SHA-256 constant-time verification.
- **Granular RBAC & Audit Logs**: 19 permissions across 7 built-in roles and immutable audit event logging with CSV/JSON exports.
- **FinOps & Cost Intelligence**: Real-time monthly spend tracking, budget caps, alert triggers, and end-of-month spend forecasting.
- **Observability & Timeline Replay**: Distributed tracing (`trace_id`, `correlation_id`), execution stage profiling, live provider health telemetry, and read-only request replay snapshots.
- **Multi-Tenant Organizations & Workspaces**: Domain linking, member invitations, isolated workspace hierarchy, and SAML/OIDC SSO provider abstraction.
- **Adaptive AI Routing & Intent Detection**: Sub-5ms intent detection, model capability catalog scoring, and explainable decision output.
- **Policy Simulator & What-If Analysis**: Dry-run policy impact analysis, versioning & zero-downtime rollback, AI optimization advisor, and hypothetical what-if scenario simulations.
- **Prometheus Metrics**: `GET /metrics` exposition endpoint.
- **CI/CD Pipeline**: GitHub Actions workflow for backend tests and frontend production builds.
