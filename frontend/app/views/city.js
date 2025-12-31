/**
 * City view - city grid, resources, building
 */

import { cityApi, statsApi, authApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";
import { showToast } from "../components/toast.js";
import { SPRITE } from "../sprite_config.js";

let selectedTile = null;
let buildingMap = new Map();
let occupancyMap = new Map();
let buildingCatalog = [];
let buildingCatalogByType = new Map();
let selectedBuildType = "";
let catalogLoaded = false;
let storedBuildings = [];
const BASE_GOLD_CAP = 200;
const TILE_WIDTH = 128;
const TILE_HEIGHT = 64;
let showDebugLabels = false;
let gridOffset = { x: 0, y: 0 };
let dragging = false;
let dragStart = { x: 0, y: 0 };
let dragOrigin = { x: 0, y: 0 };
let dragMoved = false;
let lastDragEndAt = 0;
let lastSelectedFootprint = null;
let placing = null;
let moving = null;
let ghostTile = null;
let placementListenersBound = false;
let ghostEl = null;
let topbarHeightBound = false;
let lastPointer = null;

export async function cityView() {
  const token = getToken();
  if (!token) return;

  // Hide auth section, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "block";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "none";
  document.body.classList.add("map-first");

  const hud = document.querySelector(".hud");
  const hudToggle = document.getElementById("hudToggle");
  if (hud && hudToggle && !hudToggle.dataset.bound) {
    const collapsed = localStorage.getItem("hudCollapsed") === "1";
    hud.classList.toggle("hud--collapsed", collapsed);
    hudToggle.setAttribute("aria-expanded", String(!collapsed));
    hudToggle.textContent = collapsed ? "»" : "«";
    hudToggle.dataset.bound = "1";
    hudToggle.onclick = () => {
      const nowCollapsed = hud.classList.toggle("hud--collapsed");
      hudToggle.setAttribute("aria-expanded", String(!nowCollapsed));
      hudToggle.textContent = nowCollapsed ? "»" : "«";
      localStorage.setItem("hudCollapsed", nowCollapsed ? "1" : "0");
    };
  }

  syncTopbarHeight();
  if (!topbarHeightBound) {
    topbarHeightBound = true;
    window.addEventListener("resize", syncTopbarHeight);
  }

  // Refresh catalog to pick up footprint changes.
  catalogLoaded = false;
  buildingCatalog = [];
  buildingCatalogByType = new Map();

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
  const viewportEl = document.getElementById("gridViewport");
  if (viewportEl) {
    viewportEl.onpointerdown = onGridPointerDown;
    viewportEl.onpointermove = onGridPointerMove;
    if (!placementListenersBound) {
      placementListenersBound = true;
      viewportEl.addEventListener("contextmenu", (event) => {
        if (!getActivePlacement()) return;
        event.preventDefault();
        stopPlacementMode();
      });
      window.addEventListener("keydown", (event) => {
        const active = getActivePlacement();
        if (event.key === "Escape" && active) {
          stopPlacementMode();
          return;
        }
        if ((event.key === "r" || event.key === "R") && active) {
          if (isTypingTarget(event.target)) return;
          if (active.size.w === active.size.h) return;
          active.rotated = !active.rotated;
          let seed = ghostTile;
          if (!seed && lastPointer) {
            seed = getTileFromPointIso(lastPointer.x, lastPointer.y);
          }
          if (seed) {
            const status = getPlacementStatus(
              seed.x,
              seed.y,
              getPlacementSize(active),
              active.mode === "move" ? active.id : null,
              active.mode === "move",
            );
            ghostTile = { x: seed.x, y: seed.y, valid: status.ok, reason: status.reason };
            updatePlacementCursor(status.ok);
          } else {
            ghostTile = null;
            updatePlacementCursor(null);
          }
          renderGhost();
          renderTilePanel();
          return;
        }
        if (event.key !== "Enter" || !active) return;
        if (isTypingTarget(event.target)) return;
        if (!ghostTile || !ghostTile.valid) return;
        event.preventDefault();
        attemptPlaceAt(ghostTile.x, ghostTile.y);
      });
    }
  }

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

function syncTopbarHeight() {
  const topbar = document.querySelector(".topbar");
  if (!topbar) return;
  const height = topbar.getBoundingClientRect().height;
  document.documentElement.style.setProperty("--topbar-h", `${height}px`);
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
    const [city, stats, user, stored] = await Promise.all([
      cityApi.fetch(token),
      statsApi.fetch(token),
      authApi.me(token),
      cityApi.stored(token),
    ]);

    state.setState({ city, user });
    storedBuildings = stored?.items || [];
    renderStats(city);
    renderCombat(stats);
    renderGrid(city);
    renderTilePanel();
    renderInventory();
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
  ghostEl = null;
  gridEl.style.width = `${city.grid_size * TILE_WIDTH}px`;
  gridEl.style.height = `${city.grid_size * TILE_HEIGHT}px`;
  gridEl.classList.toggle("debug", showDebugLabels);
  gridEl.style.transform = `translate(${gridOffset.x}px, ${gridOffset.y}px)`;

  buildingMap = new Map();
  occupancyMap = new Map();
  city.buildings.forEach((b) => {
    buildingMap.set(`${b.x}:${b.y}`, b);
  });
  city.buildings.forEach((b) => {
    const size = getBuildingFootprint(b);
    for (let dx = 0; dx < size.w; dx += 1) {
      for (let dy = 0; dy < size.h; dy += 1) {
        const tileX = b.x + dx;
        const tileY = b.y + dy;
        const key = `${tileX}:${tileY}`;
        occupancyMap.set(key, {
          buildingId: b.id,
          originX: b.x,
          originY: b.y,
          type: b.type,
          level: b.level,
          size,
          isOrigin: dx === 0 && dy === 0,
        });
      }
    }
  });

  lastSelectedFootprint = getSelectedFootprint();
  const selectedKeys = new Set();
  let selectedOriginKey = null;
  if (lastSelectedFootprint) {
    const { originX: selX, originY: selY, size } = lastSelectedFootprint;
    for (let dx = 0; dx < size.w; dx += 1) {
      for (let dy = 0; dy < size.h; dy += 1) {
        const tileX = selX + dx;
        const tileY = selY + dy;
        if (
          tileX < 0
          || tileY < 0
          || tileX >= city.grid_size
          || tileY >= city.grid_size
        ) {
          continue;
        }
        selectedKeys.add(`${tileX}:${tileY}`);
      }
    }
    selectedOriginKey = `${selX}:${selY}`;
  }

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
      tile.style.setProperty("--tile-w", `${TILE_WIDTH}px`);
      tile.style.setProperty("--tile-h", `${TILE_HEIGHT}px`);
      tile.classList.toggle("debug-ground", showDebugLabels);

      const occupancy = occupancyMap.get(`${x}:${y}`);
      let tileZ = x + y;
      if (occupancy?.isOrigin) {
        tileZ += (occupancy.size.w - 1) + (occupancy.size.h - 1);
      }
      tile.style.zIndex = String(1000 + tileZ);
      if (occupancy) {
        tile.classList.add("occupied");
        tile.dataset.occupied = "1";
        tile.dataset.originX = String(occupancy.originX);
        tile.dataset.originY = String(occupancy.originY);
        tile.dataset.btype = occupancy.type;
        tile.dataset.blevel = String(occupancy.level);
        if (!occupancy.isOrigin) {
          tile.classList.add("blocked");
        }
      }

      const key = `${x}:${y}`;
      if (selectedKeys.has(key)) {
        tile.classList.add("footprint");
        if (lastSelectedFootprint?.isPreview) {
          tile.classList.add("footprint-preview");
        }
      }
      if (selectedOriginKey && key === selectedOriginKey) {
        tile.classList.add("footprint-origin");
      }

      const building = occupancy?.isOrigin
        ? buildingMap.get(`${occupancy.originX}:${occupancy.originY}`)
        : null;
      if (building) {
        tile.classList.add("filled");
        if (occupancy.size.w > 1 || occupancy.size.h > 1) {
          const plate = createPlate(occupancy.size, false, "center");
          if (moving && building.id === moving.id) {
            plate.classList.add("moving-source-plate");
          }
          tile.appendChild(plate);
        }
        const sprite = getSpritePath(building.type, building.level);
        if (sprite) {
          const shadow = document.createElement("div");
          shadow.className = "shadow";
          tile.appendChild(shadow);

          const img = document.createElement("img");
          img.className = "building";
          if (moving && building.id === moving.id) {
            img.classList.add("moving-source");
          }
          img.src = sprite;
          img.alt = `${building.type} L${building.level}`;
          const sprW = Math.round(SPRITE.size * SPRITE.scale);
          const sprH = Math.round(SPRITE.size * SPRITE.scale);
          img.width = sprW;
          img.height = sprH;
          img.style.bottom = "0px";
          tile.appendChild(img);
        }
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
        if (
          lastSelectedFootprint?.isPreview
          && selectedOriginKey === key
          && (lastSelectedFootprint.size.w > 1 || lastSelectedFootprint.size.h > 1)
        ) {
          tile.appendChild(createPlate(lastSelectedFootprint.size, true, "center"));
        }
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

  if (placing && ghostTile) {
    renderGhost();
  }
}

function onGridClick(event) {
  if (Date.now() - lastDragEndAt < 120) {
    return;
  }
  if (getActivePlacement()) {
    const tile = getTileFromPointIso(event.clientX, event.clientY);
    if (!tile) return;
    attemptPlaceAt(tile.x, tile.y);
    return;
  }
  const tile = event.target.closest(".tile");
  if (!tile) return;

  const x = Number(tile.dataset.x);
  const y = Number(tile.dataset.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return;

  selectTile(x, y);
}

function onGridPointerDown(event) {
  if (event.button !== 0) return;
  const viewport = event.currentTarget;
  dragging = true;
  dragMoved = false;
  dragStart = { x: event.clientX, y: event.clientY };
  dragOrigin = { x: gridOffset.x, y: gridOffset.y };
  viewport.classList.add("dragging");

  const onMove = (moveEvent) => {
    if (!dragging) return;
    const dx = moveEvent.clientX - dragStart.x;
    const dy = moveEvent.clientY - dragStart.y;
    if (!dragMoved && Math.hypot(dx, dy) > 4) {
      dragMoved = true;
    }
    gridOffset = { x: dragOrigin.x + dx, y: dragOrigin.y + dy };
    const gridEl = document.getElementById("grid");
    if (gridEl) {
      gridEl.style.transform = `translate(${gridOffset.x}px, ${gridOffset.y}px)`;
    }
  };

  const onUp = (upEvent) => {
    dragging = false;
    viewport.classList.remove("dragging");
    if (dragMoved) {
      lastDragEndAt = Date.now();
    } else {
      selectTileFromPoint(upEvent.clientX, upEvent.clientY);
      lastDragEndAt = Date.now();
    }
    viewport.removeEventListener("pointermove", onMove);
    viewport.removeEventListener("pointerup", onUp);
    viewport.removeEventListener("pointercancel", onUp);
  };

  viewport.addEventListener("pointermove", onMove);
  viewport.addEventListener("pointerup", onUp);
  viewport.addEventListener("pointercancel", onUp);
}

function selectTileFromPoint(clientX, clientY) {
  if (getActivePlacement()) {
    const tile = getTileFromPointIso(clientX, clientY);
    if (!tile) return;
    attemptPlaceAt(tile.x, tile.y);
    return;
  }
  const domTile = getTileFromPoint(clientX, clientY);
  if (!domTile) return;
  selectTile(domTile.x, domTile.y);
}

function onGridPointerMove(event) {
  lastPointer = { x: event.clientX, y: event.clientY };
  const active = getActivePlacement();
  if (!active || dragging) return;
  const tile = getTileFromPointIso(event.clientX, event.clientY);
  if (!tile) {
    hideGhost();
    updatePlacementCursor(null);
    return;
  }
  const status = getPlacementStatus(
    tile.x,
    tile.y,
    getPlacementSize(active),
    active.mode === "move" ? active.id : null,
    active.mode === "move" || Boolean(active.sourceStoredId),
  );
  ghostTile = { x: tile.x, y: tile.y, valid: status.ok, reason: status.reason };
  updatePlacementCursor(status.ok);
  renderGhost();
  renderTilePanel();
}

function renderInventory() {
  const list = document.getElementById("inventoryList");
  if (!list) return;
  list.innerHTML = "";
  if (!storedBuildings.length) {
    list.textContent = "No stored buildings.";
    return;
  }
  storedBuildings.forEach((item) => {
    const row = document.createElement("div");
    row.className = "inventory-item";
    const label = document.createElement("div");
    label.textContent = `${item.type.replace("_", " ").toUpperCase()} L${item.level}`;
    const displaySize =
      item.rotation === 90 && item.size.w !== item.size.h
        ? { w: item.size.h, h: item.size.w }
        : item.size;
    const meta = document.createElement("div");
    meta.className = "inventory-meta";
    meta.textContent = `${displaySize.w}x${displaySize.h}`;
    const actions = document.createElement("div");
    const placeBtn = document.createElement("button");
    placeBtn.className = "btn ghost";
    placeBtn.type = "button";
    placeBtn.textContent = "Place";
    placeBtn.disabled = Boolean(getActivePlacement());
    placeBtn.addEventListener("click", () => startPlacingFromStored(item));
    actions.appendChild(placeBtn);
    row.appendChild(label);
    row.appendChild(meta);
    row.appendChild(actions);
    list.appendChild(row);
  });
}

function getTileFromPoint(clientX, clientY) {
  const ghost = ghostEl;
  if (ghost) ghost.style.display = "none";
  const target = document.elementFromPoint(clientX, clientY);
  if (ghost) ghost.style.display = "";
  const tile = target?.closest?.(".tile");
  if (!tile) return null;
  const x = Number(tile.dataset.x);
  const y = Number(tile.dataset.y);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return { x, y };
}

function getTileFromPointIso(clientX, clientY) {
  const city = state.city;
  const gridEl = document.getElementById("grid");
  const viewportEl = document.getElementById("gridViewport");
  if (!city || !gridEl || !viewportEl) return null;
  const rect = viewportEl.getBoundingClientRect();
  const localX = clientX - rect.left - gridOffset.x;
  const localY = clientY - rect.top - gridOffset.y;
  if (localX < 0 || localY < 0 || localX > gridEl.clientWidth || localY > gridEl.clientHeight) {
    return null;
  }
  const originX = (city.grid_size - 1) * (TILE_WIDTH / 2);
  const halfW = TILE_WIDTH / 2;
  const halfH = TILE_HEIGHT / 2;
  const gx = (localY / halfH + (localX - originX) / halfW) / 2;
  const gy = (localY / halfH - (localX - originX) / halfW) / 2;
  const x = Math.round(gx);
  const y = Math.round(gy);
  if (x < 0 || y < 0 || x >= city.grid_size || y >= city.grid_size) {
    return null;
  }
  return { x, y };
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

function focusTile(x, y) {
  selectTile(x, y);
  panToTile(x, y);
}

function panToTile(x, y) {
  const city = state.city;
  const gridEl = document.getElementById("grid");
  const viewportEl = document.getElementById("gridViewport");
  if (!city || !gridEl || !viewportEl) return;

  const originX = (city.grid_size - 1) * (TILE_WIDTH / 2);
  const isoX = (x - y) * (TILE_WIDTH / 2) + originX;
  const isoY = (x + y) * (TILE_HEIGHT / 2);
  const targetX = (viewportEl.clientWidth / 2) - isoX;
  const targetY = (viewportEl.clientHeight / 2) - isoY;
  gridOffset = { x: targetX, y: targetY };
  gridEl.style.transform = `translate(${gridOffset.x}px, ${gridOffset.y}px)`;
}

function renderTilePanel() {
  const title = document.getElementById("tilePanelTitle");
  const body = document.getElementById("tilePanelBody");

  if (moving) {
    const catalogItem = buildingCatalogByType.get(moving.type);
    const name = catalogItem?.display_name || moving.type.replace("_", " ").toUpperCase();
    title.textContent = "Moving";
    body.innerHTML = "";
    const placementSize = getPlacementSize(moving);

    const mode = document.createElement("div");
    mode.className = "status";
    mode.textContent = `Moving: ${name} L${moving.level} (${placementSize.w}x${placementSize.h})`;
    body.appendChild(mode);

    const rotation = document.createElement("div");
    rotation.className = "status";
    rotation.textContent = `Rotation: ${moving.rotated ? "90°" : "0°"} (R)`;
    body.appendChild(rotation);

    const hint = document.createElement("div");
    hint.className = "status";
    hint.textContent = "LMB place · RMB/ESC cancel";
    body.appendChild(hint);

    const actions = document.createElement("div");
    actions.className = "row";
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn ghost";
    cancelBtn.type = "button";
    cancelBtn.textContent = "Cancel move";
    cancelBtn.addEventListener("click", stopMoving);
    actions.appendChild(cancelBtn);
    body.appendChild(actions);

    if (ghostTile && !ghostTile.valid) {
      const reason = document.createElement("div");
      reason.className = "status status-error";
      reason.textContent = ghostTile.reason || "Cannot place here.";
      body.appendChild(reason);
    }
    return;
  }

  if (placing) {
    const catalogItem = buildingCatalogByType.get(placing.type);
    const name = catalogItem?.display_name || placing.type.replace("_", " ").toUpperCase();
    title.textContent = "Placing";
    body.innerHTML = "";
    const placementSize = getPlacementSize();
    const placementLabel = placing.sourceStoredId ? "stored" : "new";

    const mode = document.createElement("div");
    mode.className = "status";
    mode.textContent = `Placing: ${name} (${placementSize.w}x${placementSize.h}) · ${placementLabel}`;
    body.appendChild(mode);

    const rotation = document.createElement("div");
    rotation.className = "status";
    rotation.textContent = `Rotation: ${placing.rotated ? "90°" : "0°"} (R)`;
    body.appendChild(rotation);

    const hint = document.createElement("div");
    hint.className = "status";
    hint.textContent = "LMB place · RMB/ESC cancel";
    body.appendChild(hint);

    const actions = document.createElement("div");
    actions.className = "row";
    const cancelBtn = document.createElement("button");
    cancelBtn.className = "btn ghost";
    cancelBtn.textContent = "Cancel placement";
    cancelBtn.type = "button";
    cancelBtn.disabled = false;
    cancelBtn.addEventListener("click", stopPlacing);
    actions.appendChild(cancelBtn);
    body.appendChild(actions);

    if (ghostTile && !ghostTile.valid) {
      const reason = document.createElement("div");
      reason.className = "status status-error";
      reason.textContent = ghostTile.reason || "Cannot place here.";
      body.appendChild(reason);
    }
    return;
  }

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
  const occupancy = occupancyMap.get(key);
  title.textContent = `Tile (${selectedTile.x}, ${selectedTile.y})`;
  body.innerHTML = "";

  if (!catalogLoaded) {
    body.textContent = "Loading catalog...";
    return;
  }

  if (occupancy) {
    if (occupancy.isOrigin) {
      const originBuilding = buildingMap.get(`${occupancy.originX}:${occupancy.originY}`);
      if (originBuilding) {
        renderUpgradePanel(body, originBuilding);
        return;
      }
    }
    renderOccupiedPanel(body, occupancy);
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

function getSpritePath(type, level) {
  const map = {
    town_hall: "Town_Hall",
    gold_mine: "Gold_mine",
    house: "House",
    barracks: "Barracks",
    wall: "Wall",
    tower: "Tower",
    storage: "Storage",
  };
  const name = map[type];
  if (!name) return null;
  return `assets/buildings/${name}_${level}.png`;
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

function getFootprintSize(type) {
  const item = buildingCatalogByType.get(type);
  if (!item || !item.size) {
    return { w: 1, h: 1 };
  }
  return item.size;
}

function getBuildingFootprint(building) {
  const base = getFootprintSize(building.type);
  if (!building || base.w === base.h) {
    return base;
  }
  const rotation = building.rotation || 0;
  if (rotation === 90) {
    return { w: base.h, h: base.w };
  }
  return base;
}

function getPlacementSize(active = placing) {
  if (!active) return { w: 1, h: 1 };
  if (!active.rotated || active.size.w === active.size.h) {
    return active.size;
  }
  return { w: active.size.h, h: active.size.w };
}

function getActivePlacement() {
  return moving || placing;
}

function createPlate(size, isPreview, anchor) {
  const plate = document.createElement("div");
  plate.className = `plate${isPreview ? " preview" : ""}`;
  applyPlateGeometry(plate, size, anchor);
  return plate;
}

function applyPlateGeometry(plate, size, anchor) {
  const points = getFootprintPolygonPoints(size);
  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  points.forEach((point) => {
    minX = Math.min(minX, point.x);
    minY = Math.min(minY, point.y);
    maxX = Math.max(maxX, point.x);
    maxY = Math.max(maxY, point.y);
  });
  const width = maxX - minX;
  const height = maxY - minY;
  plate.style.width = `${width}px`;
  plate.style.height = `${height}px`;
  if (anchor === "center") {
    plate.style.left = `calc(50% + ${minX}px)`;
    plate.style.top = `calc(50% + ${minY}px)`;
  } else {
    plate.style.left = `${minX}px`;
    plate.style.top = `${minY}px`;
  }
  const clip = points
    .map((point) => `${point.x - minX}px ${point.y - minY}px`)
    .join(", ");
  plate.style.clipPath = `polygon(${clip})`;
}

function getFootprintPolygonPoints(size) {
  const halfW = TILE_WIDTH / 2;
  const halfH = TILE_HEIGHT / 2;
  const w = size.w;
  const h = size.h;
  return [
    { x: 0, y: -halfH },
    { x: w * halfW, y: (w - 1) * halfH },
    { x: (w - h) * halfW, y: (w + h - 1) * halfH },
    { x: -h * halfW, y: (h - 1) * halfH },
  ];
}

function startPlacing(type) {
  if (!type) return;
  if (moving) stopMoving();
  placing = { mode: "place", type, size: getFootprintSize(type), rotated: false, sourceStoredId: null, level: 1 };
  let seed = null;
  if (lastPointer) {
    seed = getTileFromPointIso(lastPointer.x, lastPointer.y);
  }
  if (!seed && selectedTile) {
    seed = { x: selectedTile.x, y: selectedTile.y };
  }
  if (seed) {
    const status = getPlacementStatus(seed.x, seed.y, getPlacementSize(placing), null, false);
    ghostTile = { x: seed.x, y: seed.y, valid: status.ok, reason: status.reason };
    updatePlacementCursor(status.ok);
  } else {
    ghostTile = null;
    updatePlacementCursor(null);
  }
  renderGhost();
}

function startPlacingFromStored(item) {
  if (!item) return;
  if (moving) stopMoving();
  placing = {
    mode: "place",
    type: item.type,
    size: item.size,
    rotated: item.rotation === 90,
    sourceStoredId: item.id,
    level: item.level,
  };
  let seed = null;
  if (lastPointer) {
    seed = getTileFromPointIso(lastPointer.x, lastPointer.y);
  }
  if (!seed && selectedTile) {
    seed = { x: selectedTile.x, y: selectedTile.y };
  }
  if (seed) {
    const status = getPlacementStatus(
      seed.x,
      seed.y,
      getPlacementSize(placing),
      null,
      true,
    );
    ghostTile = { x: seed.x, y: seed.y, valid: status.ok, reason: status.reason };
    updatePlacementCursor(status.ok);
  } else {
    ghostTile = null;
    updatePlacementCursor(null);
  }
  renderGhost();
  renderTilePanel();
}

function stopPlacing() {
  placing = null;
  ghostTile = null;
  hideGhost();
  updatePlacementCursor(null);
  selectedBuildType = "";
  renderGrid(state.city);
  renderTilePanel();
}

function startMoving(building) {
  if (!building) return;
  if (placing) stopPlacing();
  moving = {
    mode: "move",
    id: building.id,
    type: building.type,
    level: building.level,
    size: getFootprintSize(building.type),
    rotated: (building.rotation || 0) === 90,
  };
  let seed = null;
  if (lastPointer) {
    seed = getTileFromPointIso(lastPointer.x, lastPointer.y);
  }
  if (!seed) {
    seed = { x: building.x, y: building.y };
  }
  const status = getPlacementStatus(
    seed.x,
    seed.y,
    getPlacementSize(moving),
    moving.id,
    true,
  );
  ghostTile = { x: seed.x, y: seed.y, valid: status.ok, reason: status.reason };
  updatePlacementCursor(status.ok);
  renderGhost();
}

function stopMoving() {
  moving = null;
  ghostTile = null;
  hideGhost();
  updatePlacementCursor(null);
  renderGrid(state.city);
  renderTilePanel();
}

function stopPlacementMode() {
  if (moving) {
    stopMoving();
  } else if (placing) {
    stopPlacing();
  }
}

function ensureGhostElement() {
  const gridEl = document.getElementById("grid");
  if (!gridEl) return null;
  if (!ghostEl) {
    ghostEl = document.createElement("div");
    ghostEl.className = "ghost";
    ghostEl.style.position = "absolute";
    ghostEl.style.pointerEvents = "none";
    ghostEl.style.transform = "translate(-50%, -50%)";
    gridEl.appendChild(ghostEl);
  }
  return ghostEl;
}

function renderGhost() {
  const ghost = ensureGhostElement();
  const city = state.city;
  const active = getActivePlacement();
  if (!ghost || !active || !ghostTile || !city) {
    hideGhost();
    return;
  }

  const { x, y, valid } = ghostTile;
  const { type } = active;
  const size = getPlacementSize(active);
  const originX = (city.grid_size - 1) * (TILE_WIDTH / 2);
  const isoX = (x - y) * (TILE_WIDTH / 2) + originX;
  const isoY = (x + y) * (TILE_HEIGHT / 2);

  ghost.style.display = "block";
  ghost.style.left = `${isoX}px`;
  ghost.style.top = `${isoY}px`;
  ghost.style.zIndex = String(2000 + x + y);
  ghost.classList.toggle("is-valid", valid);
  ghost.classList.toggle("is-invalid", !valid);
  ghost.innerHTML = "";

  const plate = createPlate(size, false, "origin");
  plate.classList.add("ghost", valid ? "valid" : "invalid");
  ghost.appendChild(plate);

  if (active.rotated && size.w !== size.h) {
    const marker = document.createElement("div");
    marker.className = "ghost-rotation";
    marker.textContent = "↻";
    ghost.appendChild(marker);
  }

  const spriteLevel = active.level || 1;
  const sprite = getSpritePath(type, spriteLevel);
  if (sprite) {
    const img = document.createElement("img");
    img.className = "ghost-sprite";
    img.src = sprite;
    img.alt = `${type} preview`;
    const sprW = Math.round(SPRITE.size * SPRITE.scale);
    const sprH = Math.round(SPRITE.size * SPRITE.scale);
    img.width = sprW;
    img.height = sprH;
    img.style.bottom = "0px";
    ghost.appendChild(img);
  }
}

function hideGhost() {
  if (ghostEl) {
    ghostEl.style.display = "none";
    ghostEl.innerHTML = "";
  }
}

function updatePlacementCursor(valid) {
  const viewport = document.getElementById("gridViewport");
  if (!viewport) return;
  viewport.classList.remove("placing-valid", "placing-invalid");
  if (valid === true) {
    viewport.classList.add("placing-valid");
  } else if (valid === false) {
    viewport.classList.add("placing-invalid");
  }
}

function isTypingTarget(target) {
  if (!target) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return Boolean(target.isContentEditable);
}

function canPlaceAt(originX, originY, size) {
  return getPlacementStatus(originX, originY, size, null, false).ok;
}

function getPlacementStatus(originX, originY, size, ignoreBuildingId, skipCost) {
  const city = state.city;
  if (!city) return { ok: false, reason: "City not loaded." };
  for (let dx = 0; dx < size.w; dx += 1) {
    for (let dy = 0; dy < size.h; dy += 1) {
      const x = originX + dx;
      const y = originY + dy;
      if (x < 0 || y < 0 || x >= city.grid_size || y >= city.grid_size) {
        return { ok: false, reason: "Out of bounds." };
      }
      const occupancy = occupancyMap.get(`${x}:${y}`);
      if (occupancy && occupancy.buildingId !== ignoreBuildingId) {
        return { ok: false, reason: "Tile occupied." };
      }
    }
  }
  if (!skipCost) {
    const cost = getBuildCost(placing?.type, 1);
    if (Number.isFinite(cost) && state.city?.gold < cost) {
      return { ok: false, reason: "Not enough gold." };
    }
  }
  return { ok: true, reason: "" };
}

async function attemptPlaceAt(x, y) {
  const active = getActivePlacement();
  if (!active) return;
  const status = getPlacementStatus(
    x,
    y,
    getPlacementSize(active),
    active.mode === "move" ? active.id : null,
    active.mode === "move" || Boolean(active.sourceStoredId),
  );
  if (!status.ok) {
    showToast(status.reason || "Cannot place here.", true);
    return;
  }
  try {
    const token = getToken();
    const rotation = active.rotated ? 90 : 0;
    if (active.mode === "move") {
      await cityApi.move(token, active.id, x, y, rotation);
      const catalogItem = buildingCatalogByType.get(active.type);
      const name = catalogItem?.display_name || active.type;
      showToast(`Moved ${name}`);
      stopMoving();
    } else {
      await cityApi.build(token, active.type, x, y, rotation, active.sourceStoredId);
      const catalogItem = buildingCatalogByType.get(active.type);
      const name = catalogItem?.display_name || active.type;
      showToast(`Built ${name}`);
      stopPlacing();
    }
    await refreshCity();
  } catch (error) {
    showToast(getErrorMessage(error), true);
  }
}

function getSelectedFootprint() {
  if (!selectedTile || !state.city) return null;
  const key = `${selectedTile.x}:${selectedTile.y}`;
  const occupancy = occupancyMap.get(key);
  if (occupancy) {
    return {
      originX: occupancy.originX,
      originY: occupancy.originY,
      size: occupancy.size,
      isPreview: false,
    };
  }
  if (selectedBuildType && !placing) {
    return {
      originX: selectedTile.x,
      originY: selectedTile.y,
      size: getFootprintSize(selectedBuildType),
      isPreview: true,
    };
  }
  return null;
}

function cityHasTownHall() {
  return Boolean(state.city?.buildings?.some((building) => building.type === "town_hall"));
}

function renderOccupiedPanel(container, occupancy) {
  const catalogItem = buildingCatalogByType.get(occupancy.type);
  const name = catalogItem?.display_name || occupancy.type.replace("_", " ").toUpperCase();
  const info = document.createElement("div");
  info.textContent = `Occupied by: ${name} L${occupancy.level}`;
  container.appendChild(info);

  const originInfo = document.createElement("div");
  originInfo.className = "status";
  originInfo.textContent = `Origin: (${occupancy.originX}, ${occupancy.originY})`;
  container.appendChild(originInfo);

  const detail = document.createElement("div");
  detail.className = "status";
  detail.textContent = `This tile is part of a ${occupancy.size.w}x${occupancy.size.h} footprint. Select the origin tile to upgrade.`;
  container.appendChild(detail);

  if (!occupancy.isOrigin) {
    const focusBtn = document.createElement("button");
    focusBtn.className = "btn ghost";
    focusBtn.textContent = "Go to origin";
    focusBtn.addEventListener("click", () => {
      focusTile(occupancy.originX, occupancy.originY);
    });
    container.appendChild(focusBtn);
  }

  const buildBtn = document.createElement("button");
  buildBtn.className = "btn";
  buildBtn.textContent = "Build";
  buildBtn.disabled = true;
  buildBtn.title = "Tile occupied by another building";
  container.appendChild(buildBtn);
}
function renderBuildPanel(container) {
  const hasTownHall = cityHasTownHall();
  if (hasTownHall && selectedBuildType === "town_hall") {
    selectedBuildType = "";
  }
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
    if (item.type === "town_hall" && hasTownHall) {
      return;
    }
    const option = document.createElement("option");
    option.value = item.type;
    option.textContent = item.display_name;
    select.appendChild(option);
  });

  select.value = selectedBuildType;
  select.addEventListener("change", () => {
    selectedBuildType = select.value;
    if (selectedBuildType) {
      startPlacing(selectedBuildType);
    } else {
      stopPlacing();
    }
    renderGrid(state.city);
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
  buildBtn.textContent = getActivePlacement() ? "Placing..." : "Build";
  buildBtn.disabled =
    !selectedBuildType ||
    !Number.isFinite(cost) ||
    state.city.gold < cost ||
    Boolean(getActivePlacement());
  buildBtn.addEventListener("click", () => {
    if (!selectedBuildType) return;
    startPlacing(selectedBuildType);
    renderGrid(state.city);
  });
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
    addMoveButton(container, building);
    addStoreButton(container, building);
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
  addMoveButton(container, building);
  addStoreButton(container, building);
}

function addMoveButton(container, building) {
  const moveBtn = document.createElement("button");
  moveBtn.className = "btn ghost";
  moveBtn.type = "button";
  moveBtn.textContent = "Move";
  moveBtn.disabled = Boolean(getActivePlacement());
  moveBtn.addEventListener("click", () => startMoving(building));
  container.appendChild(moveBtn);
}

function addStoreButton(container, building) {
  const storeBtn = document.createElement("button");
  storeBtn.className = "btn ghost";
  storeBtn.type = "button";
  storeBtn.textContent = "Store";
  storeBtn.disabled = Boolean(getActivePlacement()) || building.type === "town_hall";
  storeBtn.addEventListener("click", () => handleStore(building));
  container.appendChild(storeBtn);
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
    TOWN_HALL_ALREADY_EXISTS: "Town Hall already placed.",
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

async function handleStore(building) {
  if (!building) return;
  stopPlacementMode();
  const catalogItem = buildingCatalogByType.get(building.type);
  const name = catalogItem?.display_name || building.type;
  const confirmed = window.confirm(`Store ${name} L${building.level}?`);
  if (!confirmed) return;
  try {
    const token = getToken();
    await cityApi.store(token, building.id);
    showToast(`Stored ${name}`);
    await refreshCity();
    renderTilePanel();
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
