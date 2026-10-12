/* app.js — Global UI controller, single-page navigation, and notification system */

const App = {
  activeView: "overview",

  init() {
    this.bindNavigation();
    DatasetManager.init();
    ClusteringManager.init();
    ReportsManager.init();

    // Auto-trigger clustering on load if dataset exists
    setTimeout(() => {
      if (!ClusteringManager.lastResult) {
        ClusteringManager.runClustering();
      }
    }, 600);
  },

  bindNavigation() {
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", (e) => {
        e.preventDefault();
        const targetView = item.getAttribute("data-view");
        if (targetView) {
          this.switchView(targetView);
        }
      });
    });

    const resetBtn = document.getElementById("btn-reset-workspace");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        if (confirm("Reset workspace to official UCI dataset with default 6 spending features?")) {
          DatasetManager.loadBuiltinDataset(false);
        }
      });
    }
  },

  switchView(viewName) {
    this.activeView = viewName;

    // Update active nav item
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(el => {
      el.classList.toggle("active", el.getAttribute("data-view") === viewName);
    });

    // Toggle view sections
    document.querySelectorAll(".view-section").forEach(sec => {
      sec.classList.toggle("active", sec.id === `view-${viewName}`);
    });

    // Resize Plotly charts when switching tabs
    setTimeout(() => {
      window.dispatchEvent(new Event("resize"));
    }, 100);
  },

  notify(msg, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `alert alert-${type}`;
    toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
    toast.style.marginBottom = "10px";
    toast.style.animation = "fadeIn 0.2s ease";
    toast.innerHTML = `<span>${msg}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.remove();
    }, 3500);
  },

  showLoading(text = "Processing...") {
    const overlay = document.getElementById("loading-overlay");
    const textEl = document.getElementById("loading-text");
    if (overlay) {
      if (textEl) textEl.textContent = text;
      overlay.style.display = "flex";
    }
  },

  hideLoading() {
    const overlay = document.getElementById("loading-overlay");
    if (overlay) {
      overlay.style.display = "none";
    }
  }
};

document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
