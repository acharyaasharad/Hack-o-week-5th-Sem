/* dataset.js — Dataset ingestion, CSV upload, and preview management */

const DatasetManager = {
  activeSummary: null,

  init() {
    this.bindEvents();
    this.fetchSummary();
  },

  bindEvents() {
    const dropzone = document.getElementById("csv-dropzone");
    const fileInput = document.getElementById("csv-file-input");

    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      
      dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("dragover");
      });

      dropzone.addEventListener("dragleave", () => {
        dropzone.classList.remove("dragover");
      });

      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
          this.uploadFile(e.dataTransfer.files[0]);
        }
      });

      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
          this.uploadFile(e.target.files[0]);
        }
      });
    }

    const loadUciBtn = document.getElementById("btn-load-uci");
    if (loadUciBtn) {
      loadUciBtn.addEventListener("click", () => this.loadBuiltinDataset(false));
    }

    const loadSampleBtn = document.getElementById("btn-load-sample");
    if (loadSampleBtn) {
      loadSampleBtn.addEventListener("click", () => this.loadBuiltinDataset(true));
    }

    const searchInput = document.getElementById("preview-search");
    if (searchInput) {
      searchInput.addEventListener("input", (e) => {
        this.fetchPreview(1, e.target.value);
      });
    }
  },

  async loadBuiltinDataset(synthetic = false) {
    App.showLoading(synthetic ? "Loading Synthetic Demonstration Dataset..." : "Loading UCI Wholesale Customers Dataset...");
    try {
      const res = await fetch(`/api/dataset/sample?synthetic=${synthetic}`);
      const data = await res.json();
      if (data.success) {
        this.activeSummary = data.summary;
        this.renderSummary();
        this.fetchPreview(1);
        App.notify(data.message, "success");
      } else {
        App.notify(data.message || "Failed to load dataset", "danger");
      }
    } catch (err) {
      App.notify("Error connecting to server", "danger");
    } finally {
      App.hideLoading();
    }
  },

  async uploadFile(file) {
    if (!file.name.endsWith(".csv")) {
      App.notify("Please upload a CSV file (.csv)", "warning");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    App.showLoading(`Uploading & Validating ${file.name}...`);
    try {
      const res = await fetch("/api/dataset/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (data.success) {
        this.activeSummary = data.summary;
        this.renderSummary();
        this.fetchPreview(1);
        App.notify(data.message, "success");
      } else {
        App.notify(data.message || "Upload failed", "danger");
      }
    } catch (err) {
      App.notify("Network error while uploading file", "danger");
    } finally {
      App.hideLoading();
    }
  },

  async fetchSummary() {
    try {
      const res = await fetch("/api/dataset/summary");
      const summary = await res.json();
      if (!summary.error) {
        this.activeSummary = summary;
        this.renderSummary();
        this.fetchPreview(1);
        this.fetchCorrelation();
      }
    } catch (err) {
      console.error("Failed to fetch dataset summary", err);
    }
  },

  renderSummary() {
    if (!this.activeSummary) return;
    const s = this.activeSummary;

    // Topbar Pill
    document.getElementById("topbar-dataset-name").textContent = s.dataset_name;
    document.getElementById("topbar-row-count").textContent = `${s.total_rows.toLocaleString()} rows`;

    // Overview Stats
    document.getElementById("stat-total-records").textContent = s.total_rows.toLocaleString();
    document.getElementById("stat-total-features").textContent = s.selected_features.length;

    // Data Explorer Metadata
    document.getElementById("meta-dataset-name").textContent = s.dataset_name;
    document.getElementById("meta-dataset-source").textContent = s.dataset_source;
    document.getElementById("meta-rows").textContent = s.total_rows.toLocaleString();
    document.getElementById("meta-cols").textContent = s.total_columns;
    document.getElementById("meta-missing").textContent = s.missing_values_count;
    document.getElementById("meta-duplicates").textContent = s.duplicate_rows_count;

    // Warnings
    const warnContainer = document.getElementById("dataset-warnings-container");
    if (warnContainer) {
      if (s.warnings && s.warnings.length > 0) {
        warnContainer.innerHTML = s.warnings.map(w => `<div class="alert alert-warning">${w}</div>`).join("");
      } else {
        warnContainer.innerHTML = `<div class="alert alert-info">Data Quality Check Passed: No missing values, empty columns, or duplicate rows detected.</div>`;
      }
    }

    // Populate Column Statistics Table
    this.renderColumnStatsTable(s.column_stats);

    // Preprocessing Feature Checkboxes
    this.populateFeatureSelectors(s);
  },

  renderColumnStatsTable(colStats) {
    const tbody = document.getElementById("column-stats-tbody");
    if (!tbody || !colStats) return;

    tbody.innerHTML = Object.entries(colStats).map(([col, stats]) => {
      return `
        <tr>
          <td><strong>${col}</strong></td>
          <td><span class="badge ${stats.is_numeric ? 'badge-info' : 'badge-warning'}">${stats.dtype}</span></td>
          <td>${stats.missing}</td>
          <td>${stats.unique_values}</td>
          <td>${stats.is_numeric ? `$${stats.mean?.toLocaleString() || '-'}` : 'N/A'}</td>
          <td>${stats.is_numeric ? `$${stats.median?.toLocaleString() || '-'}` : 'N/A'}</td>
          <td>${stats.is_numeric ? `$${stats.min?.toLocaleString() || '-'}` : 'N/A'}</td>
          <td>${stats.is_numeric ? `$${stats.max?.toLocaleString() || '-'}` : 'N/A'}</td>
        </tr>
      `;
    }).join("");
  },

  populateFeatureSelectors(s) {
    const numContainer = document.getElementById("numeric-features-checkboxes");
    if (numContainer) {
      numContainer.innerHTML = s.numeric_columns.map(col => {
        const isChecked = s.selected_features.includes(col);
        return `
          <label class="form-checkbox-label" style="margin-right: 14px; margin-bottom: 8px;">
            <input type="checkbox" name="numeric_feature" value="${col}" ${isChecked ? 'checked' : ''}>
            ${col}
          </label>
        `;
      }).join("");
    }

    const catContainer = document.getElementById("categorical-features-checkboxes");
    if (catContainer) {
      if (s.categorical_columns.length === 0) {
        catContainer.innerHTML = "<span class='text-muted' style='font-size:12px;'>No categorical columns in current dataset</span>";
      } else {
        catContainer.innerHTML = s.categorical_columns.map(col => {
          return `
            <label class="form-checkbox-label" style="margin-right: 14px; margin-bottom: 8px;">
              <input type="checkbox" name="categorical_feature" value="${col}">
              ${col}
            </label>
          `;
        }).join("");
      }
    }
  },

  async fetchPreview(page = 1, search = "") {
    try {
      const res = await fetch(`/api/dataset/preview?page=${page}&page_size=12&search=${encodeURIComponent(search)}`);
      const preview = await res.json();
      if (!preview.error) {
        this.renderPreviewTable(preview);
      }
    } catch (err) {
      console.error("Preview fetch error", err);
    }
  },

  renderPreviewTable(p) {
    const thead = document.getElementById("preview-thead");
    const tbody = document.getElementById("preview-tbody");
    if (!thead || !tbody) return;

    thead.innerHTML = `<tr>${p.columns.map(c => `<th>${c}</th>`).join("")}</tr>`;
    tbody.innerHTML = p.data.map(row => {
      return `<tr>${p.columns.map(c => `<td>${row[c] !== null ? row[c] : '-'}</td>`).join("")}</tr>`;
    }).join("");

    // Pagination info
    const info = document.getElementById("preview-pagination-info");
    if (info) {
      info.textContent = `Showing page ${p.page} of ${p.total_pages} (${p.total_records} rows)`;
    }
  },

  async fetchCorrelation() {
    try {
      const res = await fetch("/api/visualization/correlation");
      const corrData = await res.json();
      ChartManager.renderCorrelationHeatmap("chart-correlation-heatmap", corrData);
    } catch (err) {
      console.error("Correlation fetch error", err);
    }
  }
};
