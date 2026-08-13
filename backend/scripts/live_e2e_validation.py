import urllib.request
import json
import urllib.error
import time
import sys

BASE = 'http://localhost:8000/api/v1'

def req(path, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    url = f'{BASE}{path}'
    body = json.dumps(data).encode('utf-8') if data is not None else None
    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            content = resp.read().decode('utf-8')
            try:
                return resp.status, json.loads(content) if content else {}
            except Exception:
                return resp.status, {'text': content}
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8')
        try:
            return e.code, json.loads(content)
        except Exception:
            return e.code, {'detail': content}

def run_all():
    print('=== 1. Scenario A: Super Admin 1 (Vishalkumar75912@gmail.com) ===')
    status, data = req('/auth/login', 'POST', {'email': 'Vishalkumar75912@gmail.com', 'password': 'SuperAdminPassword123!'})
    print(f'Login: {status}')
    assert status == 200, f'Login failed: {data}'
    token_sa1 = data['access_token']

    status, me = req('/auth/me', 'GET', token=token_sa1)
    print(f"Me: {status}, role={me.get('role', {}).get('name')}, perms_count={len(me.get('effective_permissions', []))}")
    assert '*' in me.get('effective_permissions', []), f"Expected * in permissions, got {me.get('effective_permissions')}"

    endpoints = [
        ('/providers', 'GET', 'Providers'),
        ('/models', 'GET', 'Model Catalog'),
        ('/routing/strategies', 'GET', 'Routing Strategies'),
        ('/routing/capabilities', 'GET', 'Routing Capabilities'),
        ('/policies', 'GET', 'Policies'),
        ('/guardrails/stats', 'GET', 'Guardrails'),
        ('/security/roles', 'GET', 'Security & DLP Matrix'),
        ('/virtual-keys', 'GET', 'Virtual API Keys'),
        ('/organizations', 'GET', 'Organizations'),
        ('/workspaces', 'GET', 'Workspaces'),
        ('/roles', 'GET', 'Roles/RBAC'),
        ('/audit', 'GET', 'Audit Logs'),
        ('/audit/export', 'GET', 'Audit Export'),
        ('/finops/budgets', 'GET', 'FinOps/Budgets'),
        ('/observability/metrics', 'GET', 'Observability Metrics'),
        ('/observability/traces', 'GET', 'Observability Traces'),
        ('/mcp/tools', 'GET', 'MCP Governance'),
        ('/cache/stats', 'GET', 'Semantic Cache'),
        ('/reliability/circuit-breakers', 'GET', 'Failover/Circuit Breakers'),
        ('/policies/simulation/versions', 'GET', 'Policy Simulator Versions'),
        ('/policies/simulation/advisor/recommendations', 'GET', 'Policy Simulator Advisor'),
        ('/system/config', 'GET', 'Platform Settings'),
    ]
    for p, m, label in endpoints:
        s, d = req(p, m, token=token_sa1)
        print(f'  [{label}] {p} [{m}]: {s}')
        assert s in [200, 201], f'Endpoint {label} ({p}) failed: {s} {d}'

    print('Scenario A: PASS\n')

    print('=== 2. Scenario B: Founder / Super Admin 2 (Vishalchaudhary74096@gmail.com) ===')
    status, data = req('/auth/login', 'POST', {'email': 'Vishalchaudhary74096@gmail.com', 'password': 'SuperAdminPassword123!'})
    print(f'Login: {status}')
    assert status == 200, f'Login failed: {data}'
    token_sa2 = data['access_token']

    status, me2 = req('/auth/me', 'GET', token=token_sa2)
    print(f"Me: {status}, role={me2.get('role', {}).get('name')}, title={me2.get('title')}, perms_count={len(me2.get('effective_permissions', []))}")
    assert '*' in me2.get('effective_permissions', [])
    assert me2.get('title') == 'Founder'
    for p, m, label in endpoints:
        s, d = req(p, m, token=token_sa2)
        assert s in [200, 201], f'Endpoint {label} ({p}) failed for SA2: {s} {d}'
    print('Scenario B: PASS\n')

    print('=== 3. Scenario C: Fresh Normal Signup ===')
    ts = int(time.time())
    cust_email = f'founder_{ts}@acme-corp.com'
    status, reg_data = req('/auth/register', 'POST', {
        'email': cust_email,
        'password': 'StrongPassword123!',
        'name': 'Acme Founder',
        'organization_name': f'Acme Corp {ts}'
    })
    print(f'Register: {status}')
    assert status == 200, f'Register failed: {reg_data}'
    token_cust = reg_data['access_token']
    status, me_cust = req('/auth/me', 'GET', token=token_cust)
    print(f"Me: {status}, role_id={me_cust.get('role', {}).get('id')}, perms_count={len(me_cust.get('effective_permissions', []))}")
    assert me_cust.get('role', {}).get('id') == 'role-org-admin', f"Expected role-org-admin, got {me_cust.get('role')}"
    assert '*' not in me_cust.get('effective_permissions', []), 'Normal signup MUST NOT have *'
    org_id_a = me_cust.get('organization', {}).get('id')
    print('Scenario C: PASS\n')

    print('=== 4. Scenario D: Invite Developer & Least Privilege ===')
    dev_email = f'dev_{ts}@acme-corp.com'
    status, inv_data = req(f'/organizations/{org_id_a}/invitations', 'POST', {
        'email': dev_email,
        'role_id': 'role-developer',
        'org_id': org_id_a
    }, token=token_cust)
    print(f'Invite dev: {status}')
    assert status == 201, f'Invite failed: {inv_data}'

    status, dev_reg = req('/auth/register', 'POST', {
        'email': dev_email,
        'password': 'StrongPassword123!',
        'name': 'Dev Engineer'
    })
    print(f'Dev register: {status}')
    assert status == 200, f'Dev register failed: {dev_reg}'
    token_dev = dev_reg['access_token']
    status, me_dev = req('/auth/me', 'GET', token=token_dev)
    print(f"Dev Me: {status}, role_id={me_dev.get('role', {}).get('id')}, perms={me_dev.get('effective_permissions')}")
    assert me_dev.get('role', {}).get('id') == 'role-developer'

    # Allowed endpoint
    s_allowed, _ = req('/models', 'GET', token=token_dev)
    print(f'Dev access /models: {s_allowed}')
    assert s_allowed == 200

    # Forbidden admin endpoints
    forbidden = [
        ('/providers', 'POST', {'name': 'test'}),
        (f'/organizations/{org_id_a}/invitations', 'POST', {'email': 'x@x.com'}),
        ('/audit', 'GET', None),
        ('/audit/export', 'GET', None),
        ('/finops/budgets', 'POST', {'amount': 100}),
    ]
    for p, m, d in forbidden:
        s, res = req(p, m, data=d, token=token_dev)
        print(f'Dev accessing {p} [{m}]: {s}')
        assert s == 403, f'Expected 403 for dev on {p}, got {s}: {res}'
    print('Scenario D: PASS\n')

    print('=== 5. Scenario E: Multi-Tenant Boundary Isolation ===')
    cust_b_email = f'founder_b_{ts}@beta-inc.com'
    status, reg_b = req('/auth/register', 'POST', {
        'email': cust_b_email,
        'password': 'StrongPassword123!',
        'name': 'Beta Founder',
        'organization_name': f'Beta Inc {ts}'
    })
    assert status == 200
    token_b = reg_b['access_token']
    status, me_b = req('/auth/me', 'GET', token=token_b)
    org_id_b = me_b.get('organization', {}).get('id')

    # Org A Admin accessing Org B
    s_cross, d_cross = req(f'/organizations/{org_id_b}', 'GET', token=token_cust)
    print(f'Org A admin accessing Org B: {s_cross}')
    assert s_cross == 403, f'Expected 403 cross-tenant access, got {s_cross}: {d_cross}'

    # Super Admin accessing Org B
    s_sa_access, d_sa_access = req(f'/organizations/{org_id_b}', 'GET', token=token_sa1)
    print(f'Super Admin accessing Org B: {s_sa_access}')
    assert s_sa_access == 200, f'Super Admin should access Org B: {s_sa_access}: {d_sa_access}'

    print('Scenario E: PASS\n')
    print('======================================================')
    print('ALL AUTHENTICATION / RBAC E2E TESTS PASSED (100% PASS)')
    print('======================================================')

if __name__ == '__main__':
    run_all()
