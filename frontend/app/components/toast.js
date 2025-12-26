/**
 * Toast component - simple notification system
 */

let toastTimer = null;

export function showToast(message, isError = false) {
  const toast = document.getElementById("toast");
  if (toast) {
    toast.textContent = message;
    toast.classList.toggle("error", isError);
    toast.classList.add("show");
    if (toastTimer) {
      clearTimeout(toastTimer);
    }
    toastTimer = setTimeout(() => {
      toast.classList.remove("show");
    }, 3000);
    return;
  }

  const authMessage = document.getElementById("authMessage");
  if (authMessage) {
    authMessage.textContent = message;
    authMessage.style.whiteSpace = "pre-line";
    authMessage.style.color = isError ? "#ff8c6a" : "#9fb0c9";
  }
}
