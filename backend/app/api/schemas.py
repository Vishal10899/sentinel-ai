"""Request and response schemas for the public REST API."""

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.routing.types import TaskCategory


class ProviderResponse(BaseModel):
    provider_id: str
    provider_name: str
    enabled: bool
    adapter_registered: bool
    status: str | None = None
    configured_model: str | None = None


class ModelResponse(BaseModel):
    provider_id: str
    provider_name: str
    model_id: str
    display_name: str
    capabilities: list[str]
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal
    average_latency_ms: int
    priority: int
    context_window: int
    enabled: bool


class RouteRequest(BaseModel):
    task_category: TaskCategory = Field(description="Capability required for the workload.")
    strategy: str = Field(default="balanced", pattern="^(balanced|cheapest|fastest)$")
    provider_ids: list[str] | None = Field(
        default=None,
        description="Optional registered-provider allowlist.",
    )


class RouteResponse(BaseModel):
    provider_id: str
    model_id: str
    task_category: TaskCategory
    strategy: str
    estimated_latency_ms: int
    cost_per_1k_input_tokens: Decimal
    cost_per_1k_output_tokens: Decimal


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


class CostCompareResponse(BaseModel):
    estimates: list[CostEstimateResponse]
    cheapest: CostEstimateResponse
    most_expensive: CostEstimateResponse
    savings_amount_usd: Decimal
    savings_percentage: Decimal


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: dict[str, str]


class PlaygroundRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=32_000)
    task_category: TaskCategory = TaskCategory.CHAT
    strategy: str = Field(default="balanced", pattern="^(balanced|cheapest|fastest)$")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=250, ge=0)


class ProviderConfigRequest(BaseModel):
    api_key: str | None = Field(default=None, max_length=500)
    model: str | None = Field(default=None, max_length=200)
    enabled: bool = True
