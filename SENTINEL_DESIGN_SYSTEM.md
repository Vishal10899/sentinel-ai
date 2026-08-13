# SENTINEL ENTERPRISE DESIGN SYSTEM & VISUAL SPECIFICATION

**Document Version:** 1.0.0-DESIGN  
**Date:** August 1, 2026  
**Audience:** Design Systems Leads, Product Designers, UX Architects, Frontend Leads  
**Classification:** Enterprise Design System Specification (Internal / Restricted)

---

## SECTION 1: DESIGN PHILOSOPHY

Sentinel’s design language is built for high-stakes enterprise operation. It is modeled after the design discipline of Stripe Dashboard, Linear, Datadog, GitHub Enterprise, and Cloudflare Console.

### 1. Enterprise First
Sentinel prioritizes operational reliability, data clarity, and workflow efficiency over consumer novelty. Every element exists to assist engineers, security officers, and financial managers in governing mission-critical AI traffic.

### 2. Trust Before Beauty
Visual aesthetics must never compromise data integrity or operational legibility. A visually pleasing interface that obscures telemetry, delays error recognition, or creates ambiguous status indicators is a failed interface.

### 3. High Information Density
Enterprise operators process vast amounts of telemetry data. Sentinel avoids artificial whitespace padding and oversized consumer elements, delivering high-density, highly readable data layouts that minimize scrolling.

### 4. Progressive Disclosure
Primary status metrics and actionable alerts are exposed immediately. Granular payload definitions, raw OpenTelemetry JSON traces, and mathematical decision scores remain accessible on demand via drawers, tabs, or contextual overlays.

### 5. Explainability
No automated decision, cost optimization, or security block is presented as a black box. Every action includes a human-readable explanation rationale (`x-sentinel-routed-rationale`).

### 6. Calm Interface
Operational environments demand a visually calm backdrop. Sentinel employs dark obsidian tones, subtle slate borders, and muted visual elements so that active alerts and status anomalies stand out unmistakably.

### 7. Fast Decision Making
Interfaces are optimized for rapid cognition. Operators must be able to diagnose provider health, verify PII redaction, or assess budget utilization within 3 seconds of viewing any screen.

### 8. Zero Visual Noise
Decorative illustrations, non-functional background gradients, floating ambient particles, and novelty animations are strictly forbidden inside the operational control plane.

---

## SECTION 2: VISUAL PERSONALITY

### Emotional Identity
Sentinel must feel:
- **Intelligent:** Reflects precision algorithmic decision-making.
- **Precise:** Sharp alignment, exact numerical telemetry, structured typography.
- **Calm:** Deep obsidian palette that reduces visual fatigue during extended operations.
- **Professional:** Subdued tone suitable for CISO and Board of Directors presentations.
- **Premium:** Refined border treatments, micro-typography, and crisp contrast.
- **Trustworthy:** Deterministic, reliable, zero ambiguous UI states.
- **Secure:** Clear isolation boundaries, explicit permission indicators.
- **Modern:** Contemporary dark operational aesthetics without consumer gimmicks.

### What Sentinel Must NEVER Feel Like
- ❌ **Not Gaming UI:** No neon glow borders, futuristic cyber-hud frames, or sci-fi sound effects.
- ❌ **Not Crypto / Web3:** No flashy gradient coins, speculative trading charts, or dark-mode party visuals.
- ❌ **Not Generic Startup Landing Page:** No oversized 72pt hero copy, floating 3D icons, or decorative pricing cards.
- ❌ **Not AI-Generated Concept:** No Dribbble concept art with unreadable low-contrast text or fake floating windows.
- ❌ **Not Glassmorphism Overload:** No heavy backdrop blurs that obscure underlying telemetry text or decrease rendering performance.
- ❌ **Not Neon Cyberpunk:** No electric magenta/cyan gradients that cause visual eye strain.

---

## SECTION 3: LAYOUT SYSTEM

### Grid & Containers
- **Base Grid Unit:** 4px baseline grid (all spacing, padding, margins, and heights are multiples of 4px: 4, 8, 12, 16, 24, 32, 48, 64).
- **Max Content Container Width:** 1440px for standard operational dashboards; 100% fluid width for dense telemetry grids (e.g., Trace Inspector).
- **Sidebar Fixed Width:** Expanded: 240px | Collapsed (Icons Only): 64px.

### Spacing Scale
- `space-xs`: 4px (Tight element inline grouping)
- `space-sm`: 8px (Component internal padding / button gaps)
- `space-md`: 16px (Standard card padding / grid gaps)
- `space-lg`: 24px (Section separation / panel gaps)
- `space-xl`: 32px (Major layout module separation)

