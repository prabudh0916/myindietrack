/**
 * IndieTrack — Application Utilities & Theme Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Theme Toggle Management (Stored safely in localStorage, UI only)
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  const themeIcon = document.getElementById("themeIcon");
  const htmlElement = document.documentElement;

  const savedTheme = localStorage.getItem("indietrack-theme") || "dark";
  setTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const currentTheme = htmlElement.getAttribute("data-theme") || "dark";
      const newTheme = currentTheme === "dark" ? "light" : "dark";
      setTheme(newTheme);
      localStorage.setItem("indietrack-theme", newTheme);
    });
  }

  function setTheme(theme) {
    htmlElement.setAttribute("data-theme", theme);
    if (themeIcon) {
      if (theme === "light") {
        themeIcon.className = "bi bi-moon-stars-fill";
      } else {
        themeIcon.className = "bi bi-sun-fill";
      }
    }
  }

  // 2. Auto-dismiss alerts after 6 seconds
  const autoAlerts = document.querySelectorAll(".alert-dismissible");
  autoAlerts.forEach((alert) => {
    setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      } catch (e) {
        // Fallback
        alert.style.display = "none";
      }
    }, 6000);
  });

  // 3. Confirm dialog for destructive actions
  const destructiveForms = document.querySelectorAll("form.confirm-action");
  destructiveForms.forEach((form) => {
    form.addEventListener("submit", (e) => {
      const message = form.getAttribute("data-confirm-message") || "Are you sure you want to proceed with this deletion?";
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
});
