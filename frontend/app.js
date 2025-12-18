const API_KEY = "citypvp.api";
const TOKEN_KEY = "citypvp.token";

const apiBaseInput = document.getElementById("apiBase");
const saveApiBtn = document.getElementById("saveApi");
const authMessage = document.getElementById("authMessage");
const logoutBtn = document.getElementById("logoutBtn");
const registerForm = document.getElementById("registerForm");
const loginForm = document.getElementById("loginForm");
const collectBtn = document.getElementById("collectBtn");
const resourceStats = document.getElementById("resourceStats");
const combatStats = document.getElementById("combatStats");
const gridEl = document.getElementById("grid");
const buildingType = document.getElementById("buildingType");
const buildStatus = document.getElementById("buildStatus");

let cityState = null;

function getApiBase() {
  return localStorage.getItem(API_KEY) || "http://localhost:8000";
}

function setApiBase(value) {
  localStorage.setItem(API_KEY, value);
  apiBaseInput.value = value;
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function setMessage(message, isError = false) {
  authMessage.textContent = message;
  authMessage.style.color = isError ? "#ff8c6a" : "#9fb0c9";
}

function setBuildStatus(message, isError = false) {
  buildStatus.textContent = message;
  buildStatus.style.color = isError ? "#ff8c6a" : "#9fb0c9";
}

async function register(payload) {
  const response = await fetch(`${getApiBase()}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Register failed");
  }

  return response.json();
}

async function login(payload) {
  const form = new URLSearchParams();
  form.set("username", payload.email);
  form.set("password", payload.password);

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
}

async function fetchCity() {
  const response = await fetch(`${getApiBase()}/city`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load city");
  }

  return response.json();
}

async function collectResources() {
  const response = await fetch(`${getApiBase()}/city/collect`, {
    method: "POST",
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Collect failed");
  }

  return response.json();
}

async function fetchStats() {
  const response = await fetch(`${getApiBase()}/stats`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load stats");
  }

  return response.json();
}

async function placeBuilding(payload) {
  const response = await fetch(`${getApiBase()}/city/build`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Build failed");
  }

  return response.json();
}

function renderStats(city) {
  resourceStats.innerHTML = "";
  const stats = [
    ["Gold", city.gold],
    ["Population", city.pop],
    ["Power", city.power],
    ["Prestige", city.prestige],
  ];

  stats.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "stat";
    row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    resourceStats.appendChild(row);
  });
}

function renderCombat(stats) {
  combatStats.innerHTML = "";
  const items = [
    ["Attack", stats.attack_power],
    ["Defense", stats.defense_power],
  ];

  items.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "stat";
    row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    combatStats.appendChild(row);
  });
}

function renderGrid(city) {
  gridEl.innerHTML = "";
  const buildingMap = new Map();

  city.buildings.forEach((b) => {
    buildingMap.set(`${b.x}:${b.y}`, b);
  });

  for (let y = 0; y < city.grid_size; y += 1) {
    for (let x = 0; x < city.grid_size; x += 1) {
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile";

      const building = buildingMap.get(`${x}:${y}`);
      if (building) {
        tile.classList.add("filled");
        tile.textContent = `${building.type.replace("_", " ").toUpperCase()} L${building.level}`;
      } else {
        tile.textContent = `${x},${y}`;
      }

      tile.addEventListener("click", () => handleBuild(x, y, building));
      gridEl.appendChild(tile);
    }
  }
}

async function refreshCity() {
  try {
    const [city, stats] = await Promise.all([fetchCity(), fetchStats()]);
    cityState = city;
    renderStats(city);
    renderCombat(stats);
    renderGrid(city);
    collectBtn.disabled = false;
    setBuildStatus("Ready to build.");
  } catch (error) {
    collectBtn.disabled = true;
    setBuildStatus(error.message, true);
  }
}

async function handleBuild(x, y, existing) {
  if (existing) {
    setBuildStatus("Tile already occupied.", true);
    return;
  }

  const type = buildingType.value;
  if (!type) {
    setBuildStatus("Select a building type first.", true);
    return;
  }

  try {
    const updated = await placeBuilding({ type, x, y });
    cityState = updated;
    renderStats(updated);
    renderGrid(updated);
    const stats = await fetchStats();
    renderCombat(stats);
    setBuildStatus(`Placed ${type} at ${x},${y}.`);
  } catch (error) {
    setBuildStatus(error.message, true);
  }
}

registerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(registerForm);
  try {
    await register({
      email: data.get("email"),
      password: data.get("password"),
    });
    setMessage("Registered. You can log in now.");
  } catch (error) {
    setMessage(error.message, true);
  }
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const data = new FormData(loginForm);
  try {
    const token = await login({
      email: data.get("email"),
      password: data.get("password"),
    });
    setToken(token.access_token);
    logoutBtn.disabled = false;
    setMessage("Logged in.");
    await refreshCity();
  } catch (error) {
    setMessage(error.message, true);
  }
});

logoutBtn.addEventListener("click", () => {
  setToken(null);
  logoutBtn.disabled = true;
  cityState = null;
  gridEl.innerHTML = "";
  resourceStats.innerHTML = "";
  setMessage("Logged out.");
  setBuildStatus("");
  collectBtn.disabled = true;
});

collectBtn.addEventListener("click", async () => {
  if (!cityState) return;
  try {
    const updated = await collectResources();
    cityState = updated;
    renderStats(updated);
    const stats = await fetchStats();
    renderCombat(stats);
    setBuildStatus("Collected resources.");
  } catch (error) {
    setBuildStatus(error.message, true);
  }
});

saveApiBtn.addEventListener("click", () => {
  const value = apiBaseInput.value.trim();
  if (value) {
    setApiBase(value);
  }
});

setApiBase(getApiBase());
if (getToken()) {
  logoutBtn.disabled = false;
  refreshCity();
}
