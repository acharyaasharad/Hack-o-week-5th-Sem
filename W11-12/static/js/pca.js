/* pca.js — Principal Component Analysis execution, loadings, and variance views */

const PcaManager = {
  lastResult: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const btnRun = document.getElementById("btn-run-pca");
    if (btnRun) {
      btnRun.addEventListener("click", () => this.runPCA());
    }

    const selDim = document.getElementById("pca-dim-mode");
    if (selDim) {
      selDim.addEventListener("change", () => {
        if (this.lastResult) this.renderPlots(this.lastResult);
      });
    }

    const selLoadingComp = document.getElementById("pca-loadings-component-select");
    if (selLoadingComp) {
      selLoadingComp.addEventListener("change", (e) => {
        if (this.lastResult) ChartManager.renderLoadingsBar("chart-pca-loadings", this.lastResult.loadings, e.target.value);
      });
    }
  },

  async runPCA() {
    const features = PreprocessingManager.getSelectedFeatures();
    if (features.length < 2) {
      App.notify("Select at least 2 features for PCA.", "warning");
      return;
    }

    const { scaler, logTransform } = PreprocessingManager.getPreprocessingConfig();
    const colorBy = document.getElementById("pca-color-by").value;
    const isKmeans = document.getElementById("pca-kmeans-overlay").checked;
    const kmeansK = parseInt(document.getElementById("pca-kmeans-k").value || 3, 10);
    const nComp = parseInt(document.getElementById("pca-retained-components").value || 2, 10);

    App.showLoading("Fitting scikit-learn PCA Pipeline...");
    try {
      const res = await fetch("/api/pca/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          features: features,
          n_components: nComp,
          scaler: scaler,
          log_transform: logTransform,
          color_by: colorBy,
          kmeans_overlay: isKmeans,
          kmeans_k: kmeansK,
        }),
      });

      const data = await res.json();
      if (data.status === "success") {
        this.lastResult = data;
        this.renderOutput(data);
        App.notify(`PCA completed in ${data.execution_time_seconds}s (2D Variance: ${data.total_2d_variance}%)`, "success");
      } else {
        App.notify(data.message || "PCA failed", "danger");
      }
    } catch (err) {
      App.notify("Error executing PCA", "danger");
    } finally {
      App.hideLoading();
    }
  },

  renderOutput(data) {
    // Metric cards
    document.getElementById("stat-pca-pc1-var").textContent = `${data.pc1_variance}%`;
    document.getElementById("stat-pca-pc2-var").textContent = `${data.pc2_variance}%`;
    document.getElementById("stat-pca-total-var").textContent = `${data.total_2d_variance}%`;
    document.getElementById("stat-pca-runtime").textContent = `${data.execution_time_seconds}s`;
    document.getElementById("stat-pca-trust").textContent = data.trustworthiness !== null ? data.trustworthiness : "N/A";
    document.getElementById("stat-pca-recon").textContent = data.reconstruction_error;

    // Overview stats
    document.getElementById("stat-overview-pca-var").textContent = `${data.total_2d_variance}%`;
    document.getElementById("stat-overview-pca-status").textContent = "Fitted";

    this.renderPlots(data);
    this.renderLoadingsTable(data.loadings);
  },

  renderPlots(data) {
    const is3D = document.getElementById("pca-dim-mode").value === "3d" && data.n_components >= 3;
    const coords = data.coordinates.map(c => ({
      ...c,
      color_value: data.kmeans_overlay ? c.kmeans_cluster : c.color_value,
    }));

    ChartManager.renderScatter(
      "chart-pca-projection",
      coords,
      `PCA Projection (PC1: ${data.pc1_variance}%, PC2: ${data.pc2_variance}%)`,
      "Principal Component 1 (PC1)",
      "Principal Component 2 (PC2)",
      is3D
    );

    // Also update overview chart
    ChartManager.renderScatter(
      "chart-overview-pca",
      coords,
      "Principal Component Analysis (PCA)",
      "PC1", "PC2", false
    );

    ChartManager.renderScreePlot("chart-pca-scree", data.explained_variance_ratio, data.cumulative_variance_ratio);

    const compSel = document.getElementById("pca-loadings-component-select").value || "PC1";
    ChartManager.renderLoadingsBar("chart-pca-loadings", data.loadings, compSel);
  },

  renderLoadingsTable(loadings) {
    const tbody = document.getElementById("pca-loadings-tbody");
    if (!tbody || !loadings) return;

    tbody.innerHTML = loadings.slice(0, 20).map(l => {
      const isPos = l.loading >= 0;
      return `
        <tr>
          <td><strong>${l.component}</strong></td>
          <td>${l.feature}</td>
          <td><span class="badge ${isPos ? 'badge-info' : 'badge-warning'}">${l.loading.toFixed(4)}</span></td>
          <td>${l.abs_loading.toFixed(4)}</td>
        </tr>
      `;
    }).join("");
  }
};
