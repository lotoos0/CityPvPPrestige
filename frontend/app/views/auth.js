/**
 * Auth view - login and registration
 */

import { authApi, setApiBase, getApiBase } from "../api.js";
import { setToken, getToken } from "../auth.js";
import { router } from "../router.js";
import { showToast } from "../components/toast.js";

let initialized = false;

export async function authView() {
  const authSection = document.getElementById("authSection");
  const apiBaseInput = document.getElementById("apiBase");
  const saveApiBtn = document.getElementById("saveApi");
  const logoutBtn = document.getElementById("logoutBtn");

  // Show auth section
  authSection.style.display = "block";
  document.querySelector(".hud").style.display = "none";
  document.querySelector(".city").style.display = "none";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "none";

  // Update logout button state
  logoutBtn.disabled = !getToken();

  // Initialize API base input
  apiBaseInput.value = getApiBase();

  // Initialize event listeners (only once)
  if (!initialized) {
    initialized = true;

    // API base save
    saveApiBtn.addEventListener("click", () => {
      const value = apiBaseInput.value.trim();
      if (value) {
        setApiBase(value);
        showToast("API base saved");
      }
    });

    // Register form
    const registerForm = document.getElementById("registerForm");
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(registerForm);
      try {
        await authApi.register(data.get("email"), data.get("password"));
        showToast("Registered! You can log in now.");
        registerForm.reset();
      } catch (error) {
        showToast(error.message || "Registration failed", true);
      }
    });

    // Login form
    const loginForm = document.getElementById("loginForm");
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = new FormData(loginForm);
      try {
        const response = await authApi.login(data.get("email"), data.get("password"));
        setToken(response.access_token);
        logoutBtn.disabled = false;
        showToast("Logged in!");
        loginForm.reset();
        router.navigate("/city");
      } catch (error) {
        showToast(error.message || "Login failed", true);
      }
    });

    // Logout button
    logoutBtn.addEventListener("click", () => {
      setToken(null);
      logoutBtn.disabled = true;
      showToast("Logged out");
      router.navigate("/");
    });
  }
}