### Responsive Breakpoints
- `Mobile` (< 768px): Single-column view; read-only telemetry summary (administrative actions blocked).
- `Tablet / Laptop` (768px – 1279px): Collapsed sidebar default; 2-column grid.
- `Desktop` (1280px – 1919px): Standard 240px sidebar; 3-column or 4-column metric grid.
- `Ultra-Wide` (≥ 1920px): Full fluid telemetry layout with sticky right-side inspection drawer.

---

## SECTION 4: TYPOGRAPHY SYSTEM

Sentinel uses a dual-font system: **Inter** (or system UI sans-serif) for general interface text and **JetBrains Mono** (or UI monospace) for code, tokens, trace IDs, and numeric metrics.

| Category | Scale / Size | Weight | Line Height | Font Family | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Display** | 24px (1.5rem) | 700 (Bold) | 1.2 | Sans-Serif | Top-level Cockpit Titles |
| **Heading 1** | 20px (1.25rem) | 700 (Bold) | 1.25 | Sans-Serif | Page Headers, Major Section Titles |
| **Heading 2** | 16px (1.0rem) | 600 (SemiBold) | 1.3 | Sans-Serif | Panel & Card Titles |
| **Subheading**| 14px (0.875rem)| 600 (SemiBold) | 1.4 | Sans-Serif | Component Labels, Table Headers |
| **Body Standard**| 13px (0.8125rem)| 400 (Regular) | 1.5 | Sans-Serif | Descriptive Text, Form Field Labels |
| **Body Small** | 12px (0.75rem) | 400 (Regular) | 1.4 | Sans-Serif | Secondary Metadata, Helper Text |
| **Caption** | 11px (0.6875rem)| 600 (SemiBold) | 1.3 | Sans-Serif (Caps)| Badges, Table Column Headers |
| **Code / Token**| 12px (0.75rem) | 500 (Medium) | 1.4 | Monospace | API Keys, Trace IDs, Payloads |
| **Numeric Metrics**| 24px–32px | 700 (Bold) | 1.1 | Monospace | Spend ($), Latency (ms), Throughput |

---

## SECTION 5: SEMANTIC COLOR SYSTEM

Sentinel strictly enforces a **semantic-only color system**. Every color assignment communicates explicit system state. Decorative or random colors are forbidden.

### Core Semantic Tokens

- **Primary Action (Sentinel Blue/Cyan):** Interactive buttons, active tabs, primary focus rings.
- **Success / Healthy (Emerald):** System active, 100% provider uptime, DLP pass, budget within limits.
- **Warning / Degraded (Amber/Orange):** High latency, budget at 80% threshold, provider failover active.
- **Danger / Critical (Rose/Red):** Provider outage (5xx), PII breach attempt blocked, budget cap exceeded (402).
- **Information / Telemetry (Purple):** Intent classification, vector cache hit indicator, OpenTelemetry trace spans.
- **Neutral Surface / Text (Obsidian & Slate):**
  - Base Background: `#030712` (Obsidian)
  - Surface Card Background: `#0B0F19` (Deep Slate)
  - Border Primary: `#1E293B` (Muted Slate)
  - Text Primary: `#F8FAFC` (High-contrast white)
  - Text Secondary: `#94A3B8` (Muted slate text)

---

## SECTION 6: ELEVATION & DEPTH SYSTEM

Sentinel uses a subtle, zero-blur 3-tier elevation system based on border contrast and surface shading rather than heavy drop shadows:

- **Level 0 (Canvas Base):** `#030712` background.
- **Level 1 (Card & Grid Surface):** `#0B0F19` background with 1px border (`#1E293B`).
- **Level 2 (Hover & Elevated Panel):** `#111827` background with 1px border (`#334155`).
- **Level 3 (Modal Dialogs & Drawers):** `#0F172A` background with 1px border (`#475569`) and subtle 16px backdrop dimming.

---

## SECTION 7: COMPONENT PHILOSOPHY

- **Buttons:** Crisp, 6px border radius, high-contrast text. Maximum 1 primary button per view.
- **Tables:** Dense rows (36px height), monospace alignment for numbers, sticky headers, inline status chips.
- **Status Chips:** Small, pill-shaped tags with explicit semantic color dot and text label (`● HEALTHY`, `● DEGRADED`).
- **Metrics Cards:** Large monospace numeric values paired with micro trend indicators (+12% vs last week) and clear unit labels ($ / ms / req).
- **Drawers & Modals:** Slide-out right drawers preferred over center modals for inspecting trace spans and payload JSON, preserving underlying dashboard context.

---

## SECTION 8: MOTION & ANIMATION SYSTEM

