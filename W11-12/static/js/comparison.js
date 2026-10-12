/* comparison.js — Side-by-side PCA and t-SNE common sample benchmarking */

const ComparisonManager = {
  lastResult: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const btnCompare = document.getElementById("btn-run-comparison");
    if (btnCompare) {
      btnCompare.addEventListener("click", () => this.runComparison());
    }
  },

  async runComparison() {
    const features = PreprocessingManager.getSelectedFeatures();
    if (features.length < 2) {
      App.notify("Select at least 2 features for comparison.", "warning");
      return;
    }

    const { scaler, logTransform } = PreprocessingManager.getPreprocessingConfig();
    const colorBy = document.getElementById("compare-color-by").value;
    const perplexity = parseFloat(document.getElementById("compare-perplexity").value || 30);

    App.showLoading("Benchmarking PCA & t-SNE on aligned observation set...");
    try {
      const res = await fetch("/api/compare/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          features: features,
          perplexity: perplexity,
          scaler: scaler,
          log_transform: logTransform,
          color_by: colorBy,
        }),
      });

      const data = await res.json();
      if (data.status === "success") {
        this.lastResult = data;
        this.renderOutput(data);
        App.notify("Comparison completed successfully!", "success");
      } else {
        App.notify(data.message || "Comparison failed", "danger");
      }
    } catch (err) {
      App.notify("Error executing comparison benchmark", "danger");
    } finally {
      App.hideLoading();
    }
  },

  renderOutput(data) {
    const pca = data.pca;
    const tsne = data.tsne;

    // Side-by-side stats
    document.getElementById("stat-comp-samples").textContent = data.n_samples;
    document.getElementById("stat-comp-features").textContent = data.n_features;
    document.getElementById("stat-comp-pca-var").textContent = `${pca.total_2d_variance}%`;
    document.getElementById("stat-comp-pca-time").textContent = `${pca.execution_time_seconds}s`;
    document.getElementById("stat-comp-tsne-perp").textContent = tsne.perplexity;
    document.getElementById("stat-comp-tsne-time").textContent = `${tsne.execution_time_seconds}s`;

    // Render side-by-side charts with stable color mappings
    ChartManager.renderScatter(
      "chart-compare-pca",
      pca.coordinates,
      `PCA (2D Variance: ${pca.total_2d_variance}%)`,
      "PC1", "PC2", false
    );

    ChartManager.renderScatter(
      "chart-compare-tsne",
      tsne.coordinates,
      `t-SNE (Perplexity: ${tsne.perplexity})`,
      "Dim 1", "Dim 2", false
    );
  }
};
