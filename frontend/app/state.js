/**
 * Application state
 * Simple reactive state for shared data
 */

class AppState {
  constructor() {
    this.city = null;
    this.user = null;
    this.listeners = new Set();
  }

  /**
   * Update state and notify listeners
   */
  setState(updates) {
    Object.assign(this, updates);
    this.notify();
  }

  /**
   * Subscribe to state changes
   */
  subscribe(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify all listeners
   */
  notify() {
    this.listeners.forEach((cb) => cb(this));
  }

  /**
   * Reset state (on logout)
   */
  reset() {
    this.city = null;
    this.user = null;
    this.notify();
  }
}

export const state = new AppState();
