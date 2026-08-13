"""Runtime Policy Platform REST API Router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.dependencies import current_user, require_permission
from app.models.user import User
from app.policy import policy_engine, policy_repository
from app.policy.models import PolicyAction

router = APIRouter(prefix="/policies", tags=["policies"])


class PolicyEvaluationRequest(BaseModel):
    workspace_id: str = Field(default="default")
    user_id: str = Field(default="default_user")
    provider_id: str | None = Field(default="gemini")
    model_id: str | None = Field(default="gemini-2.0-flash")
    prompt: str = Field(default="Hello Sentinel Policy Engine")
    max_tokens: int | None = Field(default=200)
    temperature: float | None = Field(default=0.7)


class PolicyCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    workspace_id: str = Field(default="default")
    description: str = Field(default="")
    daily_budget_usd: float | None = None
    monthly_budget_limit_usd: float | None = None
    allowed_providers: list[str] = Field(default_factory=list)
    blocked_providers: list[str] = Field(default_factory=list)
    allowed_models: list[str] = Field(default_factory=list)
    blocked_models: list[str] = Field(default_factory=list)
    detect_pii: bool = True
    detect_secrets: bool = True
    blocked_keywords: list[str] = Field(default_factory=list)
    max_prompt_tokens: int | None = 4000
    is_active: bool = True


@router.get("", summary="List policies")
async def list_policies(workspace_id: str | None = Query(default=None)):
    """List runtime governance policies."""
    policies = policy_repository.list_policies(workspace_id=workspace_id)
    return [p.to_dict() for p in policies]


@router.get("/{policy_id}", summary="Get policy by ID")
async def get_policy(policy_id: str):
    """Retrieve policy details by ID."""
    policy = policy_repository.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Policy '{policy_id}' not found.")
    return policy.to_dict()


@router.post("", summary="Create a new policy")
async def create_policy(request: PolicyCreateRequest, user: User = Depends(require_permission("policy.manage"))):
    """Create a new runtime governance policy."""
    policy = policy_repository.create_policy(request.model_dump())
    return policy.to_dict()



@router.post("/evaluate", summary="Evaluate policy against request context")
async def evaluate_policy(request: PolicyEvaluationRequest):
    """Evaluate AI request context against active runtime policies in < 2ms."""
    decision = policy_engine.evaluate(request.model_dump())
    return decision.to_dict()


@router.post("/enforce", summary="Enforce policy rules")
async def enforce_policy(request: PolicyEvaluationRequest):
    """Evaluate and enforce policy decision. Throws HTTP 403 on DENY/BLOCK action."""
    decision = policy_engine.evaluate(request.model_dump())
    if decision.action in (PolicyAction.DENY, PolicyAction.BLOCK):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "PolicyEnforcementError",
                "action": decision.action.value,
                "reason": decision.reason,
                "policy_id": decision.policy_id,
            },
        )
    return decision.to_dict()


@router.get("/logs", summary="Get policy decision audit logs")
async def get_policy_logs(workspace_id: str | None = Query(default=None), limit: int = Query(default=100)):
    """Fetch policy decision audit logs."""
    logs = policy_repository.list_logs(workspace_id=workspace_id, limit=limit)
    return [l.to_dict() for l in logs]


from app.simulation.advisor import optimization_advisor
from app.simulation.engine import policy_simulator, policy_version_manager
from app.simulation.what_if import what_if_engine


class SimulateRequest(BaseModel):
    workspace_id: str = "default"
    proposed_policy: dict = Field(default_factory=dict)
    sample_trace_count: int = 100


class PublishPolicyRequest(BaseModel):
    policy_data: dict = Field(default_factory=dict)


class WhatIfRequest(BaseModel):
    scenario_type: str = Field(pattern="^(DISABLE_MODEL|BUDGET_CUT|PROVIDER_OUTAGE|LATENCY_THRESHOLD)$")
    parameters: dict = Field(default_factory=dict)
    workspace_id: str = "default"


@router.post("/simulation/run", summary="Run dry-run policy impact simulation")
async def run_simulation(request: SimulateRequest, user: User = Depends(current_user)):
    """Execute isolated dry-run policy simulation against trace records without mutating state."""
    result = policy_simulator.simulate(
        proposed_policy=request.proposed_policy,
        workspace_id=request.workspace_id,
        user_id=user.id,
        sample_size=request.sample_trace_count,
    )
    return result.to_dict()


@router.get("/simulation/versions", summary="List policy versions")
async def list_policy_versions(user: User = Depends(current_user)):
    """Retrieve versioned policy history and active status."""
    versions = policy_version_manager.list_versions()
    return [v.to_dict() for v in versions]


@router.post("/simulation/versions", status_code=status.HTTP_201_CREATED, summary="Publish new policy version")
async def publish_policy_version(request: PublishPolicyRequest, user: User = Depends(require_permission("policy.manage"))):
    """Publish a new versioned policy ruleset with zero downtime."""
    version = policy_version_manager.publish_version(
        policy_data=request.policy_data,
        publisher=user.name,
    )
    return version.to_dict()


@router.post("/simulation/versions/{version_id}/rollback", summary="Rollback policy version")
async def rollback_policy_version(version_id: str, user: User = Depends(require_permission("policy.manage"))):
    """Rollback active production policy to a previous version."""
    version = policy_version_manager.rollback_version(version_id=version_id, actor=user.name)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy version not found")
    return version.to_dict()


@router.post("/simulation/what-if", summary="Run What-If scenario analysis")
async def run_what_if_analysis(request: WhatIfRequest, user: User = Depends(current_user)):
    """Evaluate what-if questions (disabling model, budget cut, provider outage, latency threshold)."""
    result = what_if_engine.evaluate_scenario(
        scenario_type=request.scenario_type,
        parameters=request.parameters,
        workspace_id=request.workspace_id,
        user_id=user.id,
    )
    return result.to_dict()


@router.get("/simulation/advisor/recommendations", summary="Get AI optimization recommendations")
async def get_simulation_recommendations(user: User = Depends(current_user)):
    """Retrieve actionable cost, routing, latency, and cache recommendations."""
    recs = optimization_advisor.get_recommendations()
    return [r.to_dict() for r in recs]


@router.post("/simulation/advisor/recommendations/{rec_id}/apply", summary="Apply optimization recommendation")
async def apply_simulation_recommendation(rec_id: str, user: User = Depends(require_permission("policy.manage"))):
    """Apply an AI optimization recommendation and log audit event."""
    rec = optimization_advisor.apply_recommendation(rec_id=rec_id, actor_id=user.id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")
    return rec.to_dict()

