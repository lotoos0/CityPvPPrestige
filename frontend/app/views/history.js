/**
 * History view - attack log
 */

import { pvpApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";

let nextCursor = null;
let initialized = false;

export async function historyView() {
  const token = getToken();
  if (!token) return;

  // Hide auth/city, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "none";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "block";

  // Initialize load more button (only once)
  if (!initialized) {
    initialized = true;
    const loadMoreBtn = document.getElementById("historyLoadMore");
    loadMoreBtn.addEventListener("click", handleLoadMore);
  }

  // Load initial history
  nextCursor = null;
  await refreshHistory(false);
}

async function refreshHistory(append = false) {
  const historyStatus = document.getElementById("historyStatus");
  const loadMoreBtn = document.getElementById("historyLoadMore");

  try {
    const token = getToken();
    const response = await pvpApi.log(token, append ? nextCursor : null);
    renderHistory(response.items || [], append);
    nextCursor = response.next_cursor || null;

    // Show/hide load more button
    loadMoreBtn.style.display = nextCursor ? "inline-block" : "none";
    historyStatus.textContent = `Loaded ${response.items?.length || 0} entries`;
  } catch (error) {
    historyStatus.textContent = error.message || "Failed to load history";
    loadMoreBtn.style.display = "none";
  }
}

async function handleLoadMore() {
  await refreshHistory(true);
}

function renderHistory(entries, append = false) {
  const attackLog = document.getElementById("attackLog");

  if (!append) {
    attackLog.innerHTML = "";
  }

  if (!entries || entries.length === 0) {
    if (!append) {
      attackLog.innerHTML = "<p>No battles yet.</p>";
    }
    return;
  }

  entries.forEach((entry) => {
    const isAttacker = entry.attacker_id === state.user?.id;
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
