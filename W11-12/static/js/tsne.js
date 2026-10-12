/* tsne.js — t-SNE execution and parameter tuning manager */

const TsneManager = {
  lastResult: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const btnRun = document.getElementById("btn-run-tsne");
    if (btnRun) {
      btnRun.addEventListener("click", () => this.runTSNE());
    }

    const selDim = document.getElementById("tsne-dim-mode");
    if (selDim) {
      selDim.addEventListener("change", () => {
        if (this.lastResult) this.renderPlots(this.lastResult);
      });
    }
  },

  async runTSNE() {
    const features = PreprocessingManager.getSelectedFeatures();
    if (features.length < 2) {
      App.notify("Select at least 2 features for t-SNE.", "warning");
      return;
    }

    const { scaler, logTransform } = PreprocessingManager.getPreprocessingConfig();
    const perplexity = parseFloat(document.getElementById("tsne-perplexity").value || 30);
    const maxIter = parseInt(document.getElementById("tsne-max-iter").value || 1000, 10);
    const lr = document.getElementById("tsne-learning-rate").value || "auto";
    const colorBy = document.getElementById("tsne-color-by").value;
    const isKmeans = document.getElementById("tsne-kmeans-overlay").checked;
    const kmeansK = parseInt(document.getElementById("tsne-kmeans-k").value || 3, 10);

    App.showLoading(`Fitting t-SNE (Perplexity: ${perplexity}, Iterations: ${maxIter})...`);
    try {
      const res = await fetch("/api/tsne/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          features: features,
          perplexity: perplexity,
          max_iter: maxIter,
          learning_rate: lr,
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
        App.notify(`t-SNE completed in ${data.execution_time_seconds}s!`, "success");
      } else {
        App.notify(data.message || "t-SNE execution failed", "danger");
      }
    } catch (err) {
      App.notify("Error executing t-SNE", "danger");
    } finally {
      App.hideLoading();
    }
  },

  renderOutput(data) {
    document.getElementById("stat-tsne-samples").textContent = data.n_samples;
    document.getElementById("stat-tsne-perp").textContent = data.perplexity;
    document.getElementById("stat-tsne-runtime").textContent = `${data.execution_time_seconds}s`;
    document.getElementById("stat-tsne-trust").textContent = data.trustworthiness !== null ? data.trustworthiness : "N/A";
    document.getElementById("stat-tsne-kl").textContent = data.kl_divergence !== null ? data.kl_divergence : "N/A";

    // Overview stat
    document.getElementById("stat-overview-tsne-status").textContent = "Fitted";

    // Warnings
    const warnBox = document.getElementById("tsne-warnings-box");
    if (warnBox) {
      if (data.warnings && data.warnings.length > 0) {
        warnBox.innerHTML = data.warnings.map(w => `<div class="alert alert-warning">${w}</div>`).join("");
      } else {
        warnBox.innerHTML = "";
      }
    }

    this.renderPlots(data);
  },

  renderPlots(data) {
    const is3D = document.getElementById("tsne-dim-mode").value === "3d" && data.coordinates[0]?.z !== undefined;
    const coords = data.coordinates.map(c => ({
      ...c,
      color_value: data.kmeans_overlay ? c.kmeans_cluster : c.color_value,
    }));

    ChartManager.renderScatter(
      "chart-tsne-projection",
      coords,
      `t-SNE Embedding (Perplexity: ${data.perplexity})`,
      "t-SNE Dimension 1",
      "t-SNE Dimension 2",
      is3D
    );

    // Overview chart
    ChartManager.renderScatter(
      "chart-overview-tsne",
      coords,
      "t-Distributed Stochastic Neighbor Embedding (t-SNE)",
      "Dimension 1", "Dimension 2", false
    );
  }
};
