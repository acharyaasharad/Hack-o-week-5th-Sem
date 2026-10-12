/* clustering.js — Clustering execution, model comparison, elbow analysis, and customer lookup */

const ClusteringManager = {
  lastResult: null,

  init() {
    this.bindEvents();
    this.fetchInitialResults();
  },

  bindEvents() {
    // Algorithm dropdown toggle
    const algoSelect = document.getElementById("select-algorithm");
    if (algoSelect) {
      algoSelect.addEventListener("change", (e) => this.toggleAlgorithmParams(e.target.value));
    }

    // Run Clustering Button
    const runBtn = document.getElementById("btn-run-clustering");
    if (runBtn) {
      runBtn.addEventListener("click", () => this.runClustering());
    }

    // Compare Models Button
    const compareBtn = document.getElementById("btn-compare-models");
    if (compareBtn) {
      compareBtn.addEventListener("click", () => this.runModelComparison());
    }

    // Elbow Curve Button
    const elbowBtn = document.getElementById("btn-compute-elbow");
    if (elbowBtn) {
      elbowBtn.addEventListener("click", () => this.fetchElbowCurve());
    }

    // Dendrogram Button
    const dendroBtn = document.getElementById("btn-compute-dendrogram");
    if (dendroBtn) {
      dendroBtn.addEventListener("click", () => this.fetchDendrogram());
    }

    // Customer Lookup Form
    const lookupForm = document.getElementById("customer-lookup-form");
    if (lookupForm) {
      lookupForm.addEventListener("submit", (e) => {
        e.preventDefault();
        this.runCustomerLookup();
      });
    }

    // Cluster selector in Cluster Explorer
    const clusterSelect = document.getElementById("cluster-explorer-select");
    if (clusterSelect) {
      clusterSelect.addEventListener("change", (e) => this.renderSelectedClusterDetails(e.target.value));
    }
  },

  toggleAlgorithmParams(algo) {
    document.getElementById("params-kmeans").style.display = (algo === "kmeans") ? "block" : "none";
    document.getElementById("params-hierarchical").style.display = (algo === "hierarchical") ? "block" : "none";
    document.getElementById("params-dbscan").style.display = (algo === "dbscan") ? "block" : "none";
  },

  getSelectedNumericFeatures() {
    const checkboxes = document.querySelectorAll("input[name='numeric_feature']:checked");
    return Array.from(checkboxes).map(cb => cb.value);
  },

  getSelectedCategoricalFeatures() {
    const checkboxes = document.querySelectorAll("input[name='categorical_feature']:checked");
    return Array.from(checkboxes).map(cb => cb.value);
  },

  async runClustering() {
    const algo = document.getElementById("select-algorithm").value;
    const scaling = document.getElementById("select-scaling-method").value;
    const logTransform = document.getElementById("checkbox-log-transform").checked;
    const imputeStrategy = document.getElementById("select-impute-strategy").value;

    const numericFeatures = this.getSelectedNumericFeatures();
    const categoricalFeatures = this.getSelectedCategoricalFeatures();

    if (numericFeatures.length < 2) {
      App.notify("Please select at least 2 numeric features for clustering.", "warning");
      return;
    }

    // Gather algorithm parameters
    const params = {};
    if (algo === "kmeans") {
      params.n_clusters = parseInt(document.getElementById("kmeans-k").value, 10);
      params.n_init = parseInt(document.getElementById("kmeans-n-init").value, 10);
      params.max_iter = parseInt(document.getElementById("kmeans-max-iter").value, 10);
      params.random_state = parseInt(document.getElementById("kmeans-seed").value, 10);
    } else if (algo === "hierarchical") {
      params.n_clusters = parseInt(document.getElementById("hierarchical-k").value, 10);
      params.linkage = document.getElementById("hierarchical-linkage").value;
    } else if (algo === "dbscan") {
      params.eps = parseFloat(document.getElementById("dbscan-eps").value);
      params.min_samples = parseInt(document.getElementById("dbscan-min-samples").value, 10);
    }

    App.showLoading(`Fitting ${algo.toUpperCase()} scikit-learn Pipeline...`);
    try {
      const res = await fetch("/api/clustering/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          algorithm: algo,
          params: params,
          numeric_features: numericFeatures,
          categorical_features: categoricalFeatures,
          scaling_method: scaling,
          log_transform: logTransform,
          numeric_impute_strategy: imputeStrategy,
        }),
      });

      const data = await res.json();
      if (data.status === "success") {
        this.lastResult = data;
        this.renderClusteringOutput(data);
        App.notify(`Successfully completed ${data.algorithm_name} in ${data.execution_time_seconds}s!`, "success");
      } else {
        App.notify(data.message || "Clustering run failed", "danger");
      }
    } catch (err) {
      App.notify("Error executing clustering model", "danger");
    } finally {
      App.hideLoading();
    }
  },

  renderClusteringOutput(r) {
    // Update Overview & Lab Metric Cards
    document.getElementById("stat-cluster-count").textContent = r.cluster_count;
    document.getElementById("stat-noise-pct").textContent = `${r.noise_percentage}%`;
    document.getElementById("stat-active-algo").textContent = r.algorithm_name;
    document.getElementById("stat-exec-time").textContent = `${r.execution_time_seconds}s`;

    // Metrics
    const sil = r.metrics.silhouette_score;
    const db = r.metrics.davies_bouldin_index;
    const ch = r.metrics.calinski_harabasz_score;

    document.getElementById("val-silhouette").textContent = sil !== null ? sil : "N/A";
    document.getElementById("val-davies-bouldin").textContent = db !== null ? db : "N/A";
    document.getElementById("val-calinski").textContent = ch !== null ? ch : "N/A";

    // Warnings
    const warnBox = document.getElementById("clustering-warnings-box");
    if (warnBox) {
      if (r.warnings && r.warnings.length > 0) {
        warnBox.innerHTML = r.warnings.map(w => `<div class="alert alert-warning">${w}</div>`).join("");
      } else {
        warnBox.innerHTML = "";
      }
    }

    // Render Charts
    ChartManager.renderClusterSizeBar("chart-cluster-sizes", r.cluster_sizes);
    ChartManager.renderPcaScatter("chart-pca-scatter", r.pca_visualization);

    if (r.profiles) {
      ChartManager.renderSpendingProfileRadar(
        "chart-radar-profiles",
        r.profiles,
        r.preprocessing.numeric_features
      );
      this.populateClusterExplorer(r.profiles);
    }
  },

  populateClusterExplorer(profiles) {
    const select = document.getElementById("cluster-explorer-select");
    if (!select || !profiles || !profiles.clusters) return;

    select.innerHTML = Object.keys(profiles.clusters).map(name => {
      return `<option value="${name}">${name}</option>`;
    }).join("");

    const firstCluster = Object.keys(profiles.clusters)[0];
    if (firstCluster) {
      this.renderSelectedClusterDetails(firstCluster);
    }
  },

  renderSelectedClusterDetails(clusterName) {
    if (!this.lastResult || !this.lastResult.profiles) return;
    const cdata = this.lastResult.profiles.clusters[clusterName];
    if (!cdata) return;

    document.getElementById("cluster-detail-name").textContent = clusterName;
    document.getElementById("cluster-detail-count").textContent = `${cdata.customer_count} customers (${cdata.percentage_of_total}%)`;
    document.getElementById("cluster-detail-desc").textContent = cdata.derived_description;

    // Actions list
    const actionList = document.getElementById("cluster-detail-actions");
    if (actionList) {
      actionList.innerHTML = cdata.suggested_actions.map(a => `<li>${a}</li>`).join("");
    }

    // Spending Averages Table
    const tbody = document.getElementById("cluster-spend-tbody");
    if (tbody) {
      tbody.innerHTML = Object.keys(cdata.means).map(f => {
        const mean = cdata.means[f];
        const med = cdata.medians[f];
        const rel = cdata.relative_index[f];
        const badgeClass = rel >= 1.2 ? 'badge-success' : rel <= 0.8 ? 'badge-warning' : 'badge-info';
        return `
          <tr>
            <td><strong>${f}</strong></td>
            <td>$${mean.toLocaleString()}</td>
            <td>$${med.toLocaleString()}</td>
            <td><span class="badge ${badgeClass}">${rel}x mean</span></td>
          </tr>
        `;
      }).join("");
    }

    // Fetch customer observations for this cluster
    this.fetchClusterCustomers(cdata.cluster_id);
  },

  async fetchClusterCustomers(cid) {
    try {
      const res = await fetch(`/api/clustering/cluster/${cid}?page=1&page_size=8`);
      const data = await res.json();
      const tbody = document.getElementById("cluster-customers-tbody");
      if (tbody && data.records) {
        const cols = Object.keys(data.records[0] || {});
        const thead = document.getElementById("cluster-customers-thead");
        if (thead) thead.innerHTML = `<tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>`;
        tbody.innerHTML = data.records.map(row => {
          return `<tr>${cols.map(c => `<td>${row[c]}</td>`).join("")}</tr>`;
        }).join("");
      }
    } catch (err) {
      console.error("Cluster customer fetch error", err);
    }
  },

  async fetchElbowCurve() {
    App.showLoading("Computing K-Means Elbow Curve (k=2..10)...");
    try {
      const scaling = document.getElementById("select-scaling-method").value;
      const logTransform = document.getElementById("checkbox-log-transform").checked;
      const res = await fetch(`/api/clustering/elbow?scaling_method=${scaling}&log_transform=${logTransform}`);
      const data = await res.json();
      ChartManager.renderElbowCurve("chart-elbow-curve", data);
      App.notify("Elbow curve updated.", "success");
    } catch (err) {
      App.notify("Failed to compute elbow curve", "danger");
    } finally {
      App.hideLoading();
    }
  },

  async fetchDendrogram() {
    App.showLoading("Calculating SciPy Hierarchical Dendrogram...");
    try {
      const linkage = document.getElementById("hierarchical-linkage").value;
      const scaling = document.getElementById("select-scaling-method").value;
      const logTransform = document.getElementById("checkbox-log-transform").checked;
      const res = await fetch(`/api/clustering/dendrogram?linkage=${linkage}&scaling_method=${scaling}&log_transform=${logTransform}`);
      const data = await res.json();
      ChartManager.renderDendrogram("chart-dendrogram", data);
      App.notify("Dendrogram updated.", "success");
    } catch (err) {
      App.notify("Failed to calculate dendrogram", "danger");
    } finally {
      App.hideLoading();
    }
  },

  async runModelComparison() {
    App.showLoading("Benchmarking K-Means, Hierarchical & DBSCAN Models...");
    try {
      const scaling = document.getElementById("select-scaling-method").value;
      const logTransform = document.getElementById("checkbox-log-transform").checked;
      const res = await fetch("/api/clustering/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scaling_method: scaling, log_transform: logTransform }),
      });
      const data = await res.json();
      this.renderComparisonTable(data.comparison);
      App.notify("Model comparison benchmarking completed.", "success");
    } catch (err) {
      App.notify("Model comparison failed", "danger");
    } finally {
      App.hideLoading();
    }
  },

  renderComparisonTable(rows) {
    const tbody = document.getElementById("comparison-table-tbody");
    if (!tbody || !rows) return;

    tbody.innerHTML = rows.map((r, i) => {
      const sil = r.silhouette_score !== null ? r.silhouette_score : "-";
      const db = r.davies_bouldin_index !== null ? r.davies_bouldin_index : "-";
      const ch = r.calinski_harabasz_score !== null ? r.calinski_harabasz_score : "-";
      const paramStr = Object.entries(r.parameters).map(([k,v]) => `${k}=${v}`).join(", ");
      return `
        <tr>
          <td><strong>${r.algorithm_name}</strong></td>
          <td><code>${paramStr}</code></td>
          <td>${r.cluster_count}</td>
          <td>${r.noise_percentage}%</td>
          <td><strong>${sil}</strong></td>
          <td>${db}</td>
          <td>${ch}</td>
          <td>${r.execution_time_seconds}s</td>
        </tr>
      `;
    }).join("");
  },

  async runCustomerLookup() {
    const fresh = parseFloat(document.getElementById("lookup-fresh").value || 0);
    const milk = parseFloat(document.getElementById("lookup-milk").value || 0);
    const grocery = parseFloat(document.getElementById("lookup-grocery").value || 0);
    const frozen = parseFloat(document.getElementById("lookup-frozen").value || 0);
    const detergents = parseFloat(document.getElementById("lookup-detergents").value || 0);
    const delicassen = parseFloat(document.getElementById("lookup-delicassen").value || 0);

    const payload = {
      Fresh: fresh,
      Milk: milk,
      Grocery: grocery,
      Frozen: frozen,
      Detergents_Paper: detergents,
      Delicassen: delicassen,
    };

    try {
      const res = await fetch("/api/clustering/customer-lookup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      const resDiv = document.getElementById("customer-lookup-result");
      if (data.supported) {
        resDiv.innerHTML = `
          <div class="alert alert-info">
            <strong>${data.message}</strong><br>
            Centroid Distance: ${data.distance_to_centroid} (in scaled feature space).
          </div>
        `;
      } else {
        resDiv.innerHTML = `<div class="alert alert-warning">${data.message}</div>`;
      }
    } catch (err) {
      App.notify("Lookup request failed", "danger");
    }
  },

  async fetchInitialResults() {
    try {
      const res = await fetch("/api/clustering/results");
      const data = await res.json();
      if (data.status === "success") {
        this.lastResult = data;
        this.renderClusteringOutput(data);
      }
    } catch (err) {
      console.error("Initial clustering results fetch error", err);
    }
  }
};
