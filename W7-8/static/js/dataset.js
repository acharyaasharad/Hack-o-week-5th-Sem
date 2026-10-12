/**
 * Energy Intelligence — Dataset Management & Explorer
 * Handles CSV ingestion, sample selection, data quality indicators, and preview tables.
 */

const DatasetManager = {
  async loadSummary() {
    try {
      const target = AppState.activeTarget;
      const res = await fetch(`/api/dataset/summary?target=${encodeURIComponent(target)}`);
      const data = await res.json();

      if (!data.success) {
        App.showToast(data.error || 'Failed to load dataset summary', true);
        return;
      }

      AppState.datasetSummary = data;
      this.updateSummaryUI(data);
    } catch (err) {
      console.error('Error fetching dataset summary:', err);
    }
  },

  updateSummaryUI(data) {
    // Topbar & sidebar indicators
    const sourceEl = document.getElementById('sidebarStatusText');
    if (sourceEl) sourceEl.textContent = data.source_name || 'Active Dataset';

    // Summary KPI elements
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val !== null && val !== undefined ? val : '—';
    };

    setVal('kpiRowCount', Number(data.row_count).toLocaleString());
    setVal('kpiFrequency', data.frequency);
    setVal('kpiCompleteness', `${data.completeness_score}%`);
    setVal('kpiDuplicates', data.duplicate_timestamps);
    setVal('kpiMissing', data.total_missing_values);
    setVal('kpiDateRange', `${data.start_time ? data.start_time.split(' ')[0] : '—'} to ${data.end_time ? data.end_time.split(' ')[0] : '—'}`);

    // Overview KPIs
    setVal('overviewDatasetRows', Number(data.row_count).toLocaleString());
    setVal('overviewDatasetFreq', data.frequency);

    // Update target dropdown if new targets discovered
    const targetSelect = document.getElementById('globalTargetSelect');
    if (targetSelect && data.available_targets) {
      const currentVal = targetSelect.value;
      targetSelect.innerHTML = '';
      data.available_targets.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        if (t === AppState.activeTarget || t === currentVal) opt.selected = true;
        targetSelect.appendChild(opt);
      });
    }

    // Refresh preview table
    this.loadPreview();
  },

  async loadPreview(limit = 15) {
    try {
      const res = await fetch(`/api/dataset/preview?limit=${limit}`);
      const data = await res.json();
      if (!data.success) return;

      const thead = document.getElementById('previewTableHeader');
      const tbody = document.getElementById('previewTableBody');
      if (!thead || !tbody) return;

      thead.innerHTML = '';
      tbody.innerHTML = '';

      // Render headers
      const trHead = document.createElement('tr');
      data.columns.forEach(col => {
        const th = document.createElement('th');
        th.textContent = col;
        trHead.appendChild(th);
      });
      thead.appendChild(trHead);

      // Render rows
      data.rows.forEach(row => {
        const tr = document.createElement('tr');
        data.columns.forEach(col => {
          const td = document.createElement('td');
          td.textContent = row[col] !== null ? row[col] : '—';
          tr.appendChild(td);
        });
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error('Error fetching preview table:', err);
    }
  },

  async loadSampleDataset(sampleName) {
    App.showToast(`Activating ${sampleName} dataset...`);
    try {
      const res = await fetch('/api/dataset/load-sample', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: sampleName })
      });
      const data = await res.json();
      if (data.success) {
        App.showToast(data.message);
        await this.loadSummary();
        App.refreshActiveViews();
      } else {
        App.showToast(data.error || 'Failed to switch dataset', true);
      }
    } catch (err) {
      App.showToast('Network error loading sample dataset', true);
    }
  },

  async handleFileUpload(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      App.showToast('Please select a valid CSV file.', true);
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    App.showToast(`Validating and uploading ${file.name}...`);
    try {
      const res = await fetch('/api/dataset/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        App.showToast(data.message);
        await this.loadSummary();
        App.refreshActiveViews();
      } else {
        App.showToast(data.error || 'Upload validation failed', true);
      }
    } catch (err) {
      App.showToast('Failed to upload CSV file', true);
    }
  },

  initEventListeners() {
    // Upload form
    const form = document.getElementById('datasetUploadForm');
    const fileInput = document.getElementById('csvFileInput');
    if (form && fileInput) {
      form.addEventListener('submit', (e) => {
        e.preventDefault();
        if (fileInput.files.length) {
          this.handleFileUpload(fileInput.files[0]);
        }
      });
    }

    // Sample dataset dropdown
    const sampleSelect = document.getElementById('sampleDatasetSelect');
    if (sampleSelect) {
      sampleSelect.addEventListener('change', (e) => {
        if (e.target.value) this.loadSampleDataset(e.target.value);
      });
    }
  }
};
