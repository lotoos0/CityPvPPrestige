/**
 * History view - attack log
 */

import { pvpApi } from "../api.js";
import { getToken } from "../auth.js";
import { state } from "../state.js";

export async function historyView() {
  const token = getToken();
  if (!token) return;

  // Hide auth/city, show game UI
  document.getElementById("authSection").style.display = "none";
  document.querySelector(".hud").style.display = "grid";
  document.querySelector(".city").style.display = "none";
  document.querySelector(".ranking").style.display = "none";
  document.querySelector(".history").style.display = "block";

  // Load attack history
  await refreshHistory();
}

async function refreshHistory() {
  const historyStatus = document.getElementById("historyStatus");
  try {
    const token = getToken();
    const entries = await pvpApi.log(token);
    renderHistory(entries);
    historyStatus.textContent = "";
  } catch (error) {
    historyStatus.textContent = error.message || "Failed to load history";
  }
}

function renderHistory(entries) {
  const attackLog = document.getElementById("attackLog");
  attackLog.innerHTML = "";

  if (!entries || entries.length === 0) {
    attackLog.innerHTML = "<p>No battles yet.</p>";
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
