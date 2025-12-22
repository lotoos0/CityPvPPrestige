/**
 * Authentication module
 * Handles token storage and auth state
 */

const TOKEN_KEY = "citypvp.token";

/**
 * Get stored auth token
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Set auth token
 */
export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
  return !!getToken();
}

/**
 * Clear authentication
 */
export function logout() {
  setToken(null);
}
