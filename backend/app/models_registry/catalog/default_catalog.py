"""Initial static model metadata; replace this source with settings or persistence later."""

from decimal import Decimal

from app.models_registry.schemas import ModelMetadata, ProviderMetadata


# Provider identifiers align with the existing provider framework where available.
DEFAULT_PROVIDERS: tuple[ProviderMetadata, ...] = (
    ProviderMetadata(provider_id="openai", provider_name="OpenAI"),
    ProviderMetadata(provider_id="gemini", provider_name="Google"),
    ProviderMetadata(provider_id="anthropic", provider_name="Anthropic"),
    ProviderMetadata(provider_id="ollama", provider_name="Ollama"),
)


# Prices are USD per 1K text tokens. Latency is an initial operational estimate,
# not an SLA; deployment configuration can replace these records in the future.
DEFAULT_MODELS: tuple[ModelMetadata, ...] = (
    ModelMetadata(
        provider_id="openai", provider_name="OpenAI", model_id="gpt-5",
        display_name="GPT-5", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.00125"), cost_per_1k_output_tokens=Decimal("0.010"),
        average_latency_ms=900, priority=10, context_window=400_000,
    ),
    ModelMetadata(
        provider_id="openai", provider_name="OpenAI", model_id="gpt-4.1",
        display_name="GPT-4.1", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.002"), cost_per_1k_output_tokens=Decimal("0.008"),
        average_latency_ms=700, priority=20, context_window=1_000_000,
    ),
    ModelMetadata(
        provider_id="openai", provider_name="OpenAI", model_id="gpt-4o-mini",
        display_name="GPT-4o mini", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.00015"), cost_per_1k_output_tokens=Decimal("0.00060"),
        average_latency_ms=350, priority=30, context_window=128_000,
    ),
    ModelMetadata(
        provider_id="gemini", provider_name="Google", model_id="gemini-2.5-pro",
        display_name="Gemini 2.5 Pro", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.00125"), cost_per_1k_output_tokens=Decimal("0.010"),
        average_latency_ms=1_100, priority=20, context_window=1_000_000,
    ),
    ModelMetadata(
        provider_id="gemini", provider_name="Google", model_id="gemini-2.5-flash",
        display_name="Gemini 2.5 Flash", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.00030"), cost_per_1k_output_tokens=Decimal("0.00250"),
        average_latency_ms=450, priority=30, context_window=1_000_000,
    ),
    ModelMetadata(
        provider_id="anthropic", provider_name="Anthropic", model_id="claude-sonnet-4",
        display_name="Claude Sonnet", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
        cost_per_1k_input_tokens=Decimal("0.003"), cost_per_1k_output_tokens=Decimal("0.015"),
        average_latency_ms=850, priority=20, context_window=200_000,
    ),
    ModelMetadata(
    provider_id="ollama",
    provider_name="Ollama",
    model_id="llama3.2",
    display_name="Llama 3.2",
    capabilities=frozenset({
        "chat",
        "summarization",
        "translation",
        "classification",
        "code_generation",
    }),
    cost_per_1k_input_tokens=Decimal("0"),
    cost_per_1k_output_tokens=Decimal("0"),
    average_latency_ms=700,
    priority=40,
    context_window=128_000,
),
    # ModelMetadata(
    #     provider_id="ollama", provider_name="Ollama", model_id="mistral",
    #     display_name="Mistral", capabilities=frozenset({"chat", "summarization", "translation", "classification", "code_generation"}),
    #     cost_per_1k_input_tokens=Decimal("0"), cost_per_1k_output_tokens=Decimal("0"),
    #     average_latency_ms=700, priority=50, context_window=32_000,
    # ),
)
