export const getApiBaseUrl = () => {
  const envUrl = (typeof process !== "undefined" && process.env && (process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL)) || "http://localhost:8000/api/v1";
  return envUrl.endsWith("/api/v1") ? envUrl : `${envUrl.replace(/\/+$/, "")}/api/v1`;
};

export const API_BASE_URL = getApiBaseUrl();


function accessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

function refreshToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

async function request(endpoint, options = {}, isRetry = false) {
  const token = accessToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    cache: "no-store",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token && {
        Authorization: `Bearer ${token}`,
      }),
      ...(options.headers || {}),
    },
  }).catch(() => {
    throw new Error("Unable to connect to Sentinel AI Gateway. Please check network connection.");
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    if (
      response.status === 401 &&
      !isRetry &&
      endpoint !== "/auth/login" &&
      endpoint !== "/auth/register" &&
      endpoint !== "/auth/refresh"
    ) {
      const rToken = refreshToken();
      if (rToken) {
        try {
          const newSession = await api.refresh(rToken);
          if (typeof window !== "undefined" && newSession && newSession.access_token) {
            localStorage.setItem("access_token", newSession.access_token);
            localStorage.setItem("refresh_token", newSession.refresh_token);
            if (newSession.user) {
              localStorage.setItem("user", JSON.stringify(newSession.user));
            }
            return request(endpoint, options, true);
          }
        } catch {
          // Token refresh failed, proceed to dispatch session-expired
        }
      }
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("sentinel:session-expired"));
      }
    }
    throw new Error(data.detail || "Something went wrong");
  }

  return data;
}

const apiCache = new Map();
const CACHE_TTL_MS = 15000;

async function cachedRequest(key, fetcher) {
  const now = Date.now();
  const entry = apiCache.get(key);
  if (entry && now - entry.timestamp < CACHE_TTL_MS) {
    return entry.data;
  }
  const data = await fetcher();
  apiCache.set(key, { data, timestamp: now });
  return data;
}

export function clearApiCache() {
  apiCache.clear();
}

