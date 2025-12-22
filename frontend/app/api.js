/**
 * API layer - centralized HTTP communication
 * All API calls go through this module
 */

const API_KEY = "citypvp.api";

/**
 * Get configured API base URL
 */
export function getApiBase() {
  return localStorage.getItem(API_KEY) || "http://localhost:8000";
}

/**
 * Set API base URL
 */
export function setApiBase(value) {
  localStorage.setItem(API_KEY, value);
}

/**
 * Generate idempotency key for requests
 */
function idempotencyKey() {
  if (crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * Generic GET request
 * @param {string} path - API endpoint path
 * @param {Object} headers - Additional headers
 */
export async function apiGet(path, headers = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    headers: { ...headers },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
}

/**
 * Generic POST request
 * @param {string} path - API endpoint path
 * @param {Object} body - Request body
 * @param {Object} headers - Additional headers
 */
export async function apiPost(path, body = {}, headers = {}) {
  const response = await fetch(`${getApiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
}

/**
 * Auth API
 */
export const authApi = {
  async register(email, password) {
    return apiPost("/auth/register", { email, password });
  },

  async login(email, password) {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);

    const response = await fetch(`${getApiBase()}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || "Login failed");
    }

    return response.json();
  },

  async me(token) {
    return apiGet("/auth/me", { Authorization: `Bearer ${token}` });
  },
};

/**
 * City API
 */
export const cityApi = {
  async fetch(token) {
    return apiGet("/city", { Authorization: `Bearer ${token}` });
  },

  async collect(token) {
    return apiPost("/city/collect", {}, { Authorization: `Bearer ${token}` });
  },

  async build(token, type, x, y) {
    return apiPost("/city/build", { type, x, y }, { Authorization: `Bearer ${token}` });
  },
};

/**
 * Stats API
 */
export const statsApi = {
  async fetch(token) {
    return apiGet("/stats", { Authorization: `Bearer ${token}` });
  },
};

/**
 * PvP API
 */
export const pvpApi = {
  async limits(token) {
    return apiGet("/pvp/limits", { Authorization: `Bearer ${token}` });
  },

  async attack(token, defenderId) {
    return apiPost(
      "/pvp/attack",
      { defender_id: defenderId },
      {
        Authorization: `Bearer ${token}`,
        "Idempotency-Key": idempotencyKey(),
      }
    );
  },

  async log(token) {
    return apiGet("/pvp/log", { Authorization: `Bearer ${token}` });
  },
};

/**
 * Rank API
 */
export const rankApi = {
  async top(token) {
    return apiGet("/rank/top", { Authorization: `Bearer ${token}` });
  },

  async near(token) {
    return apiGet("/rank/near", { Authorization: `Bearer ${token}` });
  },
};

/**
 * Army API
 */
export const armyApi = {
  async fetch(token) {
    return apiGet("/army", { Authorization: `Bearer ${token}` });
  },
};

/**
 * Barracks API
 */
export const barracksApi = {
  async queue(token) {
    return apiGet("/barracks/queue", { Authorization: `Bearer ${token}` });
  },

  async train(token, unitCode, qty) {
    return apiPost("/barracks/train", { unit_code: unitCode, qty }, { Authorization: `Bearer ${token}` });
  },

  async claim(token) {
    return apiPost("/barracks/claim", {}, { Authorization: `Bearer ${token}` });
  },
};
