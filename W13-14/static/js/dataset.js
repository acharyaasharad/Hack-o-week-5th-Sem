/**
 * dataset.js - Handles dataset loading, preview, feature selection, and leakage warnings
 */

const DatasetManager = {
  activeDataset: null,
  activeTask: 'classification',
  columns: [],

  init() {
    this.bindEvents();
    this.loadBuiltinList();
  },

  bindEvents() {
    const loadBtn = document.getElementById('btn-load-dataset');
    if (loadBtn) {
      loadBtn.addEventListener('click', () => {
        const sel = document.getElementById('select-builtin-dataset').value;
        this.loadDataset(sel);
      });
    }

    const uploadInput = document.getElementById('input-csv-upload');
    if (uploadInput) {
      uploadInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
          this.uploadCSV(e.target.files[0]);
        }
      });
    }

    const targetSelect = document.getElementById('select-target-column');
    if (targetSelect) {
      targetSelect.addEventListener('change', () => {
        this.onTargetChange();
      });
    }

    const taskSelect = document.getElementById('select-task-type');
    if (taskSelect) {
      taskSelect.addEventListener('change', (e) => {
        this.activeTask = e.target.value;
        App.updateTaskBadge(this.activeTask);
        ModelArena.fetchAvailableModels();
      });
    }
  },

  async loadBuiltinList() {
    try {
      const res = await fetch('/api/datasets');
      const data = await res.json();
      const select = document.getElementById('select-builtin-dataset');
      if (select && data.datasets) {
        select.innerHTML = '';
        data.datasets.forEach(d => {
          const opt = document.createElement('option');
          opt.value = d.id;
          opt.textContent = `${d.name} (${d.task})`;
          select.appendChild(opt);
        });
      }
    } catch (err) {
      console.error('Failed to load dataset list', err);
    }
  },

  async loadDataset(datasetId) {
    App.showLoading(true, `Loading dataset: ${datasetId}...`);
    try {
      const res = await fetch('/api/dataset/load', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dataset_id: datasetId })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.activeDataset = data.dataset_id;
        this.activeTask = data.task;
        this.columns = data.columns;
        this.renderDatasetSummary(data);
        this.loadPreview();
        App.updateTaskBadge(this.activeTask);
        App.updateDatasetBadge(data.dataset_name);
        ModelArena.fetchAvailableModels();
        App.showNotification('Dataset loaded successfully!', 'success');
      } else {
        App.showNotification(data.error || 'Failed to load dataset', 'danger');
      }
    } catch (err) {
      App.showNotification('Network error loading dataset: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  async uploadCSV(file) {
    App.showLoading(true, 'Uploading and validating CSV...');
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/dataset/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.activeDataset = data.dataset_id;
        this.activeTask = data.task;
        this.columns = data.columns;
        this.renderDatasetSummary(data);
        this.loadPreview();
        App.updateTaskBadge(this.activeTask);
        App.updateDatasetBadge(data.dataset_name);
        ModelArena.fetchAvailableModels();
        App.showNotification('CSV uploaded and validated successfully!', 'success');
      } else {
        App.showNotification(data.error || 'Upload error', 'danger');
      }
    } catch (err) {
      App.showNotification('Error uploading file: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  async loadPreview() {
    try {
      const res = await fetch('/api/dataset/preview?page=1&per_page=10');
      const data = await res.json();
      if (data.status === 'success') {
        this.renderPreviewTable(data.columns, data.rows);
      }
    } catch (err) {
      console.error('Preview error', err);
    }
  },

  renderDatasetSummary(summary) {
    document.getElementById('summary-row-count').textContent = summary.row_count || '-';
    document.getElementById('summary-col-count').textContent = summary.column_count || '-';
    document.getElementById('summary-task').textContent = summary.task ? summary.task.toUpperCase() : '-';

    // Target select
    const targetSelect = document.getElementById('select-target-column');
    targetSelect.innerHTML = '';
    summary.columns.forEach(col => {
      const opt = document.createElement('option');
      opt.value = col.name;
      opt.textContent = `${col.name} (${col.type})`;
      if (col.name === summary.target) opt.selected = true;
      targetSelect.appendChild(opt);
    });

    // Task select sync
    const taskSelect = document.getElementById('select-task-type');
    if (taskSelect) taskSelect.value = summary.task;

    // Feature chips with leakage checks
    this.renderFeatureChips(summary.columns, summary.target, summary.excluded_columns || []);

    // Warnings display
    const warnBox = document.getElementById('dataset-leakage-warnings');
    if (summary.leakage_warnings && summary.leakage_warnings.length > 0) {
      warnBox.innerHTML = summary.leakage_warnings.map(w => `<div class="alert alert-warning">⚠️ <strong>Leakage Warning:</strong> ${w}</div>`).join('');
      warnBox.style.display = 'block';
    } else {
      warnBox.innerHTML = '';
      warnBox.style.display = 'none';
    }
  },

  renderFeatureChips(columns, target, excluded) {
    const chipBox = document.getElementById('feature-chips-container');
    chipBox.innerHTML = '';

    columns.forEach(col => {
      if (col.name === target) return; // skip target

      const label = document.createElement('label');
      label.className = 'chip';
      const isChecked = !excluded.includes(col.name);

      label.innerHTML = `
        <input type="checkbox" value="${col.name}" ${isChecked ? 'checked' : ''}>
        <span>${col.name} <small style="color:#64748b">(${col.type})</small></span>
      `;
      chipBox.appendChild(label);
    });
  },

  onTargetChange() {
    const target = document.getElementById('select-target-column').value;
    const excluded = [];
    if (this.activeDataset === 'uci_bank_marketing') excluded.push('duration');
    if (this.activeDataset === 'uci_bike_sharing') excluded.push('casual', 'registered');
    this.renderFeatureChips(this.columns, target, excluded);
  },

  getSelectedFeatures() {
    const chipBox = document.getElementById('feature-chips-container');
    const checked = chipBox.querySelectorAll('input[type="checkbox"]:checked');
    return Array.from(checked).map(cb => cb.value);
  },

  renderPreviewTable(columns, rows) {
    const thead = document.getElementById('preview-table-head');
    const tbody = document.getElementById('preview-table-body');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    const trHead = document.createElement('tr');
    columns.forEach(col => {
      const th = document.createElement('th');
      th.textContent = col;
      trHead.appendChild(th);
    });
    thead.appendChild(trHead);

    rows.forEach(row => {
      const tr = document.createElement('tr');
      columns.forEach(col => {
        const td = document.createElement('td');
        td.textContent = row[col] !== null ? row[col] : '-';
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
  }
};
