/**
 * PvP view - ranking and attacks
 */

import { pvpApi, rankApi, cityApi, statsApi, authApi } from "../api.js";
import { getToken } from "../auth.js";
import { emit, state } from "../state.js";
import { showToast } from "../components/toast.js";

let pvpRefreshTimer = null;
let lastSameTargetAvailableAt = null;

export async function pvpView() {
  const token = getToken();
  if (!token) return;

  // Hide auth/city, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "none";
  document.querySelector(".ranking").style.display = "block";
  document.querySelector(".history").style.display = "none";

  // Start PvP HUD
  startPvpHud();

  // Load ranking
  await refreshRanking();

  // Setup refresh button
  const pvpRefreshBtn = document.getElementById("pvpRefreshBtn");
  pvpRefreshBtn.disabled = false;
  pvpRefreshBtn.onclick = refreshPvpHud;
}

export function stopPvpView() {
  if (pvpRefreshTimer) {
    clearInterval(pvpRefreshTimer);
    pvpRefreshTimer = null;
  }

  const pvpRefreshBtn = document.getElementById("pvpRefreshBtn");
  pvpRefreshBtn.disabled = true;

  // Reset PvP HUD
  document.getElementById("pvpResetAt").textContent = "--";
  document.getElementById("pvpBanner").textContent = "";
  document.getElementById("pvpBanner").classList.add("hidden");
  document.getElementById("pvpAttacksRow").textContent = "Attacks: --";
  document.getElementById("pvpGainRow").textContent = "Prestige gain: --";
  document.getElementById("pvpLossRow").textContent = "Prestige loss: --";
  document.getElementById("pvpGlobalCooldown").textContent = "Global cooldown: --";
  document.getElementById("pvpTargetCooldown").textContent = "Same target cooldown: --";
  setPvpStatus("");
}

function setPvpStatus(message, isError = false) {
  const pvpStatus = document.getElementById("pvpStatus");
  pvpStatus.textContent = message;
  pvpStatus.style.color = isError ? "#ff8c6a" : "#9fb0c9";
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

function formatLosses(losses) {
  if (!losses) return "0 Raiders, 0 Guardians";
  return `${losses.raider} Raiders, ${losses.guardian} Guardians`;
}

function renderPvpHud(payload) {
  if (!payload || !payload.limits) return;
  const { limits, nightly_decay: nightlyDecay, cooldowns } = payload;

  document.getElementById("pvpResetAt").textContent = formatResetAt(limits.reset_at);

  const resetTime = new Date(limits.reset_at).getTime();
  if (Number.isFinite(resetTime) && resetTime < Date.now()) {
    setPvpStatus("Time sync issue detected.", true);
  } else {
    setPvpStatus("");
  }

  const pvpBanner = document.getElementById("pvpBanner");
  if (nightlyDecay && nightlyDecay > 0) {
    pvpBanner.textContent = `Nightly decay applied: -${nightlyDecay} prestige`;
    pvpBanner.classList.remove("hidden");
  } else {
    pvpBanner.textContent = "";
    pvpBanner.classList.add("hidden");
  }

  document.getElementById("pvpAttacksRow").innerHTML = `Attacks: <strong>${limits.attacks_used}</strong> used / left <strong>${limits.attacks_left}</strong>`;
  document.getElementById("pvpGainRow").innerHTML = `Prestige gain today: <strong>${limits.prestige_gain_today}</strong> / left <strong>${limits.prestige_gain_left}</strong>`;
  document.getElementById("pvpLossRow").innerHTML = `Prestige loss today: <strong>${limits.prestige_loss_today}</strong> / protected left <strong>${limits.prestige_loss_left}</strong>`;

  const globalLeft =
    cooldowns?.global_remaining_sec ?? secondsLeft(cooldowns?.global_available_at ?? null);
  const cachedSameTarget = lastSameTargetAvailableAt;
  const sameTargetAvailableAt = cooldowns?.same_target_available_at ?? cachedSameTarget;
  const targetLeft = secondsLeft(sameTargetAvailableAt ?? null);

  document.getElementById("pvpGlobalCooldown").innerHTML = `Global cooldown: <strong>${formatDuration(globalLeft)}</strong>`;
  document.getElementById("pvpTargetCooldown").innerHTML = `Same target cooldown: <strong>${formatDuration(targetLeft)}</strong>`;
}

async function refreshPvpHud() {
  try {
    const token = getToken();
    const payload = await pvpApi.limits(token);
    renderPvpHud(payload);
    setPvpStatus("");
  } catch (error) {
    setPvpStatus(`Disconnected: ${error.message}`, true);
  }
}

function startPvpHud() {
  if (pvpRefreshTimer) return;
  refreshPvpHud();
  pvpRefreshTimer = setInterval(refreshPvpHud, 10000);
}

async function refreshRanking() {
  const rankStatus = document.getElementById("rankStatus");
  try {
    const token = getToken();
    const [top, near] = await Promise.all([rankApi.top(token), rankApi.near(token)]);
    renderRankList(document.getElementById("rankTop"), top);
    renderRankList(document.getElementById("rankNear"), near);
    rankStatus.textContent = "";
  } catch (error) {
    rankStatus.textContent = error.message || "Failed to load ranking";
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
    attackBtn.disabled = entry.user_id === state.user?.id;

    attackBtn.addEventListener("click", async () => {
      await handleAttack(entry.user_id);
    });

    row.appendChild(attackBtn);
    container.appendChild(row);
  });
}

async function handleAttack(userId) {
  const rankStatus = document.getElementById("rankStatus");
  try {
    const token = getToken();
    const result = await pvpApi.attack(token, userId);
    rankStatus.textContent = `Result: ${result.result} (Δ${result.prestige.delta})`;

    if (result.cooldowns?.same_target_available_at) {
      lastSameTargetAvailableAt = result.cooldowns.same_target_available_at;
    }

    const attackerLosses = result.losses?.attacker;
    const defenderLosses = result.losses?.defender;
    const totalLosses =
      (attackerLosses?.raider || 0) +
      (attackerLosses?.guardian || 0) +
      (defenderLosses?.raider || 0) +
      (defenderLosses?.guardian || 0);
    if (totalLosses === 0) {
      showToast("No units lost");
    } else {
      showToast(
        `You lost: ${formatLosses(attackerLosses)}\nOpponent lost: ${formatLosses(defenderLosses)}`
      );
    }
    emit("army:refresh");

    if (result.limits) {
      renderPvpHud({
        limits: result.limits,
        cooldowns: result.cooldowns ?? null,
        nightly_decay: null,
      });
    }

    // Refresh city stats
    const [city, stats, user] = await Promise.all([
      cityApi.fetch(token),
      statsApi.fetch(token),
      authApi.me(token),
    ]);
    state.setState({ city, user });
  } catch (error) {
    if (error?.status === 403 && error?.data?.error?.code === "INSUFFICIENT_ARMY") {
      showToast("Train units in Barracks to attack (min 10).", true);
      rankStatus.textContent = "Train units in Barracks to attack (min 10).";
      window.location.hash = "#/army";
    } else {
      rankStatus.textContent = error?.data?.detail || error?.data?.message || "Attack failed";
    }
  }
}
