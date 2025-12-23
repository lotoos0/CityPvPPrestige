/**
 * City view - city grid, resources, building
 */

import { cityApi, statsApi, authApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";
import { showToast } from "../components/toast.js";

let selectedTile = null;
let buildingMap = new Map();

export async function cityView() {
  const token = getToken();
  if (!token) return;

  // Hide auth section, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "block";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "none";

  // Load city data
  await refreshCity();

  // Setup collect button
  const collectBtn = document.getElementById("collectBtn");
  collectBtn.disabled = false;
  collectBtn.onclick = handleCollect;

  const buildStatus = document.getElementById("buildStatus");
  buildStatus.textContent = "";
  buildStatus.style.color = "#9fb0c9";

  const gridEl = document.getElementById("grid");
  gridEl.onclick = onGridClick;

  renderTilePanel();
}

async function refreshCity() {
  const token = getToken();
  try {
    const [city, stats, user] = await Promise.all([
      cityApi.fetch(token),
      statsApi.fetch(token),
      authApi.me(token),
    ]);

    state.setState({ city, user });
    renderStats(city);
    renderCombat(stats);
    renderGrid(city);
    renderTilePanel();
  } catch (error) {
    showToast(error.message || "Failed to load city", true);
  }
}

function renderStats(city) {
  const resourceStats = document.getElementById("resourceStats");
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
  const combatStats = document.getElementById("combatStats");
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
  const gridEl = document.getElementById("grid");
  gridEl.innerHTML = "";

  buildingMap = new Map();
  city.buildings.forEach((b) => {
    buildingMap.set(`${b.x}:${b.y}`, b);
  });

  for (let y = 0; y < city.grid_size; y += 1) {
    for (let x = 0; x < city.grid_size; x += 1) {
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile";
      tile.dataset.x = x;
      tile.dataset.y = y;

      const building = buildingMap.get(`${x}:${y}`);
      if (building) {
        tile.classList.add("filled");
        tile.textContent = `${building.type.replace("_", " ").toUpperCase()} L${building.level}`;
      } else {
        tile.textContent = `${x},${y}`;
      }

      if (selectedTile && selectedTile.x === x && selectedTile.y === y) {
        tile.classList.add("selected");
      }
      gridEl.appendChild(tile);
    }
  }
}

function onGridClick(event) {
  const tile = event.target.closest(".tile");
  if (!tile) return;

  const x = Number(tile.dataset.x);
  const y = Number(tile.dataset.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;

  selectTile(x, y);
}

function selectTile(x, y) {
  const gridEl = document.getElementById("grid");
  const previous = gridEl.querySelector(".tile.selected");
  if (previous) {
    previous.classList.remove("selected");
  }

  const tile = gridEl.querySelector(`.tile[data-x="${x}"][data-y="${y}"]`);
  if (tile) {
    tile.classList.add("selected");
  }

  selectedTile = { x, y };
  renderTilePanel();
}

function renderTilePanel() {
  const title = document.getElementById("tilePanelTitle");
  const body = document.getElementById("tilePanelBody");

  if (!selectedTile) {
    title.textContent = "Select a tile.";
    body.textContent = "";
    return;
  }

  const key = `${selectedTile.x}:${selectedTile.y}`;
  const building = buildingMap.get(key);
  title.textContent = `Tile (${selectedTile.x}, ${selectedTile.y})`;
  if (building) {
    const label = building.type.replace("_", " ").toUpperCase();
    body.textContent = `Occupied: ${label} L${building.level}`;
  } else {
    body.textContent = "Empty tile.";
  }
}

async function handleCollect() {
  const buildStatus = document.getElementById("buildStatus");
  try {
    const token = getToken();
    const updated = await cityApi.collect(token);
    const stats = await statsApi.fetch(token);

    state.setState({ city: updated });
    renderStats(updated);
    renderCombat(stats);

    buildStatus.textContent = "Collected resources.";
    buildStatus.style.color = "#9fb0c9";
  } catch (error) {
    buildStatus.textContent = error.message || "Collect failed";
    buildStatus.style.color = "#ff8c6a";
  }
}
