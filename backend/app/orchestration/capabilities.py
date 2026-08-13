from app.orchestration.models import ModelCapability


class CapabilityEngine:
    """Catalog Model Capability Engine."""

    def __init__(self) -> None:
        self._capabilities: dict[tuple[str, str], ModelCapability] = {}
        self._seed_default_capabilities()

    def _seed_default_capabilities(self) -> None:
        """Seed catalog models with comprehensive Phase 6 capability profiles."""
        models = [
            # --- Local Open-Source Models (Ollama) ---
            ModelCapability(
                "ollama", "llama3.2", category="chat", supports_chat=True, context_window=128000,
                supports_streaming=True, supports_vision=False, supports_tools=True, supports_reasoning=False,
                supports_json_mode=True, local_execution=True, quality_score=0.80, reasoning_score=0.76,
                coding_score=0.82, creativity_score=0.78, factual_accuracy_score=0.78, cost_score=1.00,
                latency_score=0.94, privacy_score=1.00, reliability_score=0.99
            ),
            ModelCapability(
                "ollama", "llama3.1:8b", category="chat", supports_chat=True, context_window=128000,
                supports_streaming=True, supports_vision=False, supports_tools=True, supports_reasoning=False,
                supports_json_mode=True, local_execution=True, quality_score=0.78, reasoning_score=0.75,
                coding_score=0.80, creativity_score=0.76, factual_accuracy_score=0.76, cost_score=1.00,
                latency_score=0.92, privacy_score=1.00, reliability_score=0.99
            ),
            ModelCapability(
                "ollama", "mistral", category="chat", supports_chat=True, context_window=32000,
                supports_streaming=True, supports_vision=False, supports_tools=True, supports_reasoning=False,
                supports_json_mode=True, local_execution=True, quality_score=0.78, reasoning_score=0.74,
                coding_score=0.78, creativity_score=0.80, factual_accuracy_score=0.76, cost_score=1.00,
                latency_score=0.93, privacy_score=1.00, reliability_score=0.99
            ),
            ModelCapability(
                "ollama", "deepseek-r1", category="reasoning", supports_chat=True, context_window=64000,
                supports_streaming=True, supports_vision=False, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=True, quality_score=0.88, reasoning_score=0.92,
                coding_score=0.88, creativity_score=0.70, factual_accuracy_score=0.86, cost_score=1.00,
                latency_score=0.85, privacy_score=1.00, reliability_score=0.98
            ),

            # --- Gemini Models ---
            ModelCapability(
                "gemini", "gemini-2.0-flash", category="chat", supports_chat=True, context_window=1000000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.92, reasoning_score=0.90,
                coding_score=0.90, creativity_score=0.88, factual_accuracy_score=0.92, cost_score=0.96,
                latency_score=0.98, privacy_score=0.85, reliability_score=0.995
            ),
            ModelCapability(
                "gemini", "gemini-2.5-flash", category="chat", supports_chat=True, context_window=1000000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.88, reasoning_score=0.86,
                coding_score=0.86, creativity_score=0.85, factual_accuracy_score=0.88, cost_score=0.92,
                latency_score=0.94, privacy_score=0.85, reliability_score=0.99
            ),
            ModelCapability(
                "gemini", "gemini-1.5-pro", category="chat", supports_chat=True, context_window=1000000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.94, reasoning_score=0.94,
                coding_score=0.92, creativity_score=0.90, factual_accuracy_score=0.94, cost_score=0.75,
                latency_score=0.82, privacy_score=0.85, reliability_score=0.99
            ),

            # --- OpenAI Models ---
            ModelCapability(
                "openai", "gpt-4o-mini", category="chat", supports_chat=True, context_window=128000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=False,
                supports_json_mode=True, local_execution=False, quality_score=0.84, reasoning_score=0.80,
                coding_score=0.82, creativity_score=0.84, factual_accuracy_score=0.85, cost_score=0.95,
                latency_score=0.95, privacy_score=0.80, reliability_score=0.99
            ),
            ModelCapability(
                "openai", "gpt-4o", category="chat", supports_chat=True, context_window=128000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.95, reasoning_score=0.95,
                coding_score=0.94, creativity_score=0.92, factual_accuracy_score=0.95, cost_score=0.70,
                latency_score=0.86, privacy_score=0.80, reliability_score=0.995
            ),
            ModelCapability(
                "openai", "gpt-5", category="chat", supports_chat=True, context_window=400000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.98, reasoning_score=0.98,
                coding_score=0.97, creativity_score=0.95, factual_accuracy_score=0.97, cost_score=0.60,
                latency_score=0.80, privacy_score=0.80, reliability_score=0.999
            ),

            # --- Anthropic Models ---
            ModelCapability(
                "anthropic", "claude-3-5-sonnet", category="chat", supports_chat=True, context_window=200000,
                supports_streaming=True, supports_vision=True, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.96, reasoning_score=0.96,
                coding_score=0.97, creativity_score=0.94, factual_accuracy_score=0.95, cost_score=0.65,
                latency_score=0.82, privacy_score=0.85, reliability_score=0.99
            ),

            # --- OpenRouter / DeepSeek Models ---
            ModelCapability(
                "openrouter", "deepseek-r1", category="chat", supports_chat=True, context_window=64000,
                supports_streaming=True, supports_vision=False, supports_tools=True, supports_reasoning=True,
                supports_json_mode=True, local_execution=False, quality_score=0.94, reasoning_score=0.96,
                coding_score=0.95, creativity_score=0.82, factual_accuracy_score=0.92, cost_score=0.98,
                latency_score=0.88, privacy_score=0.80, reliability_score=0.98
            ),

            # --- Embedding Models ---
            ModelCapability(
                "gemini", "text-embedding-004", category="embedding", supports_chat=False, context_window=2048,
                supports_streaming=False, supports_vision=False, supports_tools=False, supports_embeddings=True,
                quality_score=0.0, cost_score=0.0, latency_score=0.0
            ),
            ModelCapability(
                "openai", "text-embedding-3-large", category="embedding", supports_chat=False, context_window=8191,
                supports_streaming=False, supports_vision=False, supports_tools=False, supports_embeddings=True,
                quality_score=0.0, cost_score=0.0, latency_score=0.0
            ),
        ]
        for m in models:
            self._capabilities[(m.provider_id, m.model_id)] = m

    def get_capability(self, provider_id: str, model_id: str) -> ModelCapability:
        key = (provider_id, model_id)
        if key in self._capabilities:
            return self._capabilities[key]
        
        is_embedding = "embedding" in model_id.lower() or "embed" in model_id.lower()
        is_ollama = provider_id.lower() == "ollama"
        return ModelCapability(
            provider_id=provider_id,
            model_id=model_id,
            category="embedding" if is_embedding else "chat",
            supports_chat=not is_embedding,
            local_execution=is_ollama,
            cost_score=1.00 if is_ollama else 0.80,
            privacy_score=1.00 if is_ollama else 0.80,
        )

    def list_capabilities(self) -> list[ModelCapability]:
        return list(self._capabilities.values())


capability_engine = CapabilityEngine()
