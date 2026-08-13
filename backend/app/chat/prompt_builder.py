"""Unified Enterprise PromptBuilder Engine for Sentinel AI.

Constructs standardized, role-based LLM messages payloads and clean fallback prompts.
Guarantees strict ordering: System Prompt -> Relevant Memory -> Conversation Summary -> Recent Messages -> Current User Prompt.
Prevents context leakage and raw string template artifact exposure.
"""

from typing import Any
from dataclasses import dataclass, field

@dataclass(frozen=True, slots=True)
class PromptContext:
    system_prompt: str | None = None
    memory_references: list[dict[str, Any]] = field(default_factory=list)
    conversation_summary: str | None = None
    prior_messages: list[Any] = field(default_factory=list)
    user_prompt: str = ""
    attachments: list[Any] = field(default_factory=list)

class PromptBuilder:
    """Unified Enterprise PromptBuilder."""

    def build_messages_payload(self, context: PromptContext) -> list[dict[str, str]]:
        """Construct universal role-based messages list for LLMs."""
        messages: list[dict[str, str]] = []

        # 1. System Prompt
        sys_parts = []
        if context.system_prompt and context.system_prompt.strip():
            sys_parts.append(context.system_prompt.strip())
        
        # 2. Relevant Memory / References
        if context.memory_references:
            mem_texts = [f"Reference ({m.get('reference_type', 'memory')}): {m.get('content', '')}" for m in context.memory_references]
            sys_parts.append("Relevant Context Memory:\n" + "\n".join(mem_texts))

        # 3. Conversation Summary
        if context.conversation_summary and context.conversation_summary.strip():
            sys_parts.append(f"Conversation Summary:\n{context.conversation_summary.strip()}")

        if sys_parts:
            messages.append({"role": "system", "content": "\n\n".join(sys_parts)})

        # 4. Recent Messages (prior turns from active conversation ONLY)
        for msg in context.prior_messages:
            content = getattr(msg, "content", None) or (msg.get("content") if isinstance(msg, dict) else "")
            role = getattr(msg, "role", None) or (msg.get("role") if isinstance(msg, dict) else "user")
            if content and content.strip():
                standard_role = "user" if role == "user" else "assistant"
                messages.append({"role": standard_role, "content": content.strip()})

        # 5. Current User Message (ALWAYS THE FINAL USER MESSAGE IN PAYLOAD)
        user_content = context.user_prompt.strip()
        if context.attachments:
            attached_texts = []
            for att in context.attachments:
                txt = getattr(att, "extracted_text", None) or (att.get("extracted_text") if isinstance(att, dict) else "")
                filename = getattr(att, "filename", None) or (att.get("filename") if isinstance(att, dict) else "Attachment")
                if txt:
                    attached_texts.append(f"--- Attachment: {filename} ---\n{txt}")
            if attached_texts:
                user_content += "\n\n" + "\n\n".join(attached_texts)

        messages.append({"role": "user", "content": user_content})
        return messages

    def build_text_prompt(self, context: PromptContext) -> str:
        """Construct clean text fallback prompt for providers requiring single text strings."""
        parts = []

        if context.system_prompt and context.system_prompt.strip():
            parts.append(f"System: {context.system_prompt.strip()}")

        if context.prior_messages:
            history_blocks = []
            for m in context.prior_messages:
                content = getattr(m, "content", None) or (m.get("content") if isinstance(m, dict) else "")
                role = getattr(m, "role", None) or (m.get("role") if isinstance(m, dict) else "user")
                if content and content.strip():
                    r_name = "User" if role == "user" else "Assistant"
                    history_blocks.append(f"[{r_name}]\n{content.strip()}")
            if history_blocks:
                parts.append("\n\n".join(history_blocks))

        user_content = context.user_prompt.strip()
        if context.attachments:
            attached_texts = []
            for att in context.attachments:
                txt = getattr(att, "extracted_text", None) or (att.get("extracted_text") if isinstance(att, dict) else "")
                filename = getattr(att, "filename", None) or (att.get("filename") if isinstance(att, dict) else "Attachment")
                if txt:
                    attached_texts.append(f"--- Attachment: {filename} ---\n{txt}")
            if attached_texts:
                user_content += "\n\n" + "\n\n".join(attached_texts)

        parts.append(user_content)
        return "\n\n".join(parts)


prompt_builder = PromptBuilder()
