# SENTINEL INFORMATION ARCHITECTURE & NAVIGATION SPECIFICATION

**Document Version:** 1.0.0-IA  
**Date:** August 1, 2026  
**Audience:** Information Architects, Principal Product Designers, UX Architects, Product Leadership  
**Classification:** Enterprise Design System & Information Architecture (Internal / Restricted)

---

## SECTION 1: GLOBAL NAVIGATION PHILOSOPHY

Sentinel's navigation is modeled after elite enterprise control planes (Azure Portal, Datadog, Cloudflare, Stripe Dashboard, GitHub Enterprise) rather than consumer SaaS applications.

### 1.1 Architectural Usability Principles
- **Role-Centric Spatial Hierarchy:** Information is grouped by domain responsibility (Gateway Operations, Security & Governance, Cost Analytics, Administration, End-User Workspace) rather than feature lists.
- **Role-Tailored Initial Entry Points:** A developer, a CISO, a FinOps manager, and an executive never see the same home landing dashboard. Upon login, Sentinel immediately renders a context-specific operational cockpit.
- **Maximum Depth 2 (Flat Architecture):** No item is nested deeper than two levels (`Category -> Sub-Page`). Every capability is reachable within two user clicks.
- **Contextual Cross-Linking:** Deep operational relationships allow users to jump fluidly between domains (e.g., from a cost anomaly in Analytics directly into a specific Trace span, then to the target Model catalog, then to the underlying DLP Security Policy).
- **Progressive Disclosure:** Primary metrics and status indicators are visible immediately; granular configuration parameters, trace raw payloads, and JSON schemas remain hidden behind secondary drawers or tab panels.

---

## SECTION 2: GLOBAL SIDEBAR STRUCTURE & TAXONOMY

The global sidebar represents the primary navigation spine of Sentinel. It is organized into 7 functional domains:

```
SENTINEL CONTROL PLANE
│
├── 📊 Cockpit (Role-Tailored Home)
│
├── ⚡ AI Gateway
│   ├── Overview & Traffic Status
│   ├── Provider Credentials
│   ├── Model Catalog & Capabilities
│   ├── Decision Intelligence Engine
│   ├── Virtual API Keys
│   └── API Playground & Debugger
│
├── 🛡️ Security & Governance
│   ├── Guardrails & DLP Redaction
│   ├── Policy Rules Engine
│   ├── What-If Policy Simulator
│   └── Immutable Audit Logs
│
├── 📈 Analytics & Telemetry
│   ├── Cost Intelligence & FinOps
│   ├── Usage & Token Analytics
│   ├── Distributed Tracing (Spans)
│   └── Provider Health Matrix
│
├── 💬 AI Workspace (Employee Portal)
│   ├── Chat Console
│   ├── Document Attachments
│   └── Prompt Template Library
│
├── ⚙️ Administration
│   ├── Organizations & Workspaces
│   ├── Users & Directory
│   ├── Teams & Departments
│   ├── RBAC Roles & Permissions
│   └── Enterprise Billing & Licenses
│
├── 🛠️ Developer & API
│   ├── Quickstart Guide
│   ├── SDK Integration Specs
│   └── OpenAPI / Swagger Reference
│
└── 🔒 Settings & System Status
```

### Rationale for Section Groupings

1. **Cockpit:** Role-specific operational home screen providing immediate domain awareness.
2. **AI Gateway:** High-frequency developer and platform engineering tools controlling request routing, keys, and model backends.
3. **Security & Governance:** Compliance, DLP redaction, policy rules, and audit logs dedicated to CISO and security team workflows.
4. **Analytics & Telemetry:** Observability, FinOps cost tracking, trace spans, and health metrics for infrastructure and finance leaders.
5. **AI Workspace:** Managed employee chat portal isolated from developer administrative controls to prevent operational confusion.
6. **Administration:** Tenant setup, user directory, team hierarchies, RBAC, and billing management.
7. **Developer & API:** Native integration documentation, SDK code snippets, and OpenAPI specifications.

---

## SECTION 3: PAGE HIERARCHY & SPECIFICATIONS

