from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class IntentResult:
    """Classified request intent metadata."""

    intent: str  # CODE_GENERATION, CODE_REVIEW, ARCHITECTURE, REASONING, CREATIVE_WRITING, TRANSLATION, LEGAL_DRAFTING, MEDICAL_EXPLANATION, MATHEMATICS, DATA_ANALYSIS, DEBUGGING, SUMMARIZATION, CLASSIFICATION, RESEARCH, CONVERSATION
    confidence: float  # 0.0 to 1.0
    required_capabilities: list[str] = field(default_factory=list)
    estimated_complexity: str = "MEDIUM"  # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    reasoning_depth: float = 0.5         # 0.0 to 1.0
    factual_accuracy_req: float = 0.5     # 0.0 to 1.0
    creativity_req: float = 0.5           # 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RequestProfile:
    """Multi-dimensional prompt workload profile (15 estimation dimensions)."""

    prompt_tokens: int
    context_tokens: int
    complexity: str = "MEDIUM"               # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    reasoning_depth: float = 0.5             # 0.0 to 1.0
    factual_accuracy: float = 0.5            # 0.0 to 1.0
    creativity: float = 0.5                  # 0.0 to 1.0
    latency_importance: float = 0.5          # 0.0 to 1.0
    cost_sensitivity: float = 0.5            # 0.0 to 1.0
    local_execution_suitability: float = 0.5 # 0.0 to 1.0
    privacy_sensitivity: float = 0.0         # 0.0 to 1.0 (source code, PII, secrets, keys)
    is_latency_sensitive: bool = False
    is_cost_sensitive: bool = False
    needs_streaming: bool = True
    needs_vision: bool = False
    needs_tools: bool = False
    needs_json: bool = False
    confidence_score: float = 0.90

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ModelCapability:
    """Comprehensive model capability profile (Phase 6 Metadata)."""

    provider_id: str
    model_id: str
    category: str = "chat"
    supports_chat: bool = True
    context_window: int = 128000
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_tools: bool = False
    supports_reasoning: bool = False
    supports_json_mode: bool = True
    supports_embeddings: bool = False
    local_execution: bool = False
    quality_score: float = 0.85          # 0.0 to 1.0
    reasoning_score: float = 0.80        # 0.0 to 1.0
    coding_score: float = 0.80           # 0.0 to 1.0
    creativity_score: float = 0.80       # 0.0 to 1.0
    factual_accuracy_score: float = 0.85 # 0.0 to 1.0
    cost_score: float = 0.80             # 0.0 to 1.0 (higher = cheaper/free)
    latency_score: float = 0.85          # 0.0 to 1.0 (higher = faster)
    privacy_score: float = 0.80          # 0.0 to 1.0 (1.0 for local/on-prem)
    reliability_score: float = 0.99

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateScore:
    provider_id: str
    model_id: str
    total_score: float
    reason: str


@dataclass
class PromptIntelligenceProfile:
    """Enterprise Prompt Intelligence Profile (Phase 1)."""

    intent: str = "CONVERSATION"
    goal: str = "General Assistance"
    complexity: str = "MEDIUM"              # VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
    reasoning_depth: float = 0.5            # 0.0 to 1.0
    creativity_req: float = 0.5             # 0.0 to 1.0
    accuracy_req: float = 0.5               # 0.0 to 1.0
    coding_pct: float = 0.0
    math_pct: float = 0.0
    architecture_pct: float = 0.0
    writing_pct: float = 0.0
    research_pct: float = 0.0
    vision_pct: float = 0.0
    image_gen_pct: float = 0.0
    translation_pct: float = 0.0
    summarization_pct: float = 0.0
    needs_json: bool = False
    needs_structured_output: bool = False
    needs_tools: bool = False
    needs_streaming: bool = True
    needs_long_context: bool = False
    has_conversation_dependency: bool = False
    privacy_sensitivity: float = 0.0        # 0.0 to 1.0
    pii_detected: bool = False
    security_risk: str = "LOW"             # LOW, MEDIUM, HIGH, CRITICAL
    latency_priority: float = 0.5         # 0.0 to 1.0
    cost_priority: float = 0.5            # 0.0 to 1.0
    quality_priority: float = 0.5          # 0.0 to 1.0
    freshness_required: bool = False
    language: str = "English"
    estimated_input_tokens: int = 10
    estimated_output_tokens: int = 150
    expected_runtime_ms: float = 250.0
    confidence: float = 0.90

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RoutingDecisionRecord:
    """Decision Memory Record for audits and self-learning (Phase 8)."""

    decision_id: str
    timestamp: float
    workspace_id: str
    prompt_profile: dict[str, Any]
    selected_provider: str
    selected_model: str
    alternative_models: list[dict[str, Any]]
    routing_score: float
    reason_for_selection: str
    estimated_cost_usd: float = 0.0
    actual_cost_usd: float = 0.0
    estimated_latency_ms: float = 0.0
    actual_latency_ms: float = 0.0
    execution_success: bool = True
    retries: int = 0
    failures: int = 0
    memory_engine_used: bool = False
    cache_hit: bool = False
    provider_health_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AdaptiveRoutingResult:
    """Explainable adaptive routing selection result."""

    selected_provider: str
    selected_model: str
    strategy_used: str
    intent_detected: str
    confidence: float
    explanation_text: str
    candidate_scores: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
