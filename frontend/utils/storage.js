/**
 * Storage utility for authentication state.
 * All browser storage access should go through this module.
 */

const ACCESS_TOKEN = "access_token";
const REFRESH_TOKEN = "refresh_token";
const USER = "user";

const isBrowser = () => typeof window !== "undefined";

export function saveSession(session) {
  if (!isBrowser()) return;

  localStorage.setItem(ACCESS_TOKEN, session.access_token);
  localStorage.setItem(REFRESH_TOKEN, session.refresh_token);
  localStorage.setItem(USER, JSON.stringify(session.user));
}

export function getAccessToken() {
  if (!isBrowser()) return null;

  return localStorage.getItem(ACCESS_TOKEN);
}

export function getRefreshToken() {
  if (!isBrowser()) return null;

  return localStorage.getItem(REFRESH_TOKEN);
}

export function getUser() {
  if (!isBrowser()) return null;

  const user = localStorage.getItem(USER);

  if (!user) return null;

  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

export function clearSession() {
  if (!isBrowser()) return;

  localStorage.removeItem(ACCESS_TOKEN);
  localStorage.removeItem(REFRESH_TOKEN);
  localStorage.removeItem(USER);
}

export function hasSession() {
  return !!getAccessToken();
}