/* app.js — Global UI orchestrator and point inspection manager */

const App = {
  activeView: "overview",

  init() {
    this.bindNavigation();
    DatasetManager.init();
    PcaManager.init();
    TsneManager.init();
    ComparisonManager.init();
    ReportsManager.init();

    // Auto-run PCA on start
    setTimeout(() => {
      PcaManager.runPCA();
    }, 500);
  },

  bindNavigation() {
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
      item.addEventListener("click", (e) => {
        e.preventDefault();
        const view = item.getAttribute("data-view");
        if (view) this.switchView(view);
      });
    });

    const resetBtn = document.getElementById("btn-reset-workspace");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        if (confirm("Reset workspace to Wine recognition dataset?")) {
          DatasetManager.loadBuiltin("wine");
        }
      });
    }
  },

  switchView(viewName) {
    this.activeView = viewName;
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(el => {
      el.classList.toggle("active", el.getAttribute("data-view") === viewName);
    });
    document.querySelectorAll(".view-section").forEach(sec => {
      sec.classList.toggle("active", sec.id === `view-${viewName}`);
    });
    setTimeout(() => window.dispatchEvent(new Event("resize")), 100);
  },

  async inspectPoint(rowId) {
    this.switchView("point-inspector");
    this.showLoading(`Loading observation ${rowId}...`);
    try {
      const res = await fetch(`/api/point/${encodeURIComponent(rowId)}`);
      const data = await res.json();
      if (!data.error) {
        document.getElementById("inspector-row-id").textContent = data.row_id;

        // Display PCA coordinates
        const pcaDiv = document.getElementById("inspector-pca-coords");
        if (data.pca_coordinates) {
          pcaDiv.innerHTML = `<strong>PC1:</strong> ${data.pca_coordinates.x} &bull; <strong>PC2:</strong> ${data.pca_coordinates.y}`;
        } else {
          pcaDiv.innerHTML = `<span class="text-muted">Not calculated in current PCA run</span>`;
        }

        // Display t-SNE coordinates
        const tsneDiv = document.getElementById("inspector-tsne-coords");
        if (data.tsne_coordinates) {
          tsneDiv.innerHTML = `<strong>Dim 1:</strong> ${data.tsne_coordinates.x} &bull; <strong>Dim 2:</strong> ${data.tsne_coordinates.y}`;
        } else {
          tsneDiv.innerHTML = `<span class="text-muted">Not calculated or excluded from sample</span>`;
        }

        // Feature values table
        const tbody = document.getElementById("inspector-features-tbody");
        if (tbody) {
          tbody.innerHTML = Object.entries(data.features).map(([feat, val]) => {
            return `<tr><td><strong>${feat}</strong></td><td>${val}</td></tr>`;
          }).join("");
        }
      }
    } catch (err) {
      this.notify("Point lookup failed", "danger");
    } finally {
      this.hideLoading();
    }
  },

  notify(msg, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `alert alert-${type}`;
    toast.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
    toast.style.marginBottom = "10px";
    toast.innerHTML = `<span>${msg}</span>`;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
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
    if (overlay) overlay.style.display = "none";
  }
};

document.addEventListener("DOMContentLoaded", () => App.init());