| Page ID | Page Name | Primary User | Secondary User | Inputs | Outputs | Primary Dependencies |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PG-01` | **Cockpit (Role Home)** | All Roles | N/A | Auth Context, User Role | Key Domain KPIs, Alerts | User Profile, RBAC Engine |
| `PG-02` | **Gateway Overview** | Platform Admin | SRE | Time Range Filter | Request Volume, Latency, Errors | Telemetry Engine |
| `PG-03` | **Provider Credentials** | Platform Admin | Dev Lead | API Keys, Endpoints | Encrypted Credentials, Health | Vault / KMS Engine |
| `PG-04` | **Model Catalog** | AI Admin | Platform Admin | Capability Flags, Prices | Qualified Model Matrix | Model Registry |
| `PG-05` | **Decision Engine** | AI Admin | CTO | Strategy Weightings | Intent & Routing Rationale | Decision Engine Core |
| `PG-06` | **Virtual API Keys** | Developer | Team Lead | Key Name, Budget Cap, TTL | Scoped Key String (`sk-snt-`) | Auth Hashing Service |
| `PG-07` | **Guardrails & DLP** | Security Admin | Compliance | Regex Rules, PII Toggles | Active Redaction Schema | DLP Engine |
| `PG-08` | **Policy Engine** | Security Admin | AI Admin | Governance Rules, Caps | Active Enforcement Policies | Rules Engine |
| `PG-09` | **Policy Simulator** | Security Admin | AI Admin | Draft Rule, Historical Data | Dry-Run Cost/Block Impact | Telemetry Archives |
| `PG-10` | **Audit Logs** | Security Admin | Auditor | Search Query, Date Range | Immutable Audit Stream, CSV | Audit Repository |
| `PG-11` | **Cost Intelligence** | Finance Manager | CTO | Workspace Filter, Date | Spend Attribution, Forecast | FinOps Engine |
| `PG-12` | **Distributed Tracing** | Developer | SRE | Trace ID, Correlation ID | Span Flamegraph, Headers | Trace Repository |
| `PG-13` | **Provider Health** | SRE | Platform Admin | Region Filter | Latency Histograms, 5xx Rates | Health Checker |
| `PG-14` | **AI Workspace Chat** | Employee | All Users | User Prompt, Document | Streamed AI Response, History | Gateway Proxy |

---

## SECTION 4: ACCESS CONTROL & PERMISSION MATRIX

| Page ID | Page Name | Owner | Plat Admin | AI Admin | Sec Admin | FinOps | Team Lead | Dev | Employee | Exec |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `PG-01` | **Cockpit** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |
| `PG-02` | **Gateway Overview** | 🟢 | 🟢 | 🟢 | 🔴 | 🟡 | 🟢 | 🟢 | 🔴 | 🟢 |
| `PG-03` | **Provider Credentials** | 🟢 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 |
| `PG-04` | **Model Catalog** | 🟢 | 🟢 | 🟢 | 🔴 | 🟡 | 🟢 | 🟢 | 🔴 | 🟢 |
| `PG-05` | **Decision Engine** | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🟢 |
| `PG-06` | **Virtual API Keys** | 🟢 | 🟢 | 🔴 | 🔴 | 🟡 | 🟢 | 🟢 | 🔴 | 🔴 |
| `PG-07` | **Guardrails & DLP** | 🟢 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🟢 |
| `PG-08` | **Policy Engine** | 🟢 | 🟢 | 🟢 | 🟢 | 🟡 | 🔴 | 🔴 | 🔴 | 🟢 |
| `PG-09` | **Policy Simulator** | 🟢 | 🟢 | 🟢 | 🟢 | 🟡 | 🔴 | 🔴 | 🔴 | 🔴 |
| `PG-10` | **Audit Logs** | 🟢 | 🟢 | 🔴 | 🟢 | 🟡 | 🔴 | 🔴 | 🔴 | 🟢 |
| `PG-11` | **Cost Intelligence** | 🟢 | 🟢 | 🟡 | 🔴 | 🟢 | 🟢 | 🟡 | 🔴 | 🟢 |
| `PG-12` | **Distributed Tracing** | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | 🔴 | 🔴 |
| `PG-13` | **Provider Health** | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🟢 | 🟢 | 🔴 | 🟢 |
| `PG-14` | **AI Workspace Chat** | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 |

*Legend: 🟢 Full Access | 🟡 Read-Only Access | 🔴 No Access*

---

## SECTION 5: CROSS-NAVIGATION & CONTEXTUAL FLOWS

Sentinel enforces seamless, context-preserving cross-navigation. Clicking an entity anywhere in the UI opens its associated detail view without losing current filter states.

```
Analytics Dashboard (Cost Anomaly Detected)
                   ↓ [Click Anomaly Node]
Distributed Trace Inspector (Inspect Span trace_snt_98401)
                   ↓ [Click Model Tag]
Model Catalog Entry (DeepSeek V3 Capabilities)
                   ↓ [Click Provider Status]
Provider Health Matrix (Azure Bedrock Regional Latency)
                   ↓ [Click Security Flag]
DLP Guardrail Policy (PII Redaction Schema)
                   ↓ [Click Audit ID]
