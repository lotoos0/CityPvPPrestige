/**
 * Toast component - simple notification system
 */

export function showToast(message, isError = false) {
  const authMessage = document.getElementById("authMessage");
  if (authMessage) {
    authMessage.textContent = message;
    authMessage.style.color = isError ? "#ff8c6a" : "#9fb0c9";
  }
}
