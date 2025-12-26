/**
 * City view - city grid, resources, building
 */

import { cityApi, statsApi, authApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";
import { showToast } from "../components/toast.js";

let selectedTile = null;
let buildingMap = new Map();
let buildingCatalog = [];
let buildingCatalogByType = new Map();
let selectedBuildType = "";
let catalogLoaded = false;
const BASE_GOLD_CAP = 200;
const TILE_WIDTH = 80;
const TILE_HEIGHT = 40;
let showDebugLabels = false;

export async function cityView() {
  const token = getToken();
  if (!token) return;

  // Hide auth section, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "block";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "none";

  await ensureCatalog(token);
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

  const debugToggle = document.getElementById("toggleDebugLabels");
  if (debugToggle) {
    debugToggle.checked = showDebugLabels;
    debugToggle.onchange = () => {
      showDebugLabels = debugToggle.checked;
      renderGrid(state.city);
      renderTilePanel();
    };
  }

  renderTilePanel();
}

async function ensureCatalog(token) {
  if (catalogLoaded) return;
  try {
    const payload = await cityApi.catalog(token);
    buildingCatalog = payload.items || [];
    buildingCatalogByType = new Map(buildingCatalog.map((item) => [item.type, item]));
  } catch (error) {
    showToast("Failed to load building catalog.", true);
    buildingCatalog = [];
    buildingCatalogByType = new Map();
  } finally {
    catalogLoaded = true;
  }
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
    return city;
  } catch (error) {
    showToast(error.message || "Failed to load city", true);
  }
  return null;
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

  updateTopbarStats(city);
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
  if (!city) return;
  const gridEl = document.getElementById("grid");
  gridEl.innerHTML = "";
  gridEl.style.width = `${city.grid_size * TILE_WIDTH}px`;
  gridEl.style.height = `${city.grid_size * TILE_HEIGHT}px`;
  gridEl.classList.toggle("debug", showDebugLabels);

  buildingMap = new Map();
  city.buildings.forEach((b) => {
    buildingMap.set(`${b.x}:${b.y}`, b);
  });

  const originX = (city.grid_size - 1) * (TILE_WIDTH / 2);

  for (let y = 0; y < city.grid_size; y += 1) {
    for (let x = 0; x < city.grid_size; x += 1) {
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = "tile";
      tile.dataset.x = x;
      tile.dataset.y = y;
      const isoX = (x - y) * (TILE_WIDTH / 2) + originX;
      const isoY = (x + y) * (TILE_HEIGHT / 2);
      tile.style.left = `${isoX}px`;
      tile.style.top = `${isoY}px`;

      const building = buildingMap.get(`${x}:${y}`);
      if (building) {
        tile.classList.add("filled");
        if (showDebugLabels) {
          const label = document.createElement("span");
          label.className = "tile-label";
          label.textContent = building.type.replace("_", " ").toUpperCase();
          tile.appendChild(label);
        }

        const levelBadge = document.createElement("span");
        levelBadge.className = "tile-badge level";
        levelBadge.textContent = `L${building.level}`;

        tile.appendChild(levelBadge);

        if (building.level < 3 && state.city) {
          const cost = getBuildCost(building.type, building.level + 1);
          if (Number.isFinite(cost) && state.city.gold >= cost) {
            const upgradeBadge = document.createElement("span");
            upgradeBadge.className = "tile-badge upgrade";
            upgradeBadge.textContent = "▲";
            tile.appendChild(upgradeBadge);
          }
        }
      } else {
        if (showDebugLabels) {
          const coords = document.createElement("span");
          coords.className = "tile-coords";
          coords.textContent = `${x},${y}`;
          tile.appendChild(coords);
        }
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

  if (!state.city) {
    title.textContent = `Tile (${selectedTile.x}, ${selectedTile.y})`;
    body.textContent = "Loading city...";
    return;
  }

  const key = `${selectedTile.x}:${selectedTile.y}`;
  const building = buildingMap.get(key);
  title.textContent = `Tile (${selectedTile.x}, ${selectedTile.y})`;
  body.innerHTML = "";

  if (!catalogLoaded) {
    body.textContent = "Loading catalog...";
    return;
  }

  if (building) {
    renderUpgradePanel(body, building);
    return;
  }

  renderBuildPanel(body);
}

function updateTopbarStats(city) {
  const gold = document.getElementById("topbarGold");
  const goldCap = document.getElementById("topbarGoldCap");
  const pop = document.getElementById("topbarPop");
  const power = document.getElementById("topbarPower");
  const prestige = document.getElementById("topbarPrestige");
  const goldPill = gold?.closest(".resource-pill");

  if (gold) gold.textContent = city.gold;
  if (goldCap) goldCap.textContent = getGoldCap(city);
  if (pop) pop.textContent = city.pop;
  if (power) power.textContent = city.power;
  if (prestige) prestige.textContent = city.prestige;

  if (goldPill) {
    goldPill.dataset.value = city.gold;
  }
}

function getGoldCap(city) {
  if (!catalogLoaded) return "--";
  let bonus = 0;
  city.buildings.forEach((building) => {
    if (building.type !== "storage") return;
    const item = buildingCatalogByType.get(building.type);
    const levelMeta = item?.levels.find((entry) => entry.level === building.level);
    bonus += levelMeta?.effects?.gold_cap || 0;
  });
  return BASE_GOLD_CAP + bonus;
}
function renderBuildPanel(container) {
  const info = document.createElement("div");
  info.textContent = "Empty tile.";
  container.appendChild(info);

  const selectLabel = document.createElement("label");
  selectLabel.className = "label";
  selectLabel.textContent = "Building type";

  const select = document.createElement("select");
  select.className = "input";
  select.innerHTML = "<option value=\"\">Select building</option>";

  buildingCatalog.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.type;
    option.textContent = item.display_name;
    select.appendChild(option);
  });

  select.value = selectedBuildType;
  select.addEventListener("change", () => {
    selectedBuildType = select.value;
    renderTilePanel();
  });

  const selectRow = document.createElement("div");
  selectRow.appendChild(selectLabel);
  selectRow.appendChild(select);
  container.appendChild(selectRow);

  const costRow = document.createElement("div");
  costRow.className = "row";
  const costText = document.createElement("span");
  const cost = getBuildCost(selectedBuildType, 1);
  if (selectedBuildType && Number.isFinite(cost)) {
    costText.textContent = `Cost: ${cost} gold`;
  } else {
    costText.textContent = "Cost: select a building";
  }
  costRow.appendChild(costText);
  container.appendChild(costRow);

  const buildBtn = document.createElement("button");
  buildBtn.className = "btn";
  buildBtn.textContent = "Build";
  buildBtn.disabled =
    !selectedBuildType ||
    !Number.isFinite(cost) ||
    state.city.gold < cost;
  buildBtn.addEventListener("click", () => handleBuild());
  container.appendChild(buildBtn);
}

function renderUpgradePanel(container, building) {
  const catalogItem = buildingCatalogByType.get(building.type);
  const name = catalogItem?.display_name || building.type.replace("_", " ").toUpperCase();
  const info = document.createElement("div");
  info.textContent = `Occupied: ${name} L${building.level}`;
  container.appendChild(info);

  if (building.level >= 3) {
    const maxLabel = document.createElement("div");
    maxLabel.className = "status";
    maxLabel.textContent = "Max level.";
    container.appendChild(maxLabel);
    const upgradeBtn = document.createElement("button");
    upgradeBtn.className = "btn upgrade-btn";
    upgradeBtn.textContent = "Upgrade";
    upgradeBtn.disabled = true;
    upgradeBtn.title = "Max level reached";
    container.appendChild(upgradeBtn);
    return;
  }

  const nextLevel = building.level + 1;
  const cost = getBuildCost(building.type, nextLevel);
  const gold = state.city?.gold ?? 0;
  const canAfford = Number.isFinite(cost) && gold >= cost;
  const costRow = document.createElement("div");
  costRow.className = "row";
  const costText = document.createElement("span");
  costText.textContent = Number.isFinite(cost) ? `Upgrade cost: ${cost} gold` : "Upgrade cost: unknown";
  costRow.appendChild(costText);
  container.appendChild(costRow);

  const upgradeBtn = document.createElement("button");
  upgradeBtn.className = "btn upgrade-btn";
  upgradeBtn.textContent = `Upgrade to L${nextLevel}`;
  upgradeBtn.disabled = !canAfford;
  if (!upgradeBtn.disabled && Number.isFinite(cost)) {
    upgradeBtn.title = "";
  } else if (!Number.isFinite(cost)) {
    upgradeBtn.title = "Upgrade cost unknown";
  } else {
    const missing = cost - gold;
    upgradeBtn.title = `Need ${missing} gold`;
  }
  upgradeBtn.addEventListener("click", () => handleUpgrade(building));
  container.appendChild(upgradeBtn);
}

function getBuildCost(type, level) {
  if (!type) return null;
  const item = buildingCatalogByType.get(type);
  if (!item) return null;
  const levelMeta = item.levels.find((entry) => entry.level === level);
  return levelMeta ? levelMeta.cost_gold : null;
}

function getErrorMessage(error) {
  const code = error?.data?.error?.code;
  if (!code) return error?.data?.detail || "Action failed";
  const map = {
    INSUFFICIENT_GOLD: "Not enough gold.",
    TILE_OCCUPIED: "Tile already occupied.",
    MAX_LEVEL: "Already max level.",
    BUILDING_TYPE_NOT_ALLOWED: "Not allowed in MVP.",
  };
  return map[code] || "Action failed.";
}

async function handleBuild() {
  if (!selectedTile || !selectedBuildType) return;
  try {
    const token = getToken();
    await cityApi.build(token, selectedBuildType, selectedTile.x, selectedTile.y);
    const catalogItem = buildingCatalogByType.get(selectedBuildType);
    const name = catalogItem?.display_name || selectedBuildType;
    showToast(`Built ${name}`);
    await refreshCity();
  } catch (error) {
    showToast(getErrorMessage(error), true);
  }
}

async function handleUpgrade(building) {
  if (!selectedTile || !building) return;
  try {
    const token = getToken();
    await cityApi.upgrade(token, selectedTile.x, selectedTile.y);
    const catalogItem = buildingCatalogByType.get(building.type);
    const name = catalogItem?.display_name || building.type;
    showToast(`Upgraded ${name} to L${building.level + 1}`);
    await refreshCity();
  } catch (error) {
    showToast(getErrorMessage(error), true);
  }
}

async function handleCollect() {
  const buildStatus = document.getElementById("buildStatus");
  try {
    const beforeGold = state.city?.gold ?? 0;
    const updated = await refreshCity();
    const afterGold = updated?.gold ?? beforeGold;
    const delta = afterGold - beforeGold;

    if (delta > 0) {
      showGoldDelta(delta);
      showToast(`Collected +${delta} gold`);
      buildStatus.textContent = `Collected +${delta} gold.`;
      buildStatus.style.color = "#9fb0c9";
    } else {
      showToast("No resources ready.");
      buildStatus.textContent = "No resources ready.";
      buildStatus.style.color = "#9fb0c9";
    }
  } catch (error) {
    buildStatus.textContent = error.message || "Collect failed";
    buildStatus.style.color = "#ff8c6a";
  }
}

function showGoldDelta(amount) {
  const gold = document.getElementById("topbarGold");
  const pill = gold?.closest(".resource-pill");
  if (!pill) return;

  const delta = document.createElement("span");
  delta.className = "gold-delta";
  delta.textContent = `+${amount}`;
  pill.appendChild(delta);
  delta.addEventListener("animationend", () => {
    delta.remove();
  });
}