Immutable Audit Log Record
```

---

## SECTION 6: ROLE-SPECIFIC DASHBOARD ENTRY POINTS

Upon authentication, Sentinel routes users directly to a role-customized Cockpit:

### 1. Executive Cockpit (CTO / VP Engineering / CISO)
- **Top Metrics:** Total Token Spend Saved ($), Overall System Availability (99.999%), Active Security Threats Blocked, ROI Ratio.
- **Primary Visuals:** High-level cost trend curve, multi-cloud provider health map, security compliance scorecard.

### 2. Platform Admin Cockpit
- **Top Metrics:** Active Throughput (req/sec), Gateway Overhead (ms), Connected Provider Status, Active Virtual Keys.
- **Primary Visuals:** Real-time request volume histogram, HTTP 5xx error rate alert feed, infrastructure quick actions.

### 3. Security Admin Cockpit
- **Top Metrics:** DLP Scans Completed, PII Redaction Count, Prompt Injections Blocked, Compliance Integrity Index.
- **Primary Visuals:** Live threat event stream, DLP category breakdown, recent high-risk audit events.

### 4. Finance Manager Cockpit
- **Top Metrics:** Current Month Spend vs Budget Cap, Projected End-of-Month Cost, Token Cost Savings %, Unattributed Spend.
- **Primary Visuals:** Department spend attribution chart, cost savings breakdown by semantic cache vs model tiering.

### 5. Developer Cockpit
- **Top Metrics:** Assigned Virtual Keys, Personal Request Count, Average Proxy Latency (ms), Error Rate %.
- **Primary Visuals:** Quickstart code snippets, recent personal request trace log, API playground launcher.

### 6. Employee AI Workspace Cockpit
- **Top Metrics:** Recent Conversations, Saved Prompt Templates, Model Selector Status.
- **Primary Visuals:** Clean chat input box, document upload drop zone, team prompt template gallery.

---

## SECTION 7: SEARCH & COMMAND PALETTE ARCHITECTURE

Sentinel incorporates a global search and command palette accessible via `Cmd + K` (macOS) or `Ctrl + K` (Windows):

### 1. Universal Entity Search
- Search by `Trace ID` (`trace_snt_...`), `Virtual Key Name`, `Provider Name`, `User Email`, `Policy ID`, or `Model Identifier`.

### 2. Quick Command Execution
- Type `> new key` to open Virtual Key creation drawer.
- Type `> simulate` to open Policy Simulator.
- Type `> export audit` to generate compliance export.

### 3. Contextual Navigation
- Direct jump to any sidebar page or workspace settings panel in under 3 keystrokes.

---

## SECTION 8: NOTIFICATION & ALERT ARCHITECTURE

Sentinel classifies notifications into 4 urgency tiers across 3 delivery channels (In-App Toast, Webhook/Slack, Email):

| Tier | Category | Trigger Event Example | Delivery Channel | Action Required |
| :--- | :--- | :--- | :--- | :--- |
| **P0: Critical** | **Provider Outage** | Primary LLM provider HTTP 5xx rate > 10% | In-App + PagerDuty/Slack | Auto-failover triggered; Admin review requested |
| **P1: High** | **Security Threat** | High-confidence prompt injection attempt blocked | In-App + Email + Webhook | Security Admin investigation |
| **P2: Medium**| **Budget Alert** | Virtual Key reaches 80% or 100% budget limit | In-App + Email | FinOps cap adjustment or approval |
| **P3: Low** | **System Info** | New model version added to catalog | In-App Notification Center | Information only |

---

## SECTION 9: PERMANENT NAVIGATION PRINCIPLES

1. **Maximum 2 Clicks to Any Feature:** No capability may be buried deeper than 2 clicks from the main navigation spine.
2. **Persistent Breadcrumb Navigation:** Every sub-page renders explicit breadcrumbs (`Security / Policies / Rule-984`) allowing single-click parent navigation.
3. **Preserved Workspace Context:** Switching between pages retains active workspace, date range, and tenant selection parameters.
4. **Responsive Desktop-First Design:** Optimized for high-density enterprise desktop screens (1440px+), with collapsing sidebar support for laptop displays (1024px+).

---

## SECTION 10: FUTURE EXPANSION PLATFORM

The global sidebar taxonomy is designed to accommodate future enterprise modules without structural redesign:

- **Future Module: Agents & Orchestration** → Placed directly under `AI Gateway / Agent Networks`
- **Future Module: Custom Fine-Tuning Jobs** → Placed directly under `AI Gateway / Fine-Tuning`
- **Future Module: Global Compliance Frameworks** → Placed directly under `Security & Governance / EU AI Act`

---

*This document permanently freezes the Information Architecture and Navigation Specifications of Sentinel AI.*
