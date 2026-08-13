from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.mcp.governance import mcp_governance_engine

router = APIRouter(prefix="/mcp", tags=["MCP Tool Governance"])


class MCPToolCallPayload(BaseModel):
    tool_name: str = Field(..., description="Name of target MCP tool")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool execution parameters")
    user_role: str = Field(default="developer", description="User role initiating call")
    workspace_id: str = Field(default="default", description="Active workspace ID")


@router.get("/tools", summary="List Registered MCP Tools & RBAC Matrix")
async def list_mcp_tools():
    """Returns catalog of registered MCP tools and role permission rules."""
    return {
        "tools": [
            {
                "name": "query_sql",
                "description": "Execute database read query",
                "risk": "MEDIUM",
                "allowed_roles": ["admin", "developer", "analyst"],
            },
            {
                "name": "search_docs",
                "description": "Search enterprise knowledge base",
                "risk": "LOW",
                "allowed_roles": ["admin", "developer", "analyst", "viewer"],
            },
            {
                "name": "fetch_web_page",
                "description": "Fetch external HTTP web content",
                "risk": "LOW",
                "allowed_roles": ["admin", "developer", "analyst"],
            },
            {
                "name": "execute_system_command",
                "description": "Execute shell script on backend node",
                "risk": "CRITICAL",
                "allowed_roles": ["admin"],
            },
        ],
        "role_permissions": mcp_governance_engine.role_tool_permissions,
    }


@router.post("/inspect", summary="Inspect & Validate MCP Payload Request")
async def inspect_mcp_payload(payload: MCPToolCallPayload):
    """Intercept and inspect MCP payload request before downstream agent execution."""
    res = mcp_governance_engine.inspect_tool_call(
        tool_name=payload.tool_name,
        arguments=payload.arguments,
        user_role=payload.user_role,
        workspace_id=payload.workspace_id,
    )
    if not res.allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "message": res.reason,
                    "tool_name": res.tool_name,
                    "risk_level": res.risk_level,
                    "code": "mcp_governance_violation",
                }
            },
        )
    return {
        "allowed": True,
        "status": res.status,
        "tool_name": res.tool_name,
        "reason": res.reason,
        "risk_level": res.risk_level,
    }
