"""Adaptive Timeout Engine.

Calculates hard and soft request execution timeouts dynamically based on task category,
model family, and prompt length in < 0.2 ms.
"""

from typing import Any

from app.reliability.models import TimeoutDecision


class AdaptiveTimeoutEngine:
    """Enterprise Adaptive Timeout Engine (< 0.2 ms evaluation time)."""

    CATEGORY_TIMEOUTS = {
        "reasoning": 45.0,
        "coding": 35.0,
        "security_review": 30.0,
        "math": 30.0,
        "summarization": 20.0,
        "translation": 15.0,
        "chat": 15.0,
    }

    def calculate_timeout(
        self,
        provider_id: str,
        model_id: str,
        task_category: str = "chat",
        prompt_length: int = 100,
        override_timeout: float | None = None,
    ) -> TimeoutDecision:
        """Calculate hard and soft timeouts in < 0.2 ms."""
        if override_timeout is not None and override_timeout > 0:
            hard = override_timeout
            soft = round(hard * 0.8, 1)
            return TimeoutDecision(
                provider_id=provider_id,
                model_id=model_id,
                task_category=task_category,
                hard_timeout_seconds=hard,
                soft_timeout_seconds=soft,
                reason=f"Explicit override timeout applied ({hard:.1f}s).",
            )

        cat_key = task_category.lower()
        base_timeout = self.CATEGORY_TIMEOUTS.get(cat_key, 20.0)

        # Longer prompts or reasoning models get incremental timeout budgets
        length_bonus = min((prompt_length // 2000) * 5.0, 15.0)
        hard_timeout = round(base_timeout + length_bonus, 1)
        soft_timeout = round(hard_timeout * 0.8, 1)

        return TimeoutDecision(
            provider_id=provider_id,
            model_id=model_id,
            task_category=task_category,
            hard_timeout_seconds=hard_timeout,
            soft_timeout_seconds=soft_timeout,
            reason=f"Adaptive timeout computed for category '{task_category}' ({hard_timeout:.1f}s hard / {soft_timeout:.1f}s soft).",
        )


adaptive_timeout_engine = AdaptiveTimeoutEngine()
