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

const listeners = new Map();

export function on(event, fn) {
  if (!listeners.has(event)) listeners.set(event, new Set());
  listeners.get(event).add(fn);
  return () => {
    const set = listeners.get(event);
    if (!set) return;
    set.delete(fn);
    if (set.size === 0) listeners.delete(event);
  };
}

export function emit(event, payload = null) {
  const set = listeners.get(event);
  if (!set) return;
  for (const fn of set) {
    try {
      fn(payload);
    } catch (error) {
      console.error("event handler error", event, error);
    }
  }
}
