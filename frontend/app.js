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
const rankTop = document.getElementById("rankTop");
const rankNear = document.getElementById("rankNear");
const rankStatus = document.getElementById("rankStatus");
const attackLog = document.getElementById("attackLog");
const historyStatus = document.getElementById("historyStatus");

let cityState = null;
let currentUser = null;

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

async function fetchMe() {
  const response = await fetch(`${getApiBase()}/auth/me`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load user profile");
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

async function fetchRankTop() {
  const response = await fetch(`${getApiBase()}/rank/top`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load top ranking");
  }

  return response.json();
}

async function fetchRankNear() {
  const response = await fetch(`${getApiBase()}/rank/near`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load near ranking");
  }

  return response.json();
}

async function attackPlayer(userId) {
  const response = await fetch(`${getApiBase()}/pvp/attack`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ defender_id: userId }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Attack failed");
  }

  return response.json();
}

async function fetchAttackLog() {
  const response = await fetch(`${getApiBase()}/pvp/log`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load attack log");
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

function renderRankList(container, entries) {
  container.innerHTML = "";
  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "rank-row";
    row.innerHTML = `<span>#${entry.rank}</span><span>${entry.email}</span><span>${entry.prestige}</span>`;

    const attackBtn = document.createElement("button");
    attackBtn.className = "btn ghost";
    attackBtn.textContent = "Attack";
    attackBtn.disabled = entry.user_id === currentUser?.id;

    attackBtn.addEventListener("click", async () => {
      try {
        const result = await attackPlayer(entry.user_id);
        rankStatus.textContent = `Result: ${result.result} (Δ${result.prestige_delta_attacker})`;
        await refreshCity();
      } catch (error) {
        rankStatus.textContent = error.message;
      }
    });

    row.appendChild(attackBtn);
    container.appendChild(row);
  });
}

function renderHistory(entries) {
  attackLog.innerHTML = "";
  entries.forEach((entry) => {
    const isAttacker = entry.attacker_id === currentUser?.id;
    const opponent = isAttacker ? entry.defender_email : entry.attacker_email;
    const delta = isAttacker ? entry.prestige_delta_attacker : entry.prestige_delta_defender;
    const outcome = delta >= 0 ? "Prestige up" : "Prestige down";
    const timestamp = new Date(entry.created_at).toLocaleString();

    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
      <div>
        <strong>${outcome} (${delta})</strong>
        <span>${isAttacker ? "Attacked" : "Defended"} vs ${opponent} • ${entry.result}</span>
      </div>
      <span>${timestamp}</span>
    `;
    attackLog.appendChild(item);
  });
}

async function refreshHistory() {
  try {
    const entries = await fetchAttackLog();
    renderHistory(entries);
    historyStatus.textContent = "";
  } catch (error) {
    historyStatus.textContent = error.message;
  }
}

async function refreshRanking() {
  try {
    const [top, near] = await Promise.all([fetchRankTop(), fetchRankNear()]);
    renderRankList(rankTop, top);
    renderRankList(rankNear, near);
    rankStatus.textContent = "";
  } catch (error) {
    rankStatus.textContent = error.message;
  }
}

async function refreshCity() {
  try {
    const [city, stats, me] = await Promise.all([fetchCity(), fetchStats(), fetchMe()]);
    cityState = city;
    currentUser = me;
    renderStats(city);
    renderCombat(stats);
    renderGrid(city);
    collectBtn.disabled = false;
    setBuildStatus("Ready to build.");
    await Promise.all([refreshRanking(), refreshHistory()]);
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
  currentUser = null;
  gridEl.innerHTML = "";
  resourceStats.innerHTML = "";
  rankTop.innerHTML = "";
  rankNear.innerHTML = "";
  attackLog.innerHTML = "";
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
