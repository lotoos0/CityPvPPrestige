/**
 * Army view - army inventory and barracks training
 */

import { armyApi, barracksApi } from "../api.js";
import { getToken } from "../auth.js";
import { showToast } from "../components/toast.js";
import { on } from "../state.js";

let armyRefreshTimer = null;
let offArmyRefresh = null;

export async function armyView() {
  const token = getToken();
  if (!token) return;

  // Hide auth/city, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "none";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "none";

  // Start army HUD
  startArmyHud();
  refreshArmyAndQueue();
  if (!offArmyRefresh) {
    offArmyRefresh = on("army:refresh", () => {
      refreshArmyAndQueue();
    });
  }

  // Setup training controls
  const trainSubmit = document.getElementById("train-submit");
  const claimSubmit = document.getElementById("claim-submit");
  const queueRefreshBtn = document.getElementById("queue-refresh");
  const armyRefreshBtn = document.getElementById("army-refresh");

  trainSubmit.onclick = trainUnits;
  claimSubmit.onclick = claimUnits;
  queueRefreshBtn.onclick = refreshQueue;
  armyRefreshBtn.onclick = refreshArmy;
}

export function stopArmyView() {
  if (armyRefreshTimer) {
    clearInterval(armyRefreshTimer);
    armyRefreshTimer = null;
  }
  if (offArmyRefresh) {
    offArmyRefresh();
    offArmyRefresh = null;
  }

  const armyRefreshBtn = document.getElementById("army-refresh");
  armyRefreshBtn.disabled = true;

  // Reset displays
  document.getElementById("army-units").textContent = "No units.";
  document.getElementById("barracks-queue").textContent = "Queue empty.";
  setArmyStatus("");
  setBarracksStatus("");
}

function setArmyStatus(message, isError = false) {
  const armyStatus = document.getElementById("army-status");
  armyStatus.textContent = message;
  armyStatus.classList.remove("bad", "good");
  if (message) {
    armyStatus.classList.add(isError ? "bad" : "good");
  }
}

function setBarracksStatus(message, isError = false) {
  const barracksStatus = document.getElementById("barracks-status");
  barracksStatus.textContent = message;
  barracksStatus.classList.remove("bad", "good");
  if (message) {
    barracksStatus.classList.add(isError ? "bad" : "good");
  }
}

function renderArmy(units) {
  const armyUnits = document.getElementById("army-units");
  if (!units || units.length === 0) {
    armyUnits.textContent = "No units.";
    return;
  }

  armyUnits.innerHTML = units
    .map((unit) => `<div>${unit.code}: <strong>${unit.qty}</strong></div>`)
    .join("");
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
  const barracksQueue = document.getElementById("barracks-queue");
  if (!queue || !queue.status) {
    barracksQueue.textContent = "Queue empty.";
    return;
  }
  barracksQueue.innerHTML = `
    <div>Status: <strong>${queue.status}</strong></div>
    <div>Unit: <strong>${queue.unit_code}</strong>, qty: <strong>${queue.qty}</strong></div>
    <div>Completes: <strong>${queue.completes_at || "?"}</strong> (${formatCountdown(queue.completes_at)})</div>
  `;
}

async function refreshArmy() {
  setArmyStatus("Loading...");
  try {
    const token = getToken();
    const data = await armyApi.fetch(token);
    renderArmy(data.units);
    setArmyStatus("OK");
  } catch (error) {
    setArmyStatus(`Disconnected (${error.status || "?"})`, true);
  }
}

async function refreshQueue() {
  setBarracksStatus("Loading...");
  try {
    const token = getToken();
    const data = await barracksApi.queue(token);
    renderQueue(data);
    setBarracksStatus("OK");
  } catch (error) {
    setBarracksStatus(`Disconnected (${error.status || "?"})`, true);
  }
}

function refreshArmyAndQueue() {
  refreshArmy();
  refreshQueue();
}

async function trainUnits() {
  setBarracksStatus("Training...");
  const unit = document.getElementById("train-unit").value;
  const qty = parseInt(document.getElementById("train-qty").value, 10);

  try {
    const token = getToken();
    await barracksApi.train(token, unit, qty);
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
    const token = getToken();
    const data = await barracksApi.claim(token);
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
  const armyRefreshBtn = document.getElementById("army-refresh");
  armyRefreshBtn.disabled = false;
  refreshArmyAndQueue();
  armyRefreshTimer = setInterval(() => {
    refreshArmyAndQueue();
  }, 10000);
}
