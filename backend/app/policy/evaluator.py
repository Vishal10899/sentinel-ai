"""Runtime Policy Evaluation Engine.

Evaluates budget limits, provider/model/region restrictions, prompt security rules (PII, secrets),
and produces policy decisions (ALLOW, DENY, WARN, REDIRECT, FALLBACK, LOG_ONLY) in < 2ms.
"""

import datetime
import re
import time
from typing import Any
import uuid

from app.audit.engine import audit_engine
from app.policy.models import AIPolicy, BudgetAction, PolicyAction, PolicyAuditLogRecord, PolicyDecision
from app.policy.repository import PolicyRepository, policy_repository


class PolicyEngine:
    """Enterprise Runtime Policy Engine (< 2ms evaluation time)."""

    PREMIUM_MODELS = {"gpt-5", "gpt-4o", "claude-sonnet-4", "claude-3-5-sonnet", "o3-mini"}

    _PII_PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b(?:\d[ -]*?){13,16}\b",
        "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
    }

    _SECRET_PATTERNS = {
        "api_key": r"\b(sk-[A-Za-z0-9\-_]{20,}|AIzaSy[A-Za-z0-9\-_]{33}|ghp_[A-Za-z0-9]{36})\b",
        "jwt": r"\beyJ[A-Za-z0-9\-_]*\.eyJ[A-Za-z0-9\-_]*\.[A-Za-z0-9\-_]*\b",
        "bearer": r"\bBearer\s+[A-Za-z0-9_\-\.=]+\b",
        "private_key": r"-----BEGIN\s+(RSA|EC|PRIVATE)\s+KEY-----",
    }

    def __init__(self, repository: PolicyRepository | None = None) -> None:
        self.repository = repository or policy_repository

    def _check_prompt_security(self, prompt: str, policy: AIPolicy) -> tuple[str | None, str | None]:
        """Check prompt text for PII, Secrets, Blocked Keywords, and Prompt Token limits."""
        if not prompt:
            return None, None

        # PII Detection
        if policy.detect_pii:
            for pii_type, pattern in self._PII_PATTERNS.items():
                if re.search(pattern, prompt):
                    return "PII_DETECTED", f"Prompt contains sensitive PII data ({pii_type})."

        # Secret & Credential Detection
        if policy.detect_secrets or policy.detect_credentials:
            for sec_type, pattern in self._SECRET_PATTERNS.items():
                if re.search(pattern, prompt):
                    return "SECRET_LEAK", f"Prompt contains exposed credential or secret token ({sec_type})."

        # Blocked Keywords Check
        if policy.blocked_keywords:
            text_lower = prompt.lower()
            for kw in policy.blocked_keywords:
                if kw.lower() in text_lower:
                    return "BLOCKED_KEYWORD", f"Prompt contains blocked keyword '{kw}'."

        # Large Prompt Abuse Check
        if policy.max_prompt_tokens and len(prompt) // 4 > policy.max_prompt_tokens:
            return "PROMPT_ABUSE", f"Prompt token count ({len(prompt) // 4}) exceeds maximum allowed limit ({policy.max_prompt_tokens})."

        return None, None

    def evaluate(self, request_payload: dict[str, Any]) -> PolicyDecision:
        """Evaluate request context against active runtime policies in < 2ms."""
        t0 = time.perf_counter_ns()

        workspace_id = request_payload.get("workspace_id", "default")
        user_id = request_payload.get("user_id", "default_user")
        request_id = request_payload.get("request_id", f"req-{uuid.uuid4().hex[:12]}")
        provider_id = request_payload.get("provider_id") or request_payload.get("provider", "gemini")
        model_id = request_payload.get("model_id") or request_payload.get("model", "gemini-2.0-flash")
        region = request_payload.get("region", "us-east-1")
        prompt = request_payload.get("prompt", "")
        max_tokens = request_payload.get("max_tokens") or request_payload.get("max_completion_tokens")
        temperature = request_payload.get("temperature", 0.7)

        policies = self.repository.list_policies(workspace_id=workspace_id)
        active_policies = [p for p in policies if p.is_active]

        if not active_policies:
            t1 = time.perf_counter_ns()
            eval_ms = round((t1 - t0) / 1_000_000, 3)
            return PolicyDecision(
                action=PolicyAction.ALLOW,
                reason="No active runtime policies found. Request allowed.",
                evaluation_time_ms=eval_ms,
            )

        modified_req = dict(request_payload)
        warnings: list[str] = []
        is_modified = False

        for policy in active_policies:
            # 1. Prompt Security Evaluation
            sec_violation, sec_reason = self._check_prompt_security(prompt, policy)
            if sec_violation:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.DENY,
                    reason=f"Security Policy Violation: {sec_reason}",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            # 2. Provider & Model Restrictions
            if provider_id in policy.blocked_providers:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.DENY,
                    reason=f"Provider '{provider_id}' is explicitly blocked by policy '{policy.name}'.",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            if model_id in policy.blocked_models:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.DENY,
                    reason=f"Model '{model_id}' is explicitly blocked by policy '{policy.name}'.",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            if policy.restrict_premium_models and model_id in self.PREMIUM_MODELS:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.FALLBACK,
                    reason=f"Premium model '{model_id}' restricted by policy '{policy.name}'. Falling back to budget model '{policy.fallback_model}'.",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    fallback_model=policy.fallback_model,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            # 3. Region Restriction Check
            if policy.restricted_regions and region in policy.restricted_regions:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.DENY,
                    reason=f"Deployment region '{region}' is restricted by policy '{policy.name}'.",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            # 4. Budget Enforcement Check
            if policy.monthly_budget_limit_usd is not None and policy.current_spend_usd >= policy.monthly_budget_limit_usd:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                if policy.budget_action == BudgetAction.DOWNGRADE_MODEL:
                    decision = PolicyDecision(
                        action=PolicyAction.FALLBACK,
                        reason=f"Monthly budget limit of ${policy.monthly_budget_limit_usd:.2f} exceeded. Downgrading to fallback model '{policy.fallback_model}'.",
                        policy_id=policy.id,
                        policy_name=policy.name,
                        fallback_model=policy.fallback_model,
                        evaluation_time_ms=eval_ms,
                    )
                else:
                    decision = PolicyDecision(
                        action=PolicyAction.DENY,
                        reason=f"Monthly budget limit of ${policy.monthly_budget_limit_usd:.2f} exceeded (Spend: ${policy.current_spend_usd:.2f}). Request blocked.",
                        policy_id=policy.id,
                        policy_name=policy.name,
                        evaluation_time_ms=eval_ms,
                    )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            # 5. Redirect Action Check
            if policy.redirect_provider and policy.redirect_model:
                t1 = time.perf_counter_ns()
                eval_ms = round((t1 - t0) / 1_000_000, 3)
                decision = PolicyDecision(
                    action=PolicyAction.REDIRECT,
                    reason=f"Policy '{policy.name}' redirected request to {policy.redirect_provider}/{policy.redirect_model}.",
                    policy_id=policy.id,
                    policy_name=policy.name,
                    redirect_provider=policy.redirect_provider,
                    redirect_model=policy.redirect_model,
                    evaluation_time_ms=eval_ms,
                )
                self.repository.record_log(policy, decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
                return decision

            # 6. Parameter Modifications
            if policy.max_tokens and max_tokens and int(max_tokens) > policy.max_tokens:
                modified_req["max_tokens"] = policy.max_tokens
                is_modified = True
                warnings.append(f"max_tokens capped to policy limit {policy.max_tokens}.")

        t1 = time.perf_counter_ns()
        eval_ms = round((t1 - t0) / 1_000_000, 3)

        action = PolicyAction.MODIFY if is_modified else (PolicyAction.WARN if warnings else PolicyAction.ALLOW)
        reason = "Request parameters adjusted to satisfy governance policy." if is_modified else "Request passed all policy governance checks."

        decision = PolicyDecision(
            action=action,
            reason=reason,
            modified_request=modified_req if is_modified else None,
            warnings=warnings,
            evaluation_time_ms=eval_ms,
        )
        self.repository.record_log(active_policies[0], decision, user_id=user_id, workspace_id=workspace_id, request_id=request_id)
        return decision


policy_engine = PolicyEngine()
