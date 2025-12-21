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
const historyLoadMore = document.getElementById("historyLoadMore");
const pvpResetAt = document.getElementById("pvpResetAt");
const pvpRefreshBtn = document.getElementById("pvpRefreshBtn");
const pvpBanner = document.getElementById("pvpBanner");
const pvpAttacksRow = document.getElementById("pvpAttacksRow");
const pvpGainRow = document.getElementById("pvpGainRow");
const pvpLossRow = document.getElementById("pvpLossRow");
const pvpGlobalCooldown = document.getElementById("pvpGlobalCooldown");
const pvpTargetCooldown = document.getElementById("pvpTargetCooldown");
const pvpStatus = document.getElementById("pvpStatus");
const armyRefreshBtn = document.getElementById("army-refresh");
const armyStatus = document.getElementById("army-status");
const armyUnits = document.getElementById("army-units");
const trainUnit = document.getElementById("train-unit");
const trainQty = document.getElementById("train-qty");
const trainSubmit = document.getElementById("train-submit");
const queueRefreshBtn = document.getElementById("queue-refresh");
const claimSubmit = document.getElementById("claim-submit");
const barracksStatus = document.getElementById("barracks-status");
const barracksQueue = document.getElementById("barracks-queue");

let cityState = null;
let currentUser = null;
let pvpRefreshTimer = null;
let armyRefreshTimer = null;
let pvpLogNextCursor = null;
let pvpLogLoading = false;
let pvpLogSeen = new Set();

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

