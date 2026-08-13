"""Enterprise Conversation Export Engine.

Exports conversation threads into structured JSON, GitHub Markdown, and PDF layout specifications.
"""

from dataclasses import dataclass
import datetime
from typing import Any


class ConversationExporter:
    """Multi-format Conversation Exporter."""

    def export_json(self, conversation: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Export conversation as structured JSON."""
        return {
            "version": "1.0",
            "exported_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "conversation": conversation,
            "messages": messages,
            "stats": {
                "total_messages": len(messages),
                "total_tokens": sum(m.get("tokens", m.get("token_usage", {}).get("total_tokens", 0)) for m in messages),
                "total_cost_usd": sum(m.get("cost", 0.0) for m in messages),
            },
        }

    def export_markdown(self, conversation: dict[str, Any], messages: list[dict[str, Any]]) -> str:
        """Export conversation as clean GitHub-Flavored Markdown document."""
        title = conversation.get("title", "Conversation Export")
        c_id = conversation.get("conversation_id") or conversation.get("id")
        created = conversation.get("created_at", "")
        prov = conversation.get("current_provider") or conversation.get("provider", "N/A")
        mod = conversation.get("current_model") or conversation.get("model", "N/A")

        lines = [
            f"# {title}",
            f"**Conversation ID**: `{c_id}`  ",
            f"**Created Date**: {created}  ",
            f"**Provider / Model**: `{prov} / {mod}`  ",
            "---",
            "",
            "## Conversation Transcript",
            "",
        ]

        for idx, m in enumerate(messages, 1):
            role = m.get("role", "user").upper()
            content = m.get("content", "")
            ts = m.get("timestamp") or m.get("created_at", "")
            tokens = m.get("tokens", 0)
            cost = m.get("cost", 0.0)

            lines.append(f"### {idx}. [{role}] — *{ts}*")
            lines.append(f"> Tokens: {tokens} | Cost: ${cost:.6f}")
            lines.append("")
            lines.append(content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def export_pdf_spec(self, conversation: dict[str, Any], messages: list[dict[str, Any]]) -> dict[str, Any]:
        """Export PDF layout document specification."""
        return {
            "document_type": "PDF_EXPORT_SPECIFICATION",
            "paper_size": "A4",
            "margin_mm": 20,
            "header": {
                "title": conversation.get("title", "Conversation Report"),
                "subtitle": f"Sentinel AI Workspace Export | ID: {conversation.get('id')}",
            },
            "summary_card": {
                "total_messages": len(messages),
                "total_tokens": sum(m.get("tokens", 0) for m in messages),
                "total_cost_usd": sum(m.get("cost", 0.0) for m in messages),
            },
            "content_blocks": [
                {
                    "block_id": f"msg-{m.get('id', idx)}",
                    "role": m.get("role"),
                    "content": m.get("content"),
                    "timestamp": m.get("timestamp"),
                }
                for idx, m in enumerate(messages)
            ],
        }


conversation_exporter = ConversationExporter()
