/**
 * Energy Intelligence — Main Application Orchestrator
 * Single-Page Dashboard Router, State Machine, and Report Exporter
 */

const AppState = {
  activeSection: 'section-overview',
  activeTarget: 'Zone1Power',
  datasetSummary: null,
  modelResults: null,
  forecastResults: null,
  optimizationResults: null,
};

const App = {
  async init() {
    console.log('Initializing Energy Intelligence Dashboard...');
    this.initRouter();
    this.initGlobalControls();
    DatasetManager.initEventListeners();
    ForecastController.initEventListeners();
    OptimizationController.initEventListeners();

    // Initial data load
    await DatasetManager.loadSummary();
    await this.loadPatterns();
    await this.loadPeaksAndAnomalies();
    await this.loadExperiments();

    // Initialize Lucide icons
    if (window.lucide) {
      lucide.createIcons();
    }
  },

  initRouter() {
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '') || 'overview';
      const sectionMap = {
        overview: 'section-overview',
        explorer: 'section-explorer',
        forecast: 'section-forecast',
        arena: 'section-arena',
        patterns: 'section-patterns',
        peaks: 'section-peaks',
        optimization: 'section-optimization',
        scenarios: 'section-scenarios',
        experiments: 'section-experiments',
        settings: 'section-settings'
      };

      const targetSection = sectionMap[hash] || 'section-overview';
      this.navigateTo(targetSection);
    };

    window.addEventListener('hashchange', handleHash);
    handleHash();

    // Mobile sidebar toggle
    const toggleBtn = document.getElementById('mobileToggleBtn');
    const sidebar = document.getElementById('sidebar');
    if (toggleBtn && sidebar) {
      toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  },

  navigateTo(sectionId) {
    AppState.activeSection = sectionId;

    // Toggle section visibility
    document.querySelectorAll('.page-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const activeSec = document.getElementById(sectionId);
    if (activeSec) {
      activeSec.classList.add('active');
    }

    // Toggle sidebar active state
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(link => {
      link.classList.toggle('active', link.dataset.section === sectionId);
    });

    // Update Topbar Breadcrumb Titles
    const titles = {
      'section-overview': { title: 'Overview', sub: 'Energy Intelligence Dashboard' },
      'section-explorer': { title: 'Data Explorer', sub: 'Dataset Hygiene & Preview' },
      'section-forecast': { title: 'Forecast Lab', sub: '24-Hour Predictive Horizon' },
      'section-arena': { title: 'Model Arena', sub: 'Cross-Algorithm Leaderboard' },
      'section-patterns': { title: 'Demand Patterns', sub: 'Diurnal Profiles & 24x7 Heatmap' },
      'section-peaks': { title: 'Peak & Anomalies', sub: 'Spike Screening & Statistical Outliers' },
      'section-optimization': { title: 'Optimization Lab', sub: 'Constrained Load Shifting (SciPy)' },
      'section-scenarios': { title: 'Scenario Comparison', sub: 'Peak & Cost Shifting Benchmarks' },
      'section-experiments': { title: 'Experiments & Reports', sub: 'Audit History & Executive Exports' },
      'section-settings': { title: 'Settings', sub: 'System Parameters & API Health' }
    };

    const meta = titles[sectionId] || { title: 'Energy Intelligence', sub: 'Lab' };
    const titleEl = document.getElementById('pageTitle');
    const subEl = document.getElementById('pageSubtitle');
    if (titleEl) titleEl.textContent = meta.title;
    if (subEl) subEl.textContent = meta.sub;

    // Close mobile drawer
    const sidebar = document.getElementById('sidebar');
    if (sidebar) sidebar.classList.remove('open');

    // Section specific refresh
    if (sectionId === 'section-patterns') this.loadPatterns();
    else if (sectionId === 'section-peaks') this.loadPeaksAndAnomalies();
    else if (sectionId === 'section-experiments') this.loadExperiments();

    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  initGlobalControls() {
    // Global Target Selector
    const targetSelect = document.getElementById('globalTargetSelect');
    if (targetSelect) {
      targetSelect.addEventListener('change', async (e) => {
        AppState.activeTarget = e.target.value;
        this.showToast(`Active Target changed to ${AppState.activeTarget}`);
        await DatasetManager.loadSummary();
        this.refreshActiveViews();
      });
    }

    // Export HTML Report Button
    const btnExportHtml = document.getElementById('btnExportHtml');
    if (btnExportHtml) {
      btnExportHtml.addEventListener('click', () => this.downloadReport('html'));
    }

    // Export CSV Forecast Button
    const btnExportCsv = document.getElementById('btnExportCsv');
    if (btnExportCsv) {
      btnExportCsv.addEventListener('click', () => this.downloadReport('csv'));
    }
  },

  async refreshActiveViews() {
    await this.loadPatterns();
    await this.loadPeaksAndAnomalies();
    if (AppState.activeSection === 'section-forecast' || AppState.activeSection === 'section-arena') {
      await ForecastController.trainModels();
    }
  },

  async loadPatterns() {
    try {
      const res = await fetch(`/api/patterns?target=${encodeURIComponent(AppState.activeTarget)}`);
      const data = await res.json();
      if (!data.success) return;

      ChartEngine.renderHourlyProfile('chartHourlyProfile', data.hourly_profile);
      ChartEngine.renderHeatmap('chartDemandHeatmap', data.heatmap);
    } catch (err) {
      console.error('Error loading patterns:', err);
    }
  },

  async loadPeaksAndAnomalies() {
    try {
      const res = await fetch(`/api/anomalies?target=${encodeURIComponent(AppState.activeTarget)}`);
      const data = await res.json();
      if (!data.success) return;

      // Populate Peaks Table
      const peakTbody = document.getElementById('peaksTableBody');
      if (peakTbody && data.peaks) {
        peakTbody.innerHTML = '';
        data.peaks.slice(0, 10).forEach(pk => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>${pk.timestamp}</strong></td>
            <td><span class="badge badge-rose">${pk.demand} kW</span></td>
            <td>+${pk.excess} kW</td>
          `;
          peakTbody.appendChild(tr);
        });
      }

      // Populate Anomalies Table
      const anomTbody = document.getElementById('anomaliesTableBody');
      if (anomTbody && data.anomalies) {
        anomTbody.innerHTML = '';
        data.anomalies.slice(0, 10).forEach(an => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td><strong>${an.timestamp}</strong></td>
            <td><strong>${an.demand} kW</strong></td>
            <td><span class="badge badge-amber">Z: +${an.z_score}</span></td>
          `;
          anomTbody.appendChild(tr);
        });
      }
    } catch (err) {
      console.error('Error loading peaks & anomalies:', err);
    }
  },

  async loadExperiments() {
    try {
      const res = await fetch('/api/experiments');
      const data = await res.json();
      if (!data.success) return;

      const tbody = document.getElementById('experimentsTableBody');
      if (!tbody || !data.experiments) return;

      tbody.innerHTML = '';
      data.experiments.forEach(exp => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${exp.timestamp}</strong></td>
          <td>${exp.target}</td>
          <td><span class="badge badge-teal">${exp.best_model}</span></td>
          <td>${exp.test_mae} kW</td>
          <td>${exp.test_rmse} kW</td>
          <td>${exp.test_wape}%</td>
        `;
        tbody.appendChild(tr);
      });
    } catch (err) {
      console.error('Error loading experiments:', err);
    }
  },

  async downloadReport(type = 'html') {
    this.showToast(`Generating ${type.toUpperCase()} executive export...`);
    try {
      const payload = {
        type: type,
        forecast_results: AppState.forecastResults,
        optimization_results: AppState.optimizationResults
      };

      const res = await fetch('/api/reports/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = type === 'html' ? 'energy_intelligence_report.html' : 'forecast_predictions_24h.csv';
      document.body.appendChild(a);
      a.click();
      a.remove();
      this.showToast(`${type.toUpperCase()} Report downloaded successfully!`);
    } catch (err) {
      this.showToast('Failed to download report', true);
    }
  },

  showToast(message, isError = false) {
    const toast = document.getElementById('toastPopup');
    const toastText = document.getElementById('toastText');
    if (!toast || !toastText) return;

    toastText.textContent = message;
    toast.className = `toast-popup visible ${isError ? 'error' : ''}`;

    setTimeout(() => {
      toast.classList.remove('visible');
    }, 3500);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
