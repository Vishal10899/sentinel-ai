# SENTINEL DECISION INTELLIGENCE ENGINE

This document defines the architecture, decision logic, and core intellectual property (IP) of the Sentinel Decision Intelligence Engine. It establishes how Sentinel evaluates, protects, optimizes, and routes enterprise AI requests before any payload reaches a model provider.

---

## 1. WHAT IS THE DECISION INTELLIGENCE ENGINE?

### The Fallacy of "Smart Routing"
Most AI proxies implement simple "Smart Routing"—a glorified fallback list or static IF/ELSE rule matrix (e.g., *"If OpenAI returns HTTP 429, call Anthropic"*). 

Simple routing fails at enterprise scale because it is reactive, blind to payload context, ignorant of financial budgets, and indifferent to security compliance.

### The Decision Intelligence Principle
Sentinel does not route requests; **Sentinel evaluates execution feasibility and trade-offs.**

The Decision Intelligence Engine is a multi-dimensional, deterministic evaluation brain. It treats every AI request as an enterprise transaction with five non-negotiable constraints:
1. **Security & Governance Boundary** (Must not leak data or violate policy)
2. **Fidelity & Quality Expectation** (Must satisfy task reasoning requirements)
3. **Latency & SLA Tolerance** (Must meet application execution speed)
4. **Financial Cost Efficiency** (Must minimize token expenditure)
5. **Provider Resilience & Availability** (Must guarantee execution uptime)

Before a single token leaves the enterprise network boundary, Sentinel scores the request against all five constraints simultaneously to render a single, explainable execution decision.

---

## 2. WHY IT EXISTS

### Enterprise Problems Solved

1. **Frontier Model Over-Provisioning**  
   Developers default to flagship frontier models (e.g., GPT-4o, Claude 3.5 Sonnet) for basic tasks such as sentiment classification or JSON formatting. This results in 70%–90% cost over-allocation without any measurable quality improvement.

2. **Compliance & Privacy Exposure**  
   Engineering teams hardcode third-party API endpoints directly into microservices. Unsanitized customer PII, internal financial figures, and secret keys bypass security inspection, creating severe regulatory liability.

3. **Brittle Vendor Lock-In & Unplanned Outages**  
   Direct application-to-LLM coupling creates single points of failure. When a primary model provider suffers service degradation, rate limits, or regional outages, downstream application features halt entirely.

4. **Zero Financial Budget Controls**  
   Without centralized decision-making, individual software teams consume token allocations uncontrollably. FinOps teams only discover budget overruns weeks later on monthly cloud invoices.

### Why Routing Alone Is Insufficient
Routing is merely the final mechanical step of a decision pipeline. If an engine routes a prompt without first inspecting its PII content, validating workspace budget caps, checking semantic vector caches, or assessing prompt injection threats, the system has failed enterprise requirements regardless of which model processes the prompt.

---

## 3. THE 18-STAGE DECISION PIPELINE

Every incoming enterprise request travels through an 18-stage evaluation pipeline:

```
01. Request Ingress & Metadata Tagging
    ↓
02. Identity & Virtual Key Authentication
    ↓
03. Workspace & Role Governance Policy Check
    ↓
04. Prompt Injection & Threat Vector Scan
    ↓
05. Inline PII & Corporate Secret DLP Sanitization
    ↓
06. Semantic Intent Classification
    ↓
07. Task Complexity & Fidelity Scoring
    ↓
08. Context Window & Token Payload Analysis
    ↓
09. Vector Embedding Semantic Cache Inspection
    ↓
10. Context Compression & Token Minimization
    ↓
11. Workspace Budget Cap & Rate Limit Evaluation
    ↓
12. Application Latency SLA Requirement Check
    ↓
13. Model Capability & Modality Catalog Matching
    ↓
14. Real-Time Provider Health & Error Rate Assessment
    ↓
15. Predictive Cost Calculation & Trade-Off Matrix
    ↓
16. Final Model Selection & Routing Decision
    ↓
17. Provider Execution & Stream Interception
    ↓
18. Unified Telemetry, Trace Logging & Cost Audit Logging
```

### Detailed Stage Breakdown

