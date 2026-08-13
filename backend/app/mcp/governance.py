import re
import logging
from typing import Any
from dataclasses import dataclass
from fastapi import HTTPException, status

from app.audit.engine import audit_engine

logger = logging.getLogger(__name__)


@dataclass
class MCPToolCallRequest:
    tool_name: str
    arguments: dict[str, Any]
    user_role: str = "developer"
    workspace_id: str = "default"


@dataclass
class MCPGovernanceResult:
    allowed: bool
    status: str  # ALLOWED, BLOCKED
    tool_name: str
    reason: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class MCPGovernanceEngine:
    """Enterprise Model Context Protocol (MCP) Tool Governance & RBAC Engine."""

    def __init__(self) -> None:
        # Destructive SQL pattern detection
        self.destructive_sql_pattern = re.compile(
            r"\b(DELETE\s+FROM|DROP\s+TABLE|DROP\s+DATABASE|TRUNCATE\s+TABLE|ALTER\s+TABLE|GRANT\s+ALL)\b",
            re.IGNORECASE,
        )
        # Dangerous system execution pattern
        self.system_exec_pattern = re.compile(
            r"\b(rm\s+-rf|exec|eval|system|spawn|format|dd\s+if=)\b",
            re.IGNORECASE,
        )

        # RBAC Tool Permissions mapping per role
        self.role_tool_permissions: dict[str, set[str]] = {
            "admin": {"*"},
            "developer": {"query_sql", "search_docs", "fetch_web_page", "run_read_only_query", "list_files"},
            "analyst": {"search_docs", "fetch_web_page", "run_read_only_query"},
            "viewer": {"search_docs"},
        }

    def inspect_tool_call(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        user_role: str = "developer",
        user_id: str = "default_user",
        workspace_id: str = "default",
    ) -> MCPGovernanceResult:
        """Inspect and enforce governance rules on downstream MCP tool invocation."""

        # 1. RBAC Permission Check
        allowed_tools = self.role_tool_permissions.get(user_role.lower(), self.role_tool_permissions["viewer"])
        if "*" not in allowed_tools and tool_name not in allowed_tools:
            msg = f"Role '{user_role}' is not authorized to invoke MCP tool '{tool_name}'."
            audit_engine.record_event(
                action="MCP_TOOL_ACCESS_DENIED",
                resource=f"tools/{tool_name}",
                user_id=user_id,
                workspace_id=workspace_id,
                severity="HIGH",
                status="DENIED",
                new_value=msg,
            )
            return MCPGovernanceResult(
                allowed=False,
                status="BLOCKED",
                tool_name=tool_name,
                reason=msg,
                risk_level="HIGH",
            )

        # 2. Inspect Arguments for Destructive SQL or Exec Operations
        arg_str = str(arguments)

        if self.destructive_sql_pattern.search(arg_str):
            msg = f"Destructive SQL operation detected in arguments for MCP tool '{tool_name}'. Query blocked."
            audit_engine.record_event(
                action="MCP_DESTRUCTIVE_QUERY_BLOCKED",
                resource=f"tools/{tool_name}",
                user_id=user_id,
                workspace_id=workspace_id,
                severity="CRITICAL",
                status="BLOCKED",
                new_value=msg,
            )
            return MCPGovernanceResult(
                allowed=False,
                status="BLOCKED",
                tool_name=tool_name,
                reason=msg,
                risk_level="CRITICAL",
            )

        if self.system_exec_pattern.search(arg_str):
            msg = f"Dangerous system command execution pattern detected for MCP tool '{tool_name}'."
            audit_engine.record_event(
                action="MCP_DANGEROUS_EXEC_BLOCKED",
                resource=f"tools/{tool_name}",
                user_id=user_id,
                workspace_id=workspace_id,
                severity="CRITICAL",
                status="BLOCKED",
                new_value=msg,
            )
            return MCPGovernanceResult(
                allowed=False,
                status="BLOCKED",
                tool_name=tool_name,
                reason=msg,
                risk_level="CRITICAL",
            )

        # 3. Approved Invocation
        audit_engine.record_event(
            action="MCP_TOOL_INVOKED",
            resource=f"tools/{tool_name}",
            user_id=user_id,
            workspace_id=workspace_id,
            severity="INFO",
            status="ALLOWED",
            new_value=f"Tool '{tool_name}' successfully executed by role '{user_role}'.",
        )

        return MCPGovernanceResult(
            allowed=True,
            status="ALLOWED",
            tool_name=tool_name,
            reason="Tool invocation passed all MCP RBAC and safety guardrails.",
            risk_level="LOW",
        )


mcp_governance_engine = MCPGovernanceEngine()
