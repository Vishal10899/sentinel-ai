const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

function accessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request(endpoint, options = {}) {
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
  });

  if (response.status === 204) return null;

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.detail || "Something went wrong");
  }

  return data;
}

export const api = {
  /* ---------------- HEALTH ---------------- */

  health() {
    return request("/health");
  },

  providerHealth() {
    return request("/health/providers");
  },

  databaseHealth() {
    return request("/health/database");
  },

  redisHealth() {
    return request("/health/redis");
  },

  /* ---------------- CATALOG ---------------- */

  providers() {
    return request("/providers");
  },

  models() {
    return request("/models?enabled_only=true");
  },

  /* ---------------- ROUTING ---------------- */

  route(payload) {
    return request("/routing/route", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  /* ---------------- COST ---------------- */

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
};

export default api;