- **01. Ingress & Metadata Tagging:** Intercepts payload and extracts application ID, user identity, department tag, target environment (production vs. staging), and SLA flags.
- **02. Authentication:** Validates virtual API key hash in constant time and verifies organization tenancy scope.
- **03. Governance Policy Check:** Evaluates enterprise rules (e.g., blocked providers, disallowed model classes, mandatory data residency).
- **04. Threat Vector Scan:** Inspects prompt for 42 known jailbreak patterns, system prompt override attempts, and adversarial injection strings.
- **05. DLP Sanitization:** Identifies and redacts Social Security Numbers, credit cards, internal API credentials, and customer PII in under 3.5ms.
- **06. Intent Classification:** Categorizes workload type (e.g., `CODING`, `MATH`, `REASONING`, `CLASSIFICATION`, `SUMMARIZATION`, `VISION`).
- **07. Task Complexity Analysis:** Evaluates structural depth, reasoning steps required, and output schema constraints to assign a complexity index (0.0 to 1.0).
- **08. Context Length Analysis:** Calculates prompt token count, inspects context window bounds, and determines maximum completion buffer needed.
- **09. Semantic Cache Inspection:** Computes vector similarity against past enterprise queries. On high-confidence similarity match (> 98%), returns cached response immediately ($0.00 cost, < 2ms latency).
- **10. Token Compression:** Strips redundant whitespace, system prompt duplications, and non-essential conversational padding to compress payload tokens.
- **11. Budget Evaluation:** Verifies virtual key and department budget limits. Rejects or throttles requests exceeding hard caps.
- **12. Latency SLA Check:** Compares application speed requirement (e.g., real-time autocomplete < 100ms vs. batch document audit < 5s) against model TTFT (Time-To-First-Token) distributions.
- **13. Capability Matching:** Filters model catalog for required modalities (e.g., native JSON mode, tool calling, vision, multi-turn context).
- **14. Provider Health Check:** Evaluates real-time P99 latency histograms, HTTP 5xx error rates, and active rate limit status across cloud endpoints.
- **15. Predictive Cost Calculation:** Computes exact expected token cost across all qualified model candidates.
- **16. Final Decision Rendering:** Weighs cost delta against quality risk score to select the optimal target model.
- **17. Provider Execution:** Dispatches sanitized payload to the chosen provider endpoint with fallback triggers active.
- **18. Telemetry Collection:** Captures total execution span, token consumption, cost savings offloaded, and audit records.

---

## 4. MULTI-DIMENSIONAL DECISION FACTORS

Sentinel evaluates 20 distinct factors before rendering a decision:

| Category | Decision Factor | Enterprise Evaluation Criteria |
| :--- | :--- | :--- |
| **Workload** | **Task Intent** | Classification, Code Generation, Mathematical Proof, Summarization, Vision Analysis |
| **Workload** | **Complexity Score** | Structural token depth, multi-step logic requirement, ambiguity index (0.0–1.0) |
| **Workload** | **Context Size** | Small (< 2k tokens), Medium (< 32k tokens), Long Context (> 128k tokens) |
| **Workload** | **Modality Scope** | Text-only, Multi-Modal Vision, Audio Input, Structured JSON Output |
| **SLA & Performance** | **Target Latency** | Ultra-Fast (< 100ms), Interactive (< 500ms), Asynchronous Batch (< 10s) |
| **SLA & Performance** | **Streaming Requirement** | Real-time Server-Sent Events (SSE) token streaming vs. unary response payload |
| **SLA & Performance** | **Time-To-First-Token** | Historical P50/P90/P99 TTFT distribution per provider endpoint |
| **Security & Governance** | **Security Level** | Public data, Internal Restricted, Confidential PII, Highly Regulated Healthcare/Finance |
| **Security & Governance** | **Compliance Mandates** | SOC2, HIPAA, GDPR, ISO 27001, Data Residency (EU-only, US-only, On-Prem) |
| **Security & Governance** | **User Role & Scope** | Executive, Senior Developer, External Contractor, Service Account, Automated Bot |
| **Security & Governance** | **Department Budget** | Current spend vs. monthly allocation, rate limit remaining, quota caps |
| **Provider & Infrastructure** | **Endpoint Availability** | Provider status, HTTP 5xx error rate in last 60s, active 429 rate-limit backoff |
| **Provider & Infrastructure** | **Model Fidelity Score** | Benchmark accuracy score for target intent (e.g., HumanEval score for coding) |
| **Provider & Infrastructure** | **Unit Cost per 1K Tokens** | Prompt vs. completion token pricing delta across available model providers |

---

## 5. REAL-WORLD ENTERPRISE DECISION FLOWS

### Case A: Customer Support Ticket Classification
- **Application:** Zendesk Automated Routing Pipeline
- **Raw Prompt:** *"Categorize support ticket #90412: 'Billing API returned HTTP 500 error during checkout'. Priority score?"*
- **Sentinel Evaluation:**
  - *Intent:* Low-complexity classification (Complexity: 0.12).
  - *Security Check:* Customer email detected and sanitized inline.
  - *Cache Check:* 99.1% vector similarity match found in semantic cache.
