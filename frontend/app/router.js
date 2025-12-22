/**
 * Hash-based SPA router
 * Routes:
 * - #/          → auth (login/register)
 * - #/city      → city grid + resources
 * - #/pvp       → ranking + attack
 * - #/army      → army + barracks
 * - #/history   → attack log
 */

class Router {
  constructor() {
    this.routes = new Map();
    this.currentRoute = null;
    this.authGuard = null;
  }

  /**
   * Register a route handler
   * @param {string} path - Route path (e.g., "/city")
   * @param {Function} handler - Route handler function
   * @param {boolean} requiresAuth - Whether route requires authentication
   */
  register(path, handler, requiresAuth = false) {
    this.routes.set(path, { handler, requiresAuth });
  }

  /**
   * Set auth guard function
   * @param {Function} guard - Function that returns true if user is authenticated
   */
  setAuthGuard(guard) {
    this.authGuard = guard;
  }

  /**
   * Navigate to a route
   * @param {string} path - Route path
   */
  navigate(path) {
    window.location.hash = `#${path}`;
  }

  /**
   * Get current route path from hash
   */
  getCurrentPath() {
    const hash = window.location.hash.slice(1) || "/";
    return hash;
  }

  /**
   * Handle route change
   */
  async handleRoute() {
    const path = this.getCurrentPath();
    const route = this.routes.get(path);

    if (!route) {
      console.warn(`No handler for route: ${path}`);
      this.navigate("/");
      return;
    }

    // Auth guard check
    if (route.requiresAuth && this.authGuard && !this.authGuard()) {
      console.warn(`Route ${path} requires authentication`);
      this.navigate("/");
      return;
    }

    this.currentRoute = path;
    await route.handler();
  }

  /**
   * Initialize router
   */
  init() {
    window.addEventListener("hashchange", () => this.handleRoute());
    this.handleRoute();
  }
}

export const router = new Router();
