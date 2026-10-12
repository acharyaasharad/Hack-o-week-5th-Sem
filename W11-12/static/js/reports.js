/* reports.js — Exports and experiment history manager */

const ReportsManager = {
  init() {
    this.bindEvents();
    this.fetchExperiments();
  },

  bindEvents() {
    const btnPcaCsv = document.getElementById("btn-export-pca-csv");
    if (btnPcaCsv) {
      btnPcaCsv.addEventListener("click", () => { window.location.href = "/api/export/pca.csv"; });
    }

    const btnTsneCsv = document.getElementById("btn-export-tsne-csv");
    if (btnTsneCsv) {
      btnTsneCsv.addEventListener("click", () => { window.location.href = "/api/export/tsne.csv"; });
    }

    const btnCombinedCsv = document.getElementById("btn-export-combined-csv");
    if (btnCombinedCsv) {
      btnCombinedCsv.addEventListener("click", () => { window.location.href = "/api/export/combined.csv"; });
    }

    const btnLoadingsCsv = document.getElementById("btn-export-loadings-csv");
    if (btnLoadingsCsv) {
      btnLoadingsCsv.addEventListener("click", () => { window.location.href = "/api/export/loadings.csv"; });
    }

    const btnHtmlReport = document.getElementById("btn-export-html-report");
    if (btnHtmlReport) {
      btnHtmlReport.addEventListener("click", () => { window.location.href = "/api/export/report"; });
    }
  },

  async fetchExperiments() {
    try {
      const res = await fetch("/api/experiments");
      const list = await res.json();
      this.renderExperimentsTable(list);
    } catch (err) {
      console.error("Experiment fetch error", err);
    }
  },

  renderExperimentsTable(list) {
    const tbody = document.getElementById("experiments-table-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted p-4">No experiment runs saved yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(item => {
      const metricStr = item.method === "PCA" 
        ? `Var: ${item.metrics.total_2d_variance}%` 
        : `Perp: ${item.metrics.perplexity}`;
      return `
        <tr>
          <td><strong>${item.id}</strong></td>
          <td>${item.timestamp}</td>
          <td><span class="badge ${item.method === 'PCA' ? 'badge-info' : 'badge-success'}">${item.method}</span></td>
          <td>${item.dataset_name}</td>
          <td>${item.n_samples}</td>
          <td>${metricStr}</td>
          <td>${item.execution_time_seconds}s</td>
        </tr>
      `;
    }).join("");
  }
};
