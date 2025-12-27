/**
 * Main entry point
 * Initializes router and registers all routes
 */

import { router } from "./router.js";
import { getToken, initTopbarLogout, isAuthenticated, updateTopbarLogout } from "./auth.js";
import { getApiBase, setApiBase } from "./api.js";
import { authView } from "./views/auth.js";
import { showToast } from "./components/toast.js";
import { cityView } from "./views/city.js";
import { pvpView, stopPvpView } from "./views/pvp.js";
import { armyView, stopArmyView } from "./views/army.js";
import { historyView } from "./views/history.js";

// Set auth guard
router.setAuthGuard(isAuthenticated);

// Initialize topbar logout button
initTopbarLogout(router);

// Update topbar on route change
router.onRouteChange = updateTopbarLogout;

const apiBaseInput = document.getElementById("apiBase");
const saveApiBtn = document.getElementById("saveApi");
if (apiBaseInput) {
  apiBaseInput.value = getApiBase();
}
if (saveApiBtn && apiBaseInput) {
  saveApiBtn.addEventListener("click", () => {
    const value = apiBaseInput.value.trim();
    if (!value) return;
    setApiBase(value);
    showToast("API base saved");
  });
}

// Register routes
router.register("/", authView, false);
router.register("/city", cityView, true);
router.register("/pvp", pvpView, true);
router.register("/army", armyView, true);
router.register("/history", historyView, true);

// Initialize router
router.init();

// Auto-navigate to city if already logged in
if (getToken() && window.location.hash === "") {
  router.navigate("/city");
}

// Cleanup on route change
window.addEventListener("hashchange", () => {
  stopPvpView();
  stopArmyView();
});