export const api = {
  /* ---------------- HEALTH & SYSTEM ---------------- */

  health() {
    return request("/health");
  },

  getSystemHealth() {
    return request("/system/health");
  },

  getSystemReadiness() {
    return request("/system/readiness");
  },

  getSystemLiveness() {
    return request("/system/liveness");
  },

  getSystemVersion() {
    return request("/system/version");
  },

  getSystemConfig() {
    return request("/system/config");
  },

  providerHealth() {
    return request("/health/providers");
  },

  workspaceAnalytics() {
    return request("/analytics");
  },

  history(query = "") {
    return request(`/history${query ? `?query=${encodeURIComponent(query)}` : ""}`);
  },

  configureProvider(providerId, payload) {
    clearApiCache();
    return request(`/providers/${encodeURIComponent(providerId)}/configuration`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  createProvider(payload) {
    clearApiCache();
    return request("/providers", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getProvider(providerId) {
    return request(`/providers/${encodeURIComponent(providerId)}`);
  },

  deleteProvider(providerId) {
    clearApiCache();
    return request(`/providers/${encodeURIComponent(providerId)}`, {
      method: "DELETE",
    });
  },

  testProvider(providerId) {
    return request(`/providers/${encodeURIComponent(providerId)}/test`, { method: "POST" });
  },

  healthCheckProvider(providerId) {
    return request(`/providers/${encodeURIComponent(providerId)}/health-check`, { method: "POST" });
  },

  updateProviderFailover(providerId, payload) {
    clearApiCache();
    return request(`/providers/${encodeURIComponent(providerId)}/failover`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  toggleProvider(providerId, enabled) {
    clearApiCache();
    return request(`/providers/${encodeURIComponent(providerId)}/toggle?enabled=${enabled}`, {
      method: "POST",
    });
  },

  databaseHealth() {
    return request("/health/database");
  },

  redisHealth() {
    return request("/health/redis");
  },

  /* ---------------- CATALOG ---------------- */

  providers() {
    return cachedRequest("providers", () => request("/providers"));
  },

  models() {
    return cachedRequest("models", () => request("/models?enabled_only=true"));
  },

  /* ---------------- ROUTING ---------------- */

  route(payload) {
    return request("/routing/route", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  explainRoute(payload) {
    return request("/routing/explain", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /* ---------------- COST INTELLIGENCE ---------------- */

  estimate(payload) {
    return request("/cost/estimate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  compare(payload) {
    return request("/cost/compare", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getBudget(workspaceId = "default") {
    return request(`/cost/budget?workspace_id=${encodeURIComponent(workspaceId)}`);
  },

  getRecommendations() {
    return request("/cost/recommendations");
  },

  /* ---------------- RELIABILITY PLATFORM ---------------- */

  getCircuitBreakers() {
    return request("/reliability/circuit-breakers");
  },

  resetCircuitBreaker(providerId) {
    return request(`/reliability/circuit-breakers/${encodeURIComponent(providerId)}/reset`, { method: "POST" });
  },

  getReliabilityQueues() {
    return request("/reliability/queues");
  },

  getReliabilityWorkers() {
    return request("/reliability/workers");
  },

  getReliabilityMetrics() {
    return request("/reliability/metrics");
  },

  /* ---------------- SECURITY PLATFORM ---------------- */

  getSecurityRoles() {
    return request("/security/roles");
  },

  getSecurityPermissions() {
    return request("/security/permissions");
  },

  getSecurityAudit(workspaceId = "default") {
    return request(`/security/audit?workspace_id=${encodeURIComponent(workspaceId)}`);
  },

  createSecurityApiKey(payload) {
    return request("/security/api-keys", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  revokeSecurityApiKey(id) {
    return request(`/security/api-keys/${encodeURIComponent(id)}`, { method: "DELETE" });
  },

  rotateSecurityApiKey(id) {
    return request(`/security/api-keys/${encodeURIComponent(id)}/rotate`, { method: "POST" });
  },

  getSecuritySessions() {
    return request("/security/sessions");
  },

  revokeSecuritySession(id) {
    return request(`/security/sessions/${encodeURIComponent(id)}`, { method: "DELETE" });
  },

  getSecurityMetrics() {
    return request("/security/metrics");
  },

  /* ---------------- CONVERSATIONS ---------------- */

  createConversation(payload) {
    return request("/conversations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getConversations(query = "") {
    return request(`/conversations${query ? `?${query}` : ""}`);
  },

  updateConversation(id, payload) {
    return request(`/conversations/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
  },

  togglePinConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/pin`, {
      method: "POST",
    });
  },

  toggleArchiveConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/archive`, {
      method: "POST",
    });
  },

  duplicateConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/duplicate`, {
      method: "POST",
    });
  },

  toggleFavoriteConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/favorite`, {
      method: "POST",
    });
  },

  restoreConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/restore`, {
      method: "POST",
    });
  },

  permanentDeleteConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/permanent`, {
      method: "DELETE",
    });
  },

  shareConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/share`, {
      method: "POST",
    });
  },

  getSharedConversation(shareToken) {
    return request(`/conversations/shared/${encodeURIComponent(shareToken)}`);
  },

  importConversation(payload) {
    return request("/conversations/import", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  exportConversation(id) {
    return request(`/conversations/${encodeURIComponent(id)}/export`);
  },

  /* ---------------- CHAT ---------------- */

  sendMessage(payload) {
    return request("/chat", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getMessages(conversationId) {
    return request(`/chat/${conversationId}/messages`);
  },

  deleteMessage(messageId) {
    return request(`/chat/messages/${encodeURIComponent(messageId)}`, {
      method: "DELETE",
    });
  },

  cancelStream(streamId) {
    return request(`/chat/stream/${encodeURIComponent(streamId)}/cancel`, {
      method: "POST",
    });
  },

  getActiveStreams() {
    return request("/chat/stream/active");
  },

  /* ---------------- FILES ---------------- */

  uploadFile(file) {
    const formData = new FormData();
    formData.append("file", file);
    return fetch(`${API_BASE_URL}/files/upload`, {
      method: "POST",
      body: formData,
    }).then((res) => {
      if (!res.ok) throw new Error("File upload failed");
      return res.json();
    });
  },

  /* ---------------- AUTH ---------------- */

  register(payload) {
    return request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  login(payload) {
    return request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  me() {
    return request("/auth/me");
  },

  refresh(refresh_token) {
    return request("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({
        refresh_token,
      }),
    });
  },

  logout(refresh_token) {
    return request("/auth/logout", {
      method: "POST",
      body: JSON.stringify({
        refresh_token,
      }),
    });
  },

  // Governance Policies API
  getPolicies(workspace_id) {
    const q = workspace_id ? `?workspace_id=${workspace_id}` : "";
    return request(`/policies${q}`);
  },

  createPolicy(payload) {
    return request("/policies", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updatePolicy(policyId, payload) {
    return request(`/policies/${policyId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deletePolicy(policyId) {
    return request(`/policies/${policyId}`, {
      method: "DELETE",
    });
  },

  simulatePolicy(payload) {
    return request("/policies/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Semantic Cache API
  getCacheStats() {
    return request("/cache/stats");
  },

  invalidateCache(workspaceId) {
    return request("/cache/invalidate", {
      method: "POST",
      body: JSON.stringify({ workspace_id: workspaceId || null }),
    });
  },

  warmCache(payload) {
    return request("/cache/warm", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // AI Guardrails API
  getGuardrailStats() {
    return request("/guardrails/stats");
  },

  scanPrompt(payload) {
    return request("/guardrails/scan", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  simulateGuardrailResponse(payload) {
    return request("/guardrails/simulate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  // Virtual API Keys API
  getVirtualKeys(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/virtual-keys${q}`);
  },

  createVirtualKey(payload) {
    return request("/virtual-keys", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  rotateVirtualKey(keyId) {
    return request(`/virtual-keys/${keyId}/rotate`, {
      method: "POST",
    });
  },

  revokeVirtualKey(keyId) {
    return request(`/virtual-keys/${keyId}/revoke`, {
      method: "POST",
    });
  },

  // Enterprise RBAC Roles API
  getRoles() {
    return request("/roles");
  },

  getPermissionMatrix() {
    return request("/roles/permissions/matrix");
  },

  createRole(payload) {
    return request("/roles", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateRole(roleId, payload) {
    return request(`/roles/${roleId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteRole(roleId) {
    return request(`/roles/${roleId}`, {
      method: "DELETE",
    });
  },

  assignRole(userId, roleId) {
    return request("/roles/assign", {
      method: "POST",
      body: JSON.stringify({ user_id: userId, role_id: roleId }),
    });
  },

  // Enterprise Audit Logs API
  searchAuditLogs(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.workspace_id) searchParams.append("workspace_id", params.workspace_id);
    if (params.user_id) searchParams.append("user_id", params.user_id);
    if (params.action) searchParams.append("action", params.action);
    if (params.severity) searchParams.append("severity", params.severity);
    if (params.query) searchParams.append("query", params.query);
    if (params.limit) searchParams.append("limit", params.limit);

    const q = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return request(`/audit${q}`);
  },

  getAuditStats(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/audit/stats${q}`);
  },

  // Enterprise Financial Governance (FinOps) API
  getBudgets(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/finops/budgets${q}`);
  },

  updateBudget(payload) {
    return request("/finops/budgets", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getSpendSummary(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/finops/analytics/spend${q}`);
  },

  getForecast(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/finops/analytics/forecast${q}`);
  },

  getFinOpsAlerts(workspaceId) {
    const q = workspaceId ? `?workspace_id=${workspaceId}` : "";
    return request(`/finops/analytics/alerts${q}`);
  },

  getCostOptimizations() {
    return request("/finops/analytics/optimization");
  },

  // Enterprise Observability & Timeline Replay API
  searchTraces(params = {}) {
    const searchParams = new URLSearchParams();
    if (params.workspace_id) searchParams.append("workspace_id", params.workspace_id);
    if (params.user_id) searchParams.append("user_id", params.user_id);
    if (params.provider_id) searchParams.append("provider_id", params.provider_id);
    if (params.model_id) searchParams.append("model_id", params.model_id);
    if (params.status) searchParams.append("status", params.status);
    if (params.query) searchParams.append("query", params.query);
    if (params.limit) searchParams.append("limit", params.limit);

    const q = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return request(`/observability/traces${q}`);
  },

  getTraceDetail(traceId) {
    return request(`/observability/traces/${traceId}`);
  },

  getRequestReplay(traceId, userId = "admin") {
    return request(`/observability/traces/${traceId}/replay?user_id=${userId}`);
  },

  getOperationalMetrics() {
    return request("/observability/metrics");
  },

  getProviderHealthStatus() {
    return request("/observability/providers/health");
  },

  getOperationalAlerts() {
    return request("/observability/alerts");
  },

  // Enterprise Multi-Tenant Workspaces & SSO API
  getOrganizations() {
    return request("/organizations");
  },

  createOrganization(payload) {
    return request("/organizations", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getWorkspaces(orgId) {
    const q = orgId ? `?org_id=${orgId}` : "";
    return request(`/workspaces${q}`);
  },

  createWorkspace(payload) {
    return request("/workspaces", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getOrgMembers(orgId) {
    return request(`/organizations/${orgId}/members`);
  },

  inviteMember(orgId, payload) {
    return request(`/organizations/${orgId}/invitations`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  acceptInvitation(payload) {
    return request("/invitations/accept", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getOrgSSO(orgId) {
    return request(`/organizations/${orgId}/sso`);
  },

  setupOrgSSO(orgId, payload) {
    return request(`/organizations/${orgId}/sso`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getUserProfile() {
    return request("/users/me/profile");
  },

  updateUserProfile(payload) {
    return request("/users/me/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  // Adaptive AI Routing & Intent Detection API
  detectIntent(payload) {
    return request("/routing/intent", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  performAdaptiveRouting(payload) {
    return request("/routing/adaptive", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getModelCapabilities() {
    return request("/routing/capabilities");
  },

  getRoutingStrategies() {
    return request("/routing/strategies");
  },

  // Enterprise Policy Simulator & AI Optimization Advisor API
  runPolicySimulation(payload) {
    return request("/policies/simulation/run", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getPolicyVersions() {
    return request("/policies/simulation/versions");
  },

  publishPolicyVersion(payload) {
    return request("/policies/simulation/versions", {
      method: "POST",
    });
  },

  rollbackPolicyVersion(versionId) {
    return request(`/policies/simulation/versions/${versionId}/rollback`, {
      method: "POST",
    });
  },

  getOptimizationRecommendations() {
    return request("/policies/simulation/advisor/recommendations");
  },

  applyOptimizationRecommendation(recId) {
    return request(`/policies/simulation/advisor/recommendations/${recId}/apply`, {
      method: "POST",
    });
  },

  runWhatIfScenario(payload) {
    return request("/policies/simulation/what-if", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  // Team Invitation & Management API
  inviteTeamMember(payload) {
    return request("/team/invite", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getTeamMembers() {
    return request("/team/members");
  },
};

export default api;