Motion in Sentinel exists solely to provide spatial feedback. Unnecessary visual decorative animations are disabled.

- **Fast Micro-Interactions (100ms – 150ms):** Button press, hover state, checkbox toggle.
- **Panel / Drawer Transitions (200ms ease-out):** Slide-out inspection drawer, accordion expansion.
- **System Telemetry Updates:** Instant numerical update; no count-up number roll animations that delay data reading.
- **Reduced Motion Support:** Respects `prefers-reduced-motion` OS setting by converting transitions to instant state cuts.

---

## SECTION 9: DATA VISUALIZATION RULES

1. **Line & Area Charts:** Used exclusively for continuous telemetry metrics (Latency over time, Request Throughput/sec, Daily Cost Spend).
2. **Monochrome + 1 Accent Color:** Charts use a single primary line color with a faint 5% opacity area fill to reduce visual clutter.
3. **No Decorative Gradients:** Chart fills must never use heavy multi-color rainbow gradients.
4. **Interactive Crosshairs:** Hovering displays precise monospace timestamp, exact value, and provider breakdown tooltip.

---

## SECTION 10: ICONOGRAPHY SYSTEM

- **Library:** Lucide Icons (or standardized enterprise SVG icon set).
- **Stroke Width:** Uniform 1.75px line stroke across all icons.
- **Sizing Standards:** Small: 14px | Standard: 16px | Large: 20px.
- **Usage:** Icons must always accompany descriptive text labels in navigation and action buttons. Icons are never used standalone without tooltips.

---

## SECTION 11: SYSTEM STATES

- **Empty States:** Clear icon, single-sentence explanation, and primary action button (e.g., *"No Virtual API Keys Found. Generate your first virtual key to begin routing."*).
- **Loading States:** Subtle pulse skeletons matching exact component dimensions. No spinning wheel overlays that block the whole screen.
- **Error States:** Explicit red border highlight, error code, human-readable cause, and "Retry Action" button.

---

## SECTION 12: ACCESSIBILITY (WCAG 2.1 AA MANDATE)

- **Contrast Ratios:** Text to background contrast ratio strictly ≥ 4.5:1 for standard text; ≥ 3:1 for large display text.
- **Keyboard Navigation:** 100% of actions accessible via `Tab`, `Enter`, `Space`, and `Esc`. Visible 2px blue focus ring on all active elements.
- **Screen Reader Support:** All interactive components include explicit `aria-label`, `aria-expanded`, and `role` attributes.

---

## SECTION 13: ENTERPRISE DESIGN RULES

1. **Maximum Border Radius:** 8px max for cards and modals; 6px for buttons and inputs; 4px for tags. Round "bubble" UI is forbidden.
2. **Maximum Colors Per View:** 1 Neutral + 1 Primary Action + Max 2 Semantic Status Colors on a single screen.
3. **No Decorative Background Patterns:** Ambient glow circles, floating particle meshes, and diagonal stripes are strictly banned inside operational screens.
4. **Monospace for Data:** All numbers, IP addresses, dates, timestamps, trace IDs, keys, and code snippets must render in monospace font.

---

## SECTION 14: DESIGN ANTI-PATTERNS (WHAT SENTINEL NEVER DOES)

- ❌ **No Dribbble Concept UI:** No floating un-bordered cards with low-contrast gray text on dark gray backgrounds.
- ❌ **No Marketing Gradients:** No rainbow gradient text headers or glowing animated buttons inside operational dashboards.
- ❌ **No Fake Count-Up Animations:** Numbers render instantly; operators must not wait 2 seconds for a dollar metric to stop rolling.
- ❌ **No Full-Screen Loading Spinners:** Skeleton loaders retain UI context during data fetches.

---

## SECTION 15: PRE-FLIGHT DESIGN CHECKLIST

Before any page or component is approved for engineering implementation, it must satisfy all 8 checks:

```
[ ] 1. Does the interface explain its primary metric/status within 3 seconds?
[ ] 2. Are all colors strictly semantic (Primary, Success, Warning, Danger, Info, Neutral)?
[ ] 3. Are all numeric metrics, timestamps, and keys rendered in monospace typography?
[ ] 4. Is the layout density appropriate for enterprise monitoring (no excessive whitespace)?
[ ] 5. Does the view provide a clear recovery path for error states?
[ ] 6. Is the interface fully usable via keyboard navigation (Tab / Focus rings verified)?
[ ] 7. Are progressive disclosure drawers used for raw JSON payloads instead of cluttering the main grid?
[ ] 8. Does the design adhere strictly to the 8px max border radius and dark obsidian theme?
```

---

*This document permanently freezes the Enterprise Design System specifications for Sentinel AI.*
