"""Request and response schemas for the public REST API."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.routing.types import TaskCategory

from datetime import datetime



class ProviderResponse(BaseModel):
    provider_id: str
    provider_name: str
    enabled: bool
    adapter_registered: bool
    status: str | None = None
    configured_model: str | None = None
    api_key_masked: str | None = None
    base_url: str | None = None
    organization_id: str | None = None
    timeout_seconds: int = 30
    retry_count: int = 3
    rate_limit_rpm: int = 600
    rate_limit_tpm: int = 100000
    priority: int = 10
    cost_multiplier: float = 1.0
    primary_provider_id: str | None = None
    secondary_provider_id: str | None = None
    auto_failover: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    supports_function_calling: bool = True
    supports_embeddings: bool = True
    supports_image_generation: bool = False
    supports_moderation: bool = False
    last_latency_ms: int = 0
    last_health_check: str | None = None
    last_failure: str | None = None
    failure_count: int = 0
    consecutive_failures: int = 0


class ModelResponse(BaseModel):
    provider_id: str
    provider_name: str
    model_id: str
    display_name: str
    category: str = "chat"
    capabilities: list[str]
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    average_latency_ms: int
    priority: int
    context_window: int
    max_output_tokens: int = 4096
    supports_streaming: bool = True
    supports_function_calling: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    reasoning_score: float = 0.0
    speed_score: float = 0.0
    quality_score: float = 0.0
    enabled: bool = True
    deprecated: bool = False


class CandidateScoreResponse(BaseModel):
    provider_id: str
    model_id: str
    overall_score: float
    rank: int
    cost_per_1k_tokens: Decimal
    latency_ms: int
    quality_score: float
    reasoning_score: float
    status: str
    reason: str


class RoutingExplanationResponse(BaseModel):
    selected_provider_id: str
    selected_model_id: str
    strategy: str
    primary_reason: str
    ranked_candidates: list[CandidateScoreResponse]
    failover_triggered: bool = False
    circuit_breaker_bypassed: list[str] = []


class RouteRequest(BaseModel):
    task_category: TaskCategory = Field(description="Capability required for the workload.")
    strategy: str = Field(
        default="balanced",
        pattern="^(balanced|cheapest|fastest|highest_quality|reasoning_optimized|vision_optimized|embedding_optimized|image_generation_optimized|custom_weighted)$",
    )
    provider_ids: list[str] | None = Field(
        default=None,
        description="Optional registered-provider allowlist.",
    )
    weights: dict[str, float] | None = Field(
        default=None,
        description="Custom strategy weights: cost, latency, quality, reasoning.",
    )
    prompt_tokens: int = Field(default=0, ge=0)
    max_completion_tokens: int = Field(default=250, ge=0)
    workspace_id: str | None = None


class RouteResponse(BaseModel):
    provider_id: str
    model_id: str
    task_category: TaskCategory
    strategy: str
    estimated_latency_ms: int
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    estimated_cost_usd: Decimal = Decimal("0.0")
    failover_triggered: bool = False
    circuit_breaker_bypassed: list[str] = []
    explanation: RoutingExplanationResponse | None = None


class CostRequest(BaseModel):
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class CostEstimateResponse(BaseModel):
    provider_id: str
    model_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Decimal
    daily_forecast_usd: Decimal = Decimal("0.0")
    monthly_forecast_usd: Decimal = Decimal("0.0")


class ModelReference(BaseModel):
    provider_id: str = Field(min_length=1)
    model_id: str = Field(min_length=1)


class CostCompareRequest(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    models: list[ModelReference] | None = Field(
        default=None,
        description="Models to compare. Omit to compare every enabled catalog model.",
    )

    @model_validator(mode="after")
    def validate_models(self) -> "CostCompareRequest":
        if self.models is not None and not self.models:
            raise ValueError("models must contain at least one model when supplied")
        return self


class CostSavingsRecommendationResponse(BaseModel):
    current_model: str
    recommended_model: str
    savings_percentage: Decimal
    savings_amount_usd: Decimal
    suggestion_text: str


class CostCompareResponse(BaseModel):
    estimates: list[CostEstimateResponse]
    cheapest: CostEstimateResponse
    most_expensive: CostEstimateResponse
    savings_amount_usd: Decimal
    savings_percentage: Decimal
    recommendations: list[CostSavingsRecommendationResponse] = []


class BudgetStatusResponse(BaseModel):
    workspace_id: str
    monthly_budget_usd: Decimal
    current_spend_usd: Decimal
    percentage_used: Decimal
    warning_status: str  # "normal", "warning_80", "warning_90", "exceeded"
    hard_stop_triggered: bool = False


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    role: str | None = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str


class RoleInfoResponse(BaseModel):
    id: str
    name: str
    is_builtin: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserResponse
    organization: OrganizationResponse | None = None
    workspace: WorkspaceResponse | None = None
    role: RoleInfoResponse | None = None
    permissions: list[str] = Field(default_factory=list)



class PlaygroundRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=32_000)
    task_category: TaskCategory = TaskCategory.CHAT
    strategy: str = Field(
        default="balanced",
        pattern="^(balanced|cheapest|fastest|highest_quality|reasoning_optimized|vision_optimized|embedding_optimized|image_generation_optimized|custom_weighted)$",
    )
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=250, ge=0)


class ProviderConfigRequest(BaseModel):
    api_key: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=200)
    enabled: bool = True
    base_url: str | None = Field(default=None, max_length=300)
    organization_id: str | None = Field(default=None, max_length=100)
    timeout_seconds: int | None = Field(default=None, ge=1, le=300)
    retry_count: int | None = Field(default=None, ge=0, le=10)
    rate_limit_rpm: int | None = Field(default=None, ge=1)
    rate_limit_tpm: int | None = Field(default=None, ge=1)
    priority: int | None = Field(default=None, ge=1)
    cost_multiplier: float | None = Field(default=None, ge=0.0)
    primary_provider_id: str | None = None
    secondary_provider_id: str | None = None
    auto_failover: bool | None = None
    supports_streaming: bool | None = None
    supports_vision: bool | None = None
    supports_audio: bool | None = None
    supports_function_calling: bool | None = None
    supports_embeddings: bool | None = None
    supports_image_generation: bool | None = None
    supports_moderation: bool | None = None


class ProviderCreateRequest(BaseModel):
    provider_id: str = Field(min_length=2, max_length=50, pattern="^[a-zA-Z0-9_-]+$")
    provider_name: str | None = Field(default=None, max_length=100)
    api_key: str | None = Field(default=None, max_length=500)
    base_url: str | None = Field(default=None, max_length=300)
    organization_id: str | None = Field(default=None, max_length=100)
    default_model: str | None = Field(default=None, max_length=100)
    timeout_seconds: int = 30
    retry_count: int = 3
    rate_limit_rpm: int = 600
    rate_limit_tpm: int = 100000
    priority: int = 10
    cost_multiplier: float = 1.0
    primary_provider_id: str | None = None
    secondary_provider_id: str | None = None
    auto_failover: bool = True
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_audio: bool = False
    supports_function_calling: bool = True
    supports_embeddings: bool = True
    supports_image_generation: bool = False
    supports_moderation: bool = False


class ProviderFailoverRequest(BaseModel):
    primary_provider_id: str | None = None
    secondary_provider_id: str | None = None
    auto_failover: bool = True


class ProviderTestResponse(BaseModel):
    provider_id: str
    valid: bool
    status: str
    message: str
    latency_ms: int
 

class CreateConversationRequest(BaseModel):
    title: str = Field(
        default="New Conversation",
        max_length=200,
    )


class UpdateConversationRequest(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    is_pinned: bool | None = None
    is_favorite: bool | None = None
    is_archived: bool | None = None
    tags: str | None = Field(default=None, max_length=500)
    summary: str | None = Field(default=None, max_length=1000)


class ConversationResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    is_pinned: bool = False
    is_favorite: bool = False
    is_archived: bool = False
    is_deleted: bool = False
    deleted_at: datetime | None = None
    share_token: str | None = None
    summary: str | None = None
    tags: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShareConversationResponse(BaseModel):
    conversation_id: str
    share_token: str
    share_url: str


class GenerateTitleResponse(BaseModel):
    conversation_id: str
    generated_title: str
    summary: str


class ImportConversationMessage(BaseModel):
    role: str
    content: str
    provider: str | None = None
    model: str | None = None


class ImportConversationRequest(BaseModel):
    title: str = Field(default="Imported Conversation", max_length=200)
    tags: str | None = None
    messages: list[ImportConversationMessage] = Field(default_factory=list)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    provider: str | None = None
    model: str | None = None
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    latency_ms: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
