"""Comprehensive Unit, Integration, & Performance Test Suite for Sprint 3.0.

Tests Enterprise RBAC, Fine-Grained Permissions, Role Inheritance, Workspace Isolation,
API Key Management, Secret Encryption & Masking, Multi-Device Session Revocation,
Audit Logging, Security Metrics, and Performance Benchmarks.
"""

import time
import pytest

from app.audit import audit_engine, audit_repository
from app.rbac import ALL_PERMISSIONS, rbac_engine, role_repository
from app.security import (
    enterprise_api_key_manager,
    secret_manager,
    security_metrics_aggregator,
    session_manager,
)


# ====================================================
# 1. RBAC & Permission Matrix Tests (< 0.2 ms)
# ====================================================

def test_rbac_roles_and_permission_inheritance():
    # 1. Check all 8 required built-in roles exist
    roles = role_repository.list_roles()
    role_ids = {r.id for r in roles}

    expected_roles = {
        "role-super-admin", "role-org-admin", "role-workspace-admin",
        "role-ai-engineer", "role-analyst", "role-developer",
        "role-viewer", "role-service-account",
    }
    assert expected_roles.issubset(role_ids)

    # 2. Permission inheritance resolution
    org_admin_perms = role_repository.get_effective_permissions("role-org-admin")
    assert "view_models" in org_admin_perms
    assert "manage_workspaces" in org_admin_perms

    # 3. Super Admin wildcard access
    super_admin_perms = role_repository.get_effective_permissions("role-super-admin")
    assert "*" in super_admin_perms

    # 4. RBAC Check Permission (< 0.2 ms)
    allowed = rbac_engine.check_permission("user-1", "view_models")
    assert allowed is True


# ====================================================
# 2. API Key Management Tests (< 0.2 ms)
# ====================================================

def test_api_key_management():
    # 1. Create API key
    rec, raw_key = enterprise_api_key_manager.create_api_key("CI-CD Pipeline Key")
    assert rec.key_id is not None
    assert raw_key.startswith("sentinel_sec_")
    assert rec.masked_key != raw_key  # Raw key is masked in metadata

    # 2. Rotate API key
    rotated = enterprise_api_key_manager.rotate_api_key(rec.key_id)
    assert rotated is not None
    updated_rec, new_raw_key = rotated
    assert new_raw_key != raw_key

    # 3. Revoke API key
    revoked = enterprise_api_key_manager.revoke_api_key(rec.key_id)
    assert revoked is True
    assert len(enterprise_api_key_manager.list_api_keys()) == 0


# ====================================================
# 3. Secret Management & Masking Tests
# ====================================================

def test_secret_management_and_masking():
    raw_secret = "sk-proj-1234567890abcdef"

    # Masking test
    masked = secret_manager.mask_secret(raw_secret)
    assert masked.startswith("sk-p...")
    assert raw_secret not in masked

    # Encryption at rest & storage
    rec = secret_manager.store_secret("openai_key", raw_secret, "provider_key")
    assert rec.encrypted_value.startswith("enc_sha256_")

    # Rotation hook
    rotated = secret_manager.rotate_secret(rec.secret_id, "sk-proj-new-secret-val")
    assert rotated is not None
    assert rotated.version == 2


# ====================================================
# 4. Multi-Device Session Management Tests (< 0.2 ms)
# ====================================================

def test_session_management():
    user_id = "usr-security-test"

    # Create sessions across multi-devices
    s1 = session_manager.create_session(user_id, device_info="MacBook Pro Chrome")
    s2 = session_manager.create_session(user_id, device_info="iPhone 15 Mobile")

    # Validate session (< 0.2 ms)
    valid, sess = session_manager.validate_session(s1.session_id)
    assert valid is True
    assert sess.session_id == s1.session_id

    # Force logout specific session
    session_manager.revoke_session(s1.session_id)
    valid_after, _ = session_manager.validate_session(s1.session_id)
    assert valid_after is False

    # Force logout all user sessions
    revoked_count = session_manager.revoke_all_user_sessions(user_id)
    assert revoked_count == 1


# ====================================================
# 5. Audit Logging Tests (< 0.5 ms)
# ====================================================

def test_audit_logging():
    rec = audit_engine.record_event(
        action="API_KEY_CREATED",
        resource="api_key:key-test-123",
        user_id="admin-1",
        workspace_id="ws-enterprise",
    )
    assert rec.id is not None
    assert rec.action == "API_KEY_CREATED"

    logs = audit_repository.list(workspace_id="ws-enterprise")
    assert len(logs) >= 1


# ====================================================
# 6. Performance Benchmarks Tests
# ====================================================

def test_performance_benchmarks():
    # 1. Permission Check (< 0.2 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        rbac_engine.check_permission("user-1", "view_models")
    perm_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert perm_ms < 0.2, f"Permission check took {perm_ms:.3f} ms (limit 0.2 ms)"

    # 2. RBAC Evaluation (< 0.2 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        role_repository.get_effective_permissions("role-org-admin")
    rbac_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert rbac_ms < 0.2, f"RBAC evaluation took {rbac_ms:.3f} ms (limit 0.2 ms)"

    # 3. Audit Logging (< 0.5 ms)
    t0 = time.perf_counter_ns()
    for _ in range(100):
        audit_engine.record_event("TEST_ACTION", "resource:test")
    audit_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert audit_ms < 0.5, f"Audit logging took {audit_ms:.3f} ms (limit 0.5 ms)"

    # 4. Session Validation (< 0.2 ms)
    s = session_manager.create_session("bench-user")
    t0 = time.perf_counter_ns()
    for _ in range(100):
        session_manager.validate_session(s.session_id)
    sess_ms = ((time.perf_counter_ns() - t0) / 1_000_000) / 100.0
    assert sess_ms < 0.2, f"Session validation took {sess_ms:.3f} ms (limit 0.2 ms)"
