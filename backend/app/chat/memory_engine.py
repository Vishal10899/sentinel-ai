"""Enterprise Memory & Context Management Layer.

Provides Short-Term Memory, Long-Term Memory, Context Window Trimming,
Context Compression Hooks, and Semantic Cache references for AI Workspace conversations.
"""

from dataclasses import dataclass, field
import datetime
from typing import Any
import uuid

from app.cache.semantic import semantic_cache


@dataclass(frozen=True, slots=True)
class MemoryContext:
    """Bounded conversation memory context snapshot."""

    conversation_id: str
    short_term_messages: list[dict[str, Any]]
    long_term_references: list[dict[str, Any]]
    total_context_tokens: int
    is_compressed: bool
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "short_term_messages": self.short_term_messages,
            "long_term_references": self.long_term_references,
            "total_context_tokens": self.total_context_tokens,
            "is_compressed": self.is_compressed,
            "summary": self.summary,
        }


class MemoryEngine:
    """Enterprise Conversation Memory Engine."""

    def __init__(self, default_token_limit: int = 4000) -> None:
        self.default_token_limit = default_token_limit

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count (approx 4 chars per token)."""
        if not text:
            return 0
        return max(len(text) // 4, 1)

    def trim_context(self, messages: list[dict[str, Any]], max_tokens: int = 4000) -> tuple[list[dict[str, Any]], int]:
        """Automatically trim conversation messages to stay within max_tokens context window."""
        if not messages:
            return [], 0

        # Separate system messages (must be preserved)
        system_msgs = [m for m in messages if m.get("role") == "system"]
        other_msgs = [m for m in messages if m.get("role") != "system"]

        system_tokens = sum(self.estimate_tokens(m.get("content", "")) for m in system_msgs)
        budget = max_tokens - system_tokens

        trimmed_others: list[dict[str, Any]] = []
        current_tokens = 0

        # Preserve most recent messages backwards
        for m in reversed(other_msgs):
            t_cnt = self.estimate_tokens(m.get("content", ""))
            if current_tokens + t_cnt <= budget:
                trimmed_others.insert(0, m)
                current_tokens += t_cnt
            else:
                break

        final_msgs = system_msgs + trimmed_others
        total_tokens = system_tokens + current_tokens
        return final_msgs, total_tokens

    def compress_context(self, messages: list[dict[str, Any]]) -> str:
        """Generate abstract context compression summary for long multi-turn conversations."""
        if not messages:
            return "No conversation history."

        roles_summary = [f"{m.get('role', 'user')}: {m.get('content', '')[:60]}..." for m in messages[-6:]]
        summary = "Key Topics: " + " | ".join(roles_summary)
        return summary

    async def get_memory_context(
        self,
        conversation_id: str,
        messages: list[dict[str, Any]],
        query: str = "",
        max_tokens: int = 4000,
    ) -> MemoryContext:
        """Construct unified short-term and long-term memory context."""
        # 1. Short-Term Memory Trimming
        trimmed_msgs, total_tokens = self.trim_context(messages, max_tokens=max_tokens)
        is_compressed = len(trimmed_msgs) < len(messages)

        # 2. Long-Term Semantic References from SemanticCache
        long_term_refs: list[dict[str, Any]] = []
        if query:
            try:
                cached_res = semantic_cache.get(query)
                if cached_res and cached_res.get("hit"):
                    long_term_refs.append({
                        "reference_type": "semantic_cache_hit",
                        "similarity_score": cached_res.get("similarity_score", 1.0),
                        "content": cached_res.get("response_text", ""),
                    })
            except Exception:
                pass

        summary = ""
        if is_compressed:
            summary = self.compress_context(messages)

        return MemoryContext(
            conversation_id=conversation_id,
            short_term_messages=trimmed_msgs,
            long_term_references=long_term_refs,
            total_context_tokens=total_tokens,
            is_compressed=is_compressed,
            summary=summary,
        )


memory_engine = MemoryEngine()
