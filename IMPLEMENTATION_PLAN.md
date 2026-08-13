# SENTINEL AI — FINAL PRE-LAUNCH ENGINEERING FREEZE
## Evidence-Based Implementation Plan & Audit Matrix

**Project:** SENTINEL AI Enterprise Control Plane  
**Status:** Pre-Launch Engineering Freeze  
**Target Repository:** `D:/sentinal ai/sentinel-ai`  
**Architectural Mandate:** Production Readiness, Zero Redesign, Zero Duplicate Services, 100% Empirical Verification.

---

## 1. EVIDENCE MATRIX & FINDINGS AUDIT

Below is the complete audit of existing codebase components, identified gaps, severity, recommended actions, and launch-blocking status based on direct inspection of the code.

| # | Subsystem / File | Function / Class | Current Behavior | Evidence | Problem | Severity | Recommended Action | Launch-Blocking? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Docker Compose Prod**<br>`docker-compose.prod.yml` | `services:` | Defines `backend`, `postgres`, and `redis` only. | [`docker-compose.prod.yml`](file:///D:/sentinal%20ai/sentinel-ai/docker-compose.prod.yml#L3-L67) | `ollama` and `qdrant` containers and volumes are missing from production configuration. | **HIGH** | Add `ollama` (with persistent volume `ollama_prod_data:/root/.ollama`) and `qdrant` services to `docker-compose.prod.yml`. | **YES** |
| **2** | **SSE Stream Disconnect**<br>`backend/app/chat/service.py` & `backend/app/api/routers/chat.py` | `ChatService.stream_generate()` | Streams token chunks via SSE. Checks `session.is_cancelled()`. | [`service.py:L626`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/chat/service.py#L626) | HTTP connection closure (tab close/refresh) is not automatically detected by FastAPI `StreamingResponse` without checking request disconnect state. | **HIGH** | Pass `Request` object into stream generator and check `await request.is_disconnected()`, triggering `stream_manager.cancel_session()` immediately. | **YES** |
| **3** | **Virtual Keys Persistence**<br>`backend/app/security/repository.py` | `VirtualKeyRepository` | Stores Virtual API Keys in process memory `_keys_db: dict`. | [`repository.py:L18`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/security/repository.py#L18) | Virtual API Keys vanish whenever the FastAPI backend process restarts. | **HIGH** | Create SQLAlchemy model `VirtualKeyConfig` in `app/models/` and persist keys to PostgreSQL. | **YES** |
| **4** | **Audit & Policy Persistence**<br>`backend/app/audit/engine.py` & `backend/app/policy/repository.py` | `AuditEngine`, `PolicyRepository` | Audit logs stored in `_events: list`, policies stored in `_policies: dict`. | [`engine.py:L16`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/audit/engine.py#L16), [`repository.py:L14`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/policy/repository.py#L14) | Compliance audit logs and custom governance policies disappear on process restart. | **HIGH** | Create SQLAlchemy models `AuditEventModel` and `PolicyRuleModel` and persist data to PostgreSQL. | **YES** |
| **5** | **Developer Gateway Proxy**<br>`backend/app/api/routers/` | *Missing Gateway Router* | API routers support internal UI (`/api/v1/chat/stream`), but lack OpenAI SDK proxy. | Grep search confirms `/v1/chat/completions` is absent from router files. | Developers cannot use Sentinel AI as an invisible gateway via standard OpenAI SDKs (`base_url="http://localhost:8000/v1"`). | **HIGH** | Create `backend/app/api/routers/openai_gateway.py` mounting `/v1/chat/completions`, `/v1/models`, `/v1/embeddings` with Virtual Key Bearer auth. | **YES** |
| **6** | **Routing Engine Consolidation**<br>`backend/app/routing/router.py` & `backend/app/orchestration/router.py` | `IntelligentRouter` vs `AdaptiveRouter` | Dual candidate scoring path (`IntelligentRouter` strategy scoring vs `AdaptiveRouter` 5-stage intent profiling). | [`chat/service.py:L74-L146`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/chat/service.py#L74-L146) | Violates Rule #4 (duplicate implementations). Creates fragmented decision explanations and analytics. | **MEDIUM** | Unify strategy evaluation (`Balanced`, `Cheapest`, `Fastest`, `Quality`) inside `AdaptiveRouter`, making it the single authoritative routing engine. | **YES** |
| **7** | **Qdrant Vector Cache Integration**<br>`backend/app/cache/semantic.py` | `SemanticCache` & `CacheStore` | Uses in-memory TF-IDF vector embedding engine and dictionary store. | [`semantic.py:L20`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/cache/semantic.py#L20) | Vector cache is not persisted to Qdrant vector database (`qdrant/qdrant:v1.12.1`), preventing cross-worker cache sharing. | **MEDIUM** | Add Qdrant Client store adapter in `SemanticCache` to sync vector embeddings with Qdrant collection `sentinel_semantic_cache`. | **YES** |
| **8** | **Database Default Seed Data**<br>`backend/app/core/lifecycle.py` & `app/repositories/conversation_repository.py` | `_run_migrations()`, `ConversationRepository.create()` | Auto-creates `default_user` and `default` workspace on startup or missing workspace. | [`lifecycle.py:L40-L50`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/core/lifecycle.py#L40-L50), [`conversation_repository.py:L25-L54`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/repositories/conversation_repository.py#L25-L54) | Direct `asyncio.run()` inside `_run_migrations` thread causes event loop warnings; workspace lookup handling requires clean transaction safety. | **MEDIUM** | Clean up startup database initialization in `lifecycle.py` and ensure `WorkspaceRepository` gracefully handles default workspace lookup. | **YES** |

---

## 2. STEP-BY-STEP EXECUTION ROADMAP

Follow the strict progression mandated by the engineering freeze:

```
[Phase 1: Core Reliability] -> [Phase 2: Security Persistence] -> [Phase 3: Developer Gateway] -> [Phase 4: Explainable Routing Consolidation] -> [Phase 5: Qdrant Vector Cache] -> [Phase 6: Verification & End-to-End Testing]
```

### Phase 1: CORE RELIABILITY
1. **Production Infrastructure Parity (`docker-compose.prod.yml`):**
   - Add `ollama` container definition with `ollama_prod_data:/root/.ollama` volume.
   - Add `qdrant` container definition (`qdrant/qdrant:v1.12.1`) with `qdrant_prod_data:/qdrant/storage`.
   - Ensure all services belong to `sentinel-network`.
2. **Client Disconnect Signal Handling:**
   - Update `stream_generate` endpoint in [`backend/app/api/routers/chat.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/api/routers/chat.py) to accept `request: Request`.
   - Inject periodic `await request.is_disconnected()` check into `ChatService._stream_generate_impl()` token loop. If disconnected, log cancellation and call `stream_manager.cancel_session(session.stream_id)`.
3. **Database Lifespan & Seeding Clean Up:**
   - Refactor `lifecycle.py` startup database initialization to execute clean async migrations and seed default user/workspace cleanly within the main event loop context.

### Phase 2: MAKE SECURITY REAL (Database Persistence)
1. **Virtual API Keys Database Persistence:**
   - Add `VirtualKeyModel` in [`backend/app/models/virtual_key.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/models/virtual_key.py) with columns `id`, `name`, `key_hash`, `prefix`, `workspace_id`, `key_type`, `allowed_providers`, `allowed_models`, `expires_at`, `created_at`.
   - Update [`backend/app/security/repository.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/security/repository.py) to persist and query virtual keys using SQLAlchemy async sessions.
2. **Audit Log & Policy Rules Database Persistence:**
   - Add `AuditEventModel` in [`backend/app/models/audit.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/models/audit.py) and `PolicyRuleModel` in [`backend/app/models/policy.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/models/policy.py).
   - Update `AuditEngine` and `PolicyRepository` to store and query events/policies in PostgreSQL.

### Phase 3: MAKE THE GATEWAY REAL (OpenAI-Compatible Proxy)
1. **Create OpenAI Gateway Router ([`backend/app/api/routers/openai_gateway.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/api/routers/openai_gateway.py)):**
   - Implements endpoints:
     - `POST /v1/chat/completions` (Supports standard OpenAI JSON request, non-streaming & streaming responses `text/event-stream`).
     - `GET /v1/models` (Returns list of enabled catalog models in OpenAI format).
     - `POST /v1/embeddings` (Routes vector embedding request to active provider/Ollama).
   - Authenticates requests via `Authorization: Bearer sk-sentinel-...` using `virtual_key_repository.validate_key()`.
   - Transforms OpenAI payload into `ChatRequest`, routes through `chat_service`, and maps response back to standard OpenAI response format.
2. **Register Gateway Router in [`backend/app/main.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/main.py):**
   - Mount router at `/v1` prefix.

### Phase 4: MAKE DECISIONS EXPLAINABLE (Routing Engine Consolidation)
1. **Unify Strategy Evaluation in `AdaptiveRouter` ([`backend/app/orchestration/router.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/orchestration/router.py)):**
   - Integrate strategy weighting (`cost`, `latency`, `balanced`, `quality`, `reasoning_optimized`) into `AdaptiveRouter.route()`.
   - Deprecate parallel scoring in `IntelligentRouter`, ensuring a single, provider-agnostic decision pipeline.
   - Ensure every routing decision generates a complete `RoutingDecisionExplanation` with candidate rankings and primary rationale.

### Phase 5: AI MEMORY & QDRANT VECTOR CACHE INTEGRATION
1. **Integrate Qdrant Client in `SemanticCache` ([`backend/app/cache/semantic.py`](file:///D:/sentinal%20ai/sentinel-ai/backend/app/cache/semantic.py)):**
   - Add Qdrant client connection initialization targeting `settings.qdrant_url` (`http://qdrant:6333` or `http://localhost:6333`).
   - Create collection `sentinel_semantic_cache` with 128-dim Cosine vector distance configuration.
   - Store and search vector embeddings in Qdrant when reachable, falling back gracefully to in-memory `CacheStore`.

### Phase 6: VERIFICATION & END-TO-END TESTING
1. **End-to-End Verification Script:**
   - Execute verification suite checking:
     - Database persistence for Users, Workspaces, Conversations, Messages, Virtual Keys, Audit Logs, Policies.
     - OpenAI Gateway proxy endpoints (`/v1/chat/completions`, `/v1/models`).
     - Live Provider connectivity (Ollama, Gemini, OpenAI).
     - SSE streaming and connection disconnect handling.
     - Qdrant collection creation and vector search retrieval.
     - Frontend UI integration and API client SDK calls.

---

## 3. VERIFICATION & SUCCESS CRITERIA

Before marking the pre-launch engineering freeze complete:
- [ ] All database entities (Workspaces, Conversations, Messages, Virtual Keys, Audit Logs, Policies) persist across backend container restarts.
- [ ] OpenAI SDK can execute chat completions using `http://localhost:8000/v1` base URL and a valid Virtual Key (`sk-sentinel-...`).
- [ ] Client SSE disconnects immediately abort backend LLM provider streaming loops.
- [ ] Routing decisions are 100% explainable, provider-agnostic, and evaluated through unified `AdaptiveRouter`.
- [ ] Production Compose file (`docker-compose.prod.yml`) contains all required services (`backend`, `postgres`, `redis`, `ollama`, `qdrant`).
- [ ] Empirical test scripts pass 100% clean with zero unhandled exceptions.

---
*End of Implementation Plan.*
