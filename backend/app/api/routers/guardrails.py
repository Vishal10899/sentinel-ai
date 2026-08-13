"""AI Guardrails & Security Threat Detection API Router."""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends

from app.api.dependencies import current_user
from app.guardrails.engine import guardrails_engine
from app.models.user import User

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


class ScanPromptRequest(BaseModel):
    prompt: str = Field(min_length=1)
    block_high_risk: bool = True
    redact_pii: bool = True
    redact_secrets: bool = True


@router.get("/stats", summary="Get AI Guardrails detection statistics")
async def get_guardrail_stats(user: User = Depends(current_user)):
    """Retrieve guardrail detection telemetry (injections, jailbreaks, PII redactions, masked secrets, blocked requests)."""
    return guardrails_engine.get_metrics()


@router.post("/scan", summary="Scan prompt for safety threats and PII")
async def scan_prompt(request: ScanPromptRequest, user: User = Depends(current_user)):
    """Scan and sanitize an input prompt for injection attacks, jailbreaks, PII, and API keys."""
    res = guardrails_engine.scan_request(
        prompt=request.prompt,
        block_high_risk=request.block_high_risk,
        redact_pii=request.redact_pii,
        redact_secrets=request.redact_secrets,
    )
    return res.to_dict()


@router.post("/simulate", summary="Simulate response scanning and redaction")
async def simulate_response_scan(payload: dict[str, str], user: User = Depends(current_user)):
    """Simulate scanning LLM generated responses for accidental secret/PII leaks."""
    text = payload.get("response_text", "")
    sanitized = guardrails_engine.scan_response(text)
    return {
        "original_text": text,
        "sanitized_text": sanitized,
        "is_modified": text != sanitized,
    }