- **Sentinel Decision:** **Served directly from Semantic Cache** ($0.00 token cost, 1.8ms response time). GPT-4o call avoided.

### Case B: Software Development Code Refactoring
- **Application:** Enterprise CI/CD Pipeline Agent
- **Raw Prompt:** *"Scan deployment.yaml for root privilege escalations and hardcoded AWS_SECRET_ACCESS_KEY='AKIAIOSFODNN7EXAMPLE'. Provide patch."*
- **Sentinel Evaluation:**
  - *Intent:* Code vulnerability analysis & generation (Complexity: 0.78).
  - *Security Check:* Hardcoded AWS Key detected and redacted to `[REDACTED_AWS_KEY]` before dispatch.
  - *Capability Match:* Requires high code accuracy and structured output.
- **Sentinel Decision:** **Routed to DeepSeek V3 / OpenAI GPT-4o-mini**. Offloads task from GPT-4o, cutting cost by 92% while maintaining 99.4% patch accuracy.

### Case C: Q3 Financial Ledger Compliance Audit
- **Application:** FinServ Internal Audit Engine
- **Raw Prompt:** *"Analyze Q3 balance ledger for Client ACCT-9841 with SSN 948-20-1984. Calculate risk exposure."*
- **Sentinel Evaluation:**
  - *Intent:* High-risk financial reasoning & math (Complexity: 0.95).
  - *Security Check:* PII SSN and Account Number sanitized inline.
  - *Fidelity Expectation:* Maximum reasoning accuracy required; cost optimization secondary to quality.
- **Sentinel Decision:** **Routed to Anthropic Claude 3.5 Sonnet / DeepSeek R1**. Delivers maximum reasoning fidelity while logging full OpenTelemetry audit spans.

### Case D: Executive Board Deck Summarization
- **Application:** Executive Assistant Portal (CEO Identity)
- **Raw Prompt:** *"Summarize confidential M&A acquisition target document and list key valuation risks."*
- **Sentinel Evaluation:**
  - *User Scope:* CEO / Executive Role (Priority routing queue).
  - *Security Check:* Confidential tag enforced; data residency locked to US-East dedicated tenant. Zero-data-retention proxy enforced.
- **Sentinel Decision:** **Routed to Primary Frontier Reasoning Model (GPT-4o / Claude 3.5 Sonnet)** on dedicated zero-retention enterprise endpoint.

---

## 6. FAILURE HANDLING & RESILIENCY DECISIONS

When disruptions occur, Sentinel applies deterministic fallback logic rather than throwing unhandled errors to calling applications:

| Failure Scenario | Sentinel Decision Logic | Downstream Impact |
| :--- | :--- | :--- |
| **Primary Provider Outage (5xx Error)** | Instantly reroutes payload to pre-qualified secondary provider matching intent capabilities within 2.5ms. | **Zero Downtime:** Application receives valid response seamlessly. |
| **Rate Limit Exceeded (HTTP 429)** | Shifts request to alternative cloud host (e.g., Azure OpenAI → AWS Bedrock → DeepSeek) and logs endpoint backoff. | **Zero Latency Spike:** Avoids blocking application thread. |
| **Workspace Budget Exceeded** | Rejects request gracefully with `402 Payment Required` telemetry header and notifies FinOps admins. | **Cost Protection:** Prevents unauthorized financial overruns. |
| **Prompt Injection Detected** | Blocks payload execution, returns `400 Bad Request` safety flag, and logs incident to Security Audit. | **Data Defense:** Prevents model jailbreak and prompt leakage. |
| **Context Exceeds Model Window** | Applies token compression or routes to long-context model (e.g., 200k+ token window). | **Execution Continuity:** Prevents context truncation crashes. |
| **All Providers Degraded** | Serves closest semantic cache match or gracefully degraded response with explicit warning header. | **System Graceful Degradation:** Avoids hard application crash. |

---

## 7. FUTURE EVOLUTION & ADAPTIVE LEARNING

The Decision Intelligence Engine evolves continuously over time:

1. **Continuous Capability Scoring:** Dynamic model quality scores update automatically based on real-time execution feedback and benchmark evals.
2. **Predictive Latency Modeling:** Machine learning models predict provider latency spikes before they occur, proactively shifting traffic ahead of outages.
3. **Reinforcement Learning from FinOps Feedback:** The engine learns optimal cost/quality trade-off thresholds based on historical enterprise feedback.
4. **Automated Policy Recommendation:** Analyzes traffic patterns to recommend custom semantic caching rules and model tiering policies to administrators.

---

*This document defines the permanent intellectual property and competitive advantage of Sentinel AI.*
