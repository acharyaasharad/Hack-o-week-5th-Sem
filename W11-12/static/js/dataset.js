/* dataset.js — Dataset loading, drag-and-drop CSV upload, and preview pagination */

const DatasetManager = {
  activeSummary: null,

  init() {
    this.bindEvents();
    this.fetchSummary();
  },

  bindEvents() {
    const selectDataset = document.getElementById("select-builtin-dataset");
    if (selectDataset) {
      selectDataset.addEventListener("change", (e) => this.loadBuiltin(e.target.value));
    }

    const dropzone = document.getElementById("csv-dropzone");
    const fileInput = document.getElementById("csv-file-input");
    if (dropzone && fileInput) {
      dropzone.addEventListener("click", () => fileInput.click());
      dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
      dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
      dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) this.uploadCSV(e.dataTransfer.files[0]);
      });
      fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) this.uploadCSV(e.target.files[0]);
      });
    }

    const previewSearch = document.getElementById("preview-search");
    if (previewSearch) {
      previewSearch.addEventListener("input", (e) => this.fetchPreview(1, e.target.value));
    }
  },

  async loadBuiltin(datasetId) {
    App.showLoading(`Loading ${datasetId.toUpperCase()} dataset...`);
    try {
      const res = await fetch("/api/dataset/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId }),
      });
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

  async uploadCSV(file) {
    if (!file.name.endsWith(".csv")) {
      App.notify("Please upload a .csv file", "warning");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    App.showLoading(`Uploading & validating ${file.name}...`);
    try {
      const res = await fetch("/api/dataset/upload", { method: "POST", body: formData });
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
      App.notify("Network error during upload", "danger");
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
      }
    } catch (err) {
      console.error("Summary fetch error", err);
    }
  },

  renderSummary() {
    if (!this.activeSummary) return;
    const s = this.activeSummary;

    // Topbar Pill
    document.getElementById("topbar-dataset-name").textContent = s.dataset_name;
    document.getElementById("topbar-row-count").textContent = `(${s.total_rows} rows)`;

    // Overview Stats
    document.getElementById("stat-total-records").textContent = s.total_rows.toLocaleString();
    document.getElementById("stat-total-features").textContent = s.selected_features.length;

    // Explorer Metadata
    document.getElementById("meta-dataset-name").textContent = s.dataset_name;
    document.getElementById("meta-dataset-source").textContent = s.dataset_source;
    document.getElementById("meta-rows").textContent = s.total_rows.toLocaleString();
    document.getElementById("meta-cols").textContent = s.total_columns;
    document.getElementById("meta-missing").textContent = s.missing_values_count;
    document.getElementById("meta-duplicates").textContent = s.duplicate_rows_count;

    // Warnings
    const warnBox = document.getElementById("dataset-warnings-container");
    if (warnBox) {
      if (s.warnings && s.warnings.length > 0) {
        warnBox.innerHTML = s.warnings.map(w => `<div class="alert alert-warning">${w}</div>`).join("");
      } else {
        warnBox.innerHTML = `<div class="alert alert-info">Data Quality Verified: No missing values or duplicates detected.</div>`;
      }
    }

    // Populate Column Stats Table
    this.renderColumnStats(s.column_stats);

    // Populate Preprocessing Feature Checkboxes & Color-by Dropdowns
    this.populateSelectors(s);
  },

  renderColumnStats(stats) {
    const tbody = document.getElementById("column-stats-tbody");
    if (!tbody || !stats) return;

    tbody.innerHTML = Object.entries(stats).map(([col, c]) => {
      return `
        <tr>
          <td><strong>${col}</strong></td>
          <td><span class="badge ${c.is_numeric ? 'badge-info' : 'badge-warning'}">${c.dtype}</span></td>
          <td>${c.missing}</td>
          <td>${c.unique}</td>
          <td>${c.is_numeric ? c.mean?.toFixed(3) : '-'}</td>
          <td>${c.is_numeric ? c.std?.toFixed(3) : '-'}</td>
          <td>${c.is_numeric ? c.min?.toFixed(3) : '-'}</td>
          <td>${c.is_numeric ? c.max?.toFixed(3) : '-'}</td>
        </tr>
      `;
    }).join("");
  },

  populateSelectors(s) {
    // Feature checkboxes
    const numContainer = document.getElementById("numeric-features-container");
    if (numContainer) {
      numContainer.innerHTML = s.numeric_columns.map(col => {
        const isChecked = s.selected_features.includes(col);
        return `
          <label class="form-checkbox-label" style="margin-right: 14px; margin-bottom: 8px;">
            <input type="checkbox" name="pca_feature" value="${col}" ${isChecked ? 'checked' : ''}>
            ${col}
          </label>
        `;
      }).join("");
    }

    // Color by dropdowns in PCA, t-SNE, Compare
    const colorSelects = [
      document.getElementById("pca-color-by"),
      document.getElementById("tsne-color-by"),
      document.getElementById("compare-color-by"),
    ];

    const availableColors = [...s.categorical_columns, ...s.numeric_columns];
    colorSelects.forEach(sel => {
      if (!sel) return;
      sel.innerHTML = `<option value="">None (Uniform Color)</option>` +
        availableColors.map(c => `<option value="${c}" ${c === s.color_column ? 'selected' : ''}>${c}</option>`).join("");
    });
  },

  async fetchPreview(page = 1, search = "") {
    try {
      const res = await fetch(`/api/dataset/preview?page=${page}&page_size=12&search=${encodeURIComponent(search)}`);
      const p = await res.json();
      if (!p.error) this.renderPreviewTable(p);
    } catch (err) {
      console.error("Preview error", err);
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

    const info = document.getElementById("preview-pagination-info");
    if (info) info.textContent = `Showing page ${p.page} of ${p.total_pages} (${p.total_records} rows)`;
  }
};
