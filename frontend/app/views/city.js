/**
 * City view - city grid, resources, building
 */

import { cityApi, statsApi, authApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";
import { showToast } from "../components/toast.js";

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

  // Setup build interaction
  const buildingType = document.getElementById("buildingType");
  const buildStatus = document.getElementById("buildStatus");
  buildStatus.textContent = "Ready to build.";
  buildStatus.style.color = "#9fb0c9";
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

async function handleBuild(x, y, existing) {
  const buildStatus = document.getElementById("buildStatus");

  if (existing) {
    buildStatus.textContent = "Tile already occupied.";
    buildStatus.style.color = "#ff8c6a";
    return;
  }

  const buildingType = document.getElementById("buildingType");
  const type = buildingType.value;

  if (!type) {
    buildStatus.textContent = "Select a building type first.";
    buildStatus.style.color = "#ff8c6a";
    return;
  }

  try {
    const token = getToken();
    const updated = await cityApi.build(token, type, x, y);
    const stats = await statsApi.fetch(token);

    state.setState({ city: updated });
    renderStats(updated);
    renderGrid(updated);
    renderCombat(stats);

    buildStatus.textContent = `Placed ${type} at ${x},${y}.`;
    buildStatus.style.color = "#9fb0c9";
  } catch (error) {
    buildStatus.textContent = error.message || "Build failed";
    buildStatus.style.color = "#ff8c6a";
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
