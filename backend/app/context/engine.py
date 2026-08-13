from dataclasses import dataclass
from typing import Any


@dataclass
class ContextBudget:
    """Token budget breakdown for context window management."""

    max_context_tokens: int = 8192
    reserved_response_tokens: int = 1024
    system_budget: int = 1024
    attachment_budget: int = 4096
    history_budget: int = 2048


class ContextEngine:
    """Enterprise Context Engine allocating token budgets, ranking context, and truncating gracefully."""

    def __init__(self, default_max_context_tokens: int = 8192) -> None:
        self.default_max_context_tokens = default_max_context_tokens

    def allocate_budget(self, max_context_tokens: int | None = None) -> ContextBudget:
        """Calculate token budget limits dynamically based on model context window."""
        max_tokens = max_context_tokens or self.default_max_context_tokens
        reserved = min(int(max_tokens * 0.2), 2048)
        available = max_tokens - reserved

        return ContextBudget(
            max_context_tokens=max_tokens,
            reserved_response_tokens=reserved,
            system_budget=min(int(available * 0.15), 1024),
            attachment_budget=int(available * 0.55),
            history_budget=int(available * 0.30),
        )

    def build_prompt_context(
        self,
        prompt: str,
        system_prompt: str | None = None,
        attachments: list[dict[str, Any]] | None = None,
        max_context_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Rank, merge, and truncate system prompt, user query, and attachment text into token-budget compliant prompt."""
        budget = self.allocate_budget(max_context_tokens)

        # 1. Truncate System Prompt if provided
        formatted_system = ""
        if system_prompt and system_prompt.strip():
            sys_text = system_prompt.strip()
            sys_tokens = max(len(sys_text) // 4, 1)
            if sys_tokens > budget.system_budget:
                char_limit = budget.system_budget * 4
                sys_text = sys_text[:char_limit] + "... [truncated]"
            formatted_system = sys_text

        # 2. Extract & Truncate Attachment Contexts
        formatted_attachments = []
        total_att_tokens = 0
        if attachments:
            for att in attachments:
                text = att.get("extracted_text", "").strip()
                filename = att.get("filename", "Attached File")
                if not text:
                    continue

                att_tokens = max(len(text) // 4, 1)
                if total_att_tokens + att_tokens > budget.attachment_budget:
                    remaining_budget = max(budget.attachment_budget - total_att_tokens, 0)
                    if remaining_budget > 50:
                        char_limit = remaining_budget * 4
                        text = text[:char_limit] + "... [context truncated]"
                        formatted_attachments.append(f"--- Document: {filename} ---\n{text}")
                        total_att_tokens += remaining_budget
                    break
                else:
                    formatted_attachments.append(f"--- Document: {filename} ---\n{text}")
                    total_att_tokens += att_tokens

        # 3. Assemble Final Unified Prompt
        prompt_parts = []
        if formatted_system:
            prompt_parts.append(f"System: {formatted_system}")

        if formatted_attachments:
            prompt_parts.append("[Attached Document Context]\n" + "\n\n".join(formatted_attachments))

        prompt_parts.append(f"User: {prompt}")

        final_prompt = "\n\n".join(prompt_parts)
        prompt_tokens = max(len(final_prompt) // 4, 1)

        return {
            "full_prompt": final_prompt,
            "prompt_tokens": prompt_tokens,
            "budget": {
                "max_context_tokens": budget.max_context_tokens,
                "attachment_budget": budget.attachment_budget,
                "attachment_tokens_used": total_att_tokens,
            },
            "attachments_count": len(formatted_attachments),
        }


context_engine = ContextEngine()