function idempotencyKey() {
  if (crypto && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function apiGet(path) {
  const response = await fetch(`${getApiBase()}${path}`, {
    headers: { ...authHeaders() },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
}

async function apiPost(path, body) {
  const response = await fetch(`${getApiBase()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body || {}),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw { status: response.status, data };
  }
  return data;
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
    headers: {
      "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey(),
      ...authHeaders(),
    },
    body: JSON.stringify({ defender_id: userId }),
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw { status: response.status, data: detail };
  }

  return response.json();
}

async function fetchAttackLog(limit = 20, cursor = null) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (cursor) {
    params.set("cursor", cursor);
  }
  const response = await fetch(`${getApiBase()}/pvp/log?${params.toString()}`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    throw new Error("Failed to load attack log");
  }

  return response.json();
}

async function fetchPvPLimits() {
  const response = await fetch(`${getApiBase()}/pvp/limits`, {
    headers: { ...authHeaders() },
  });

  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || "Failed to load PvP limits");
  }

  return response.json();
}

function formatResetAt(resetAt) {
  if (!resetAt) return "unknown";
  const date = new Date(resetAt);
  if (Number.isNaN(date.getTime())) return "unknown";
  return date.toLocaleString();
}

function secondsLeft(iso) {
  if (!iso) return null;
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return null;
  const delta = Math.floor((target - Date.now()) / 1000);
  return Math.max(0, delta);
}

function formatDuration(seconds) {
  if (seconds === null) return "n/a";
  if (seconds <= 0) return "Ready";
  if (seconds < 60) return `Ready in ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `Ready in ${minutes}m ${remainder}s`;
}

function setPvpStatus(message, isError = false) {
  pvpStatus.textContent = message;
  pvpStatus.style.color = isError ? "#ff8c6a" : "#9fb0c9";
}

function setArmyStatus(message, isError = false) {
  armyStatus.textContent = message;
  armyStatus.classList.remove("bad", "good");
  if (message) {
    armyStatus.classList.add(isError ? "bad" : "good");
  }
}

function renderArmy(units) {
  if (!units || units.length === 0) {
    armyUnits.textContent = "No units.";
    return;
  }

  armyUnits.innerHTML = units
    .map((unit) => `<div>${unit.code}: <strong>${unit.qty}</strong></div>`)
    .join("");
}

async function refreshArmy() {
  setArmyStatus("Loading...");
  try {
    const data = await apiGet("/army");
    renderArmy(data.units);
    setArmyStatus("OK");
  } catch (error) {
    setArmyStatus(`Disconnected (${error.status || "?"})`, true);
  }
}

function setBarracksStatus(message, isError = false) {
  barracksStatus.textContent = message;
  barracksStatus.classList.remove("bad", "good");
  if (message) {
    barracksStatus.classList.add(isError ? "bad" : "good");
  }
}

function formatCountdown(iso) {
  if (!iso) return "n/a";
  const target = new Date(iso).getTime();
  if (Number.isNaN(target)) return "n/a";
  const seconds = Math.max(0, Math.floor((target - Date.now()) / 1000));
  if (seconds === 0) return "Ready";
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

function renderQueue(queue) {
  if (!queue || !queue.status) {
    barracksQueue.textContent = "Queue empty.";
    return;
  }
  barracksQueue.innerHTML = `
    <div>Status: <strong>${queue.status}</strong></div>
    <div>Unit: <strong>${queue.unit_code}</strong>, qty: <strong>${queue.qty}</strong></div>
    <div>Completes: <strong>${queue.completes_at || "?"}</strong> (${formatCountdown(
      queue.completes_at
    )})</div>
  `;
}

async function refreshQueue() {
  setBarracksStatus("Loading...");
  try {
    const data = await apiGet("/barracks/queue");
    renderQueue(data);
    setBarracksStatus("OK");
  } catch (error) {
    setBarracksStatus(`Disconnected (${error.status || "?"})`, true);
  }
}

async function trainUnits() {
  setBarracksStatus("Training...");
  const unit = trainUnit.value;
  const qty = parseInt(trainQty.value, 10);

  try {
    await apiPost("/barracks/train", { unit_code: unit, qty });
    setBarracksStatus("Training started");
    await refreshQueue();
  } catch (error) {
    if (error.status === 409) {
      setBarracksStatus("Queue busy", true);
      return;
    }
    setBarracksStatus(`Error (${error.status || "?"})`, true);
  }
}

async function claimUnits() {
  setBarracksStatus("Claiming...");
  try {
    const data = await apiPost("/barracks/claim");
    if (!data.claimed) {
      setBarracksStatus("Nothing to claim", true);
      await refreshQueue();
      return;
    }
    setBarracksStatus(`Claimed ${data.qty} ${data.unit_code}`);
    await refreshQueue();
    await refreshArmy();
  } catch (error) {
    setBarracksStatus(`Error (${error.status || "?"})`, true);
  }
}

function startArmyHud() {
  if (armyRefreshTimer) return;
  armyRefreshBtn.disabled = false;
  refreshArmy();
  refreshQueue();
  armyRefreshTimer = setInterval(() => {
    refreshArmy();
    refreshQueue();
  }, 10000);
}

function stopArmyHud() {
  if (armyRefreshTimer) {
    clearInterval(armyRefreshTimer);
    armyRefreshTimer = null;
  }
  armyRefreshBtn.disabled = true;
  armyUnits.textContent = "No units.";
  barracksQueue.textContent = "Queue empty.";
  setArmyStatus("");
  setBarracksStatus("");
}

function renderPvpHud(payload) {
  if (!payload || !payload.limits) return;
  const { limits, nightly_decay: nightlyDecay, cooldowns } = payload;

  pvpResetAt.textContent = formatResetAt(limits.reset_at);

  const resetTime = new Date(limits.reset_at).getTime();
  if (Number.isFinite(resetTime) && resetTime < Date.now()) {
    setPvpStatus("Time sync issue detected.", true);
  } else {
    setPvpStatus("");
  }

  if (nightlyDecay && nightlyDecay > 0) {
    pvpBanner.textContent = `Nightly decay applied: -${nightlyDecay} prestige`;
    pvpBanner.classList.remove("hidden");
  } else {
    pvpBanner.textContent = "";
    pvpBanner.classList.add("hidden");
  }

  pvpAttacksRow.innerHTML = `Attacks: <strong>${limits.attacks_used}</strong> used / left <strong>${limits.attacks_left}</strong>`;
  pvpGainRow.innerHTML = `Prestige gain today: <strong>${limits.prestige_gain_today}</strong> / left <strong>${limits.prestige_gain_left}</strong>`;
  pvpLossRow.innerHTML = `Prestige loss today: <strong>${limits.prestige_loss_today}</strong> / protected left <strong>${limits.prestige_loss_left}</strong>`;

  const globalLeft =
    typeof cooldowns?.global_remaining_sec === "number"
      ? cooldowns.global_remaining_sec
      : secondsLeft(cooldowns?.global_available_at ?? null);
  const targetLeft = secondsLeft(cooldowns?.same_target_available_at ?? null);

  pvpGlobalCooldown.innerHTML = `Global cooldown: <strong>${formatDuration(globalLeft)}</strong>`;
  pvpTargetCooldown.innerHTML = `Same target cooldown: <strong>${formatDuration(targetLeft)}</strong>`;
}

async function refreshPvpHud() {
  try {
    const payload = await fetchPvPLimits();
    renderPvpHud(payload);
    setPvpStatus("");
  } catch (error) {
    setPvpStatus(`Disconnected: ${error.message}`, true);
  }
}

function startPvpHud() {
  if (pvpRefreshTimer) return;
  pvpRefreshBtn.disabled = false;
  refreshPvpHud();
  pvpRefreshTimer = setInterval(refreshPvpHud, 10000);
}

function stopPvpHud() {
  if (pvpRefreshTimer) {
    clearInterval(pvpRefreshTimer);
    pvpRefreshTimer = null;
  }
  pvpRefreshBtn.disabled = true;
  pvpResetAt.textContent = "--";
  pvpBanner.textContent = "";
  pvpBanner.classList.add("hidden");
  pvpAttacksRow.textContent = "Attacks: --";
  pvpGainRow.textContent = "Prestige gain: --";
  pvpLossRow.textContent = "Prestige loss: --";
  pvpGlobalCooldown.textContent = "Global cooldown: --";
  pvpTargetCooldown.textContent = "Same target cooldown: --";
  setPvpStatus("");
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
        rankStatus.textContent = `Result: ${result.result} (Δ${result.prestige.delta})`;
        if (result.limits) {
          renderPvpHud({
            limits: result.limits,
            cooldowns: result.cooldowns ?? null,
            nightly_decay: null,
          });
        }
        await refreshCity();
      } catch (error) {
        if (error?.status === 403 && error?.data?.error?.code === "INSUFFICIENT_ARMY") {
          rankStatus.textContent = "Train units in Barracks to attack.";
        } else {
          rankStatus.textContent = error?.data?.detail || error?.data?.message || "Attack failed";
        }
      }
    });

    row.appendChild(attackBtn);
    container.appendChild(row);
  });
}

function renderHistory(entries, append = false) {
  if (!append) {
    attackLog.innerHTML = "";
  }
  entries.forEach((entry) => {
    const isAttacker = entry.attacker_id === currentUser?.id;
    const opponent = isAttacker ? entry.defender_email : entry.attacker_email;
    const delta = entry.prestige_delta;
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

function updateHistoryLoadMore() {
  if (!historyLoadMore) {
    return;
  }
  if (pvpLogNextCursor) {
    historyLoadMore.disabled = false;
    historyLoadMore.textContent = "Load more";
  } else {
    historyLoadMore.disabled = true;
    historyLoadMore.textContent = "No more";
  }
}

async function refreshHistory() {
  if (pvpLogLoading) {
    return;
  }
  pvpLogLoading = true;
  historyStatus.textContent = "Loading...";
  try {
    const response = await fetchAttackLog(20);
    const items = response.items || [];
    pvpLogSeen = new Set(items.map((item) => item.battle_id));
    pvpLogNextCursor = response.next_cursor || null;
    renderHistory(items, false);
    updateHistoryLoadMore();
    historyStatus.textContent = "";
  } catch (error) {
    historyStatus.textContent = error.message;
  } finally {
    pvpLogLoading = false;
  }
}

async function loadMoreHistory() {
  if (pvpLogLoading || !pvpLogNextCursor) {
    return;
  }
  pvpLogLoading = true;
  historyStatus.textContent = "Loading...";
  try {
    const response = await fetchAttackLog(20, pvpLogNextCursor);
    const items = response.items || [];
    const freshItems = items.filter((item) => !pvpLogSeen.has(item.battle_id));
    freshItems.forEach((item) => pvpLogSeen.add(item.battle_id));
    pvpLogNextCursor = response.next_cursor || null;
    renderHistory(freshItems, true);
    updateHistoryLoadMore();
    historyStatus.textContent = "";
  } catch (error) {
    historyStatus.textContent = error.message;
  } finally {
    pvpLogLoading = false;
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
    startPvpHud();
    startArmyHud();
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
  pvpLogNextCursor = null;
  pvpLogSeen = new Set();
  updateHistoryLoadMore();
  setMessage("Logged out.");
  setBuildStatus("");
  collectBtn.disabled = true;
  stopPvpHud();
  stopArmyHud();
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
} else {
  stopPvpHud();
  stopArmyHud();
}

pvpRefreshBtn.addEventListener("click", () => {
  refreshPvpHud();
});

armyRefreshBtn.addEventListener("click", () => {
  refreshArmy();
});

queueRefreshBtn.addEventListener("click", () => {
  refreshQueue();
});

trainSubmit.addEventListener("click", () => {
  trainUnits();
});

claimSubmit.addEventListener("click", () => {
  claimUnits();
});

if (historyLoadMore) {
  historyLoadMore.addEventListener("click", () => {
    loadMoreHistory();
  });
  updateHistoryLoadMore();
}
