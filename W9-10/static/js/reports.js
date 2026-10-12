/* reports.js — Exports and experiment history manager */

const ReportsManager = {
  init() {
    this.bindEvents();
    this.fetchExperiments();
  },

  bindEvents() {
    const btnCsv = document.getElementById("btn-export-labeled-csv");
    if (btnCsv) {
      btnCsv.addEventListener("click", () => {
        window.location.href = "/api/export/clusters.csv";
      });
    }

    const btnProfiles = document.getElementById("btn-export-profiles-csv");
    if (btnProfiles) {
      btnProfiles.addEventListener("click", () => {
        window.location.href = "/api/export/profiles.csv";
      });
    }

    const btnHtml = document.getElementById("btn-export-html-report");
    if (btnHtml) {
      btnHtml.addEventListener("click", () => {
        window.location.href = "/api/export/report.html";
      });
    }

    const saveExpBtn = document.getElementById("btn-save-experiment");
    if (saveExpBtn) {
      saveExpBtn.addEventListener("click", () => this.saveExperiment());
    }
  },

  async fetchExperiments() {
    try {
      const res = await fetch("/api/experiments");
      const list = await res.json();
      this.renderExperimentsTable(list);
    } catch (err) {
      console.error("Experiments history fetch error", err);
    }
  },

  renderExperimentsTable(list) {
    const tbody = document.getElementById("experiments-table-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted p-4">No experiment runs saved yet. Run a clustering model to log runs.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(item => {
      const sil = item.metrics && item.metrics.silhouette_score !== null ? item.metrics.silhouette_score : "-";
      return `
        <tr>
          <td><strong>${item.id || item.timestamp}</strong></td>
          <td>${item.timestamp}</td>
          <td>${item.algorithm}</td>
          <td>${item.cluster_count}</td>
          <td>${item.noise_percentage}%</td>
          <td><strong>${sil}</strong></td>
          <td><span class="badge badge-success">Completed</span></td>
        </tr>
      `;
    }).join("");
  },

  async saveExperiment() {
    const notes = prompt("Enter optional notes for this experiment run:");
    if (notes === null) return;

    try {
      const res = await fetch("/api/experiments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: notes }),
      });
      const data = await res.json();
      if (data.success) {
        App.notify("Experiment saved to history log.", "success");
        this.fetchExperiments();
      }
    } catch (err) {
      App.notify("Failed to save experiment.", "danger");
    }
  }
};
