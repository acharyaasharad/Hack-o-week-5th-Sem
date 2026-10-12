/**
 * app.js - Main Application Controller, navigation, tabs, notifications, and initialization
 */

const App = {
  trainedModelCount: 0,

  init() {
    this.bindNavigation();
    this.bindAccordions();
    this.checkHealth();

    // Initialize submodules
    DatasetManager.init();
    ModelArena.init();
    GeneralizationLab.init();
    RegularizationLab.init();
    PredictionPlayground.init();
    ReportManager.init();
  },

  bindNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetTab = link.getAttribute('data-tab');
        this.switchTab(targetTab);
      });
    });
  },

  switchTab(tabId) {
    // Nav links
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    const activeLink = document.querySelector(`.nav-link[data-tab="${tabId}"]`);
    if (activeLink) activeLink.classList.add('active');

    // Panes
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    const targetPane = document.getElementById(tabId);
    if (targetPane) targetPane.classList.add('active');

    // Trigger chart resize if Plotly container exists in view
    window.dispatchEvent(new Event('resize'));
  },

  bindAccordions() {
    const accordions = document.querySelectorAll('.accordion-header');
    accordions.forEach(h => {
      h.addEventListener('click', () => {
        h.parentElement.classList.toggle('active');
      });
    });
  },

  async checkHealth() {
    try {
      const res = await fetch('/api/health');
      const data = await res.json();
      const statusBadge = document.getElementById('topbar-health-status');
      if (statusBadge) {
        statusBadge.textContent = data.status === 'healthy' ? 'System Ready' : 'Issues Detected';
        statusBadge.style.color = data.status === 'healthy' ? '#10b981' : '#ef4444';
      }
    } catch (err) {
      console.error('Health check failed', err);
    }
  },

  updateTaskBadge(task) {
    const badge = document.getElementById('topbar-task-badge');
    if (badge) {
      badge.textContent = task.toUpperCase();
      badge.className = `badge badge-${task}`;
    }
  },

  updateDatasetBadge(name) {
    const el = document.getElementById('topbar-dataset-name');
    if (el) el.textContent = name;
    const ovEl = document.getElementById('ov-dataset-name');
    if (ovEl) ovEl.textContent = name;
  },

  updateTrainedCount(count) {
    this.trainedModelCount = count;
    const el = document.getElementById('ov-models-count');
    if (el) el.textContent = count;
  },

  showLoading(show, message = 'Processing...') {
    const overlay = document.getElementById('loading-overlay');
    const msgEl = document.getElementById('loading-message');
    if (overlay) {
      overlay.style.display = show ? 'flex' : 'none';
      if (msgEl) msgEl.textContent = message;
    }
  },

  showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notif = document.createElement('div');
    notif.className = `alert alert-${type}`;
    notif.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    notif.style.marginBottom = '8px';
    notif.style.minWidth = '280px';
    notif.innerHTML = message;

    container.appendChild(notif);
    setTimeout(() => {
      notif.style.opacity = '0';
      notif.style.transition = 'opacity 0.4s';
      setTimeout(() => notif.remove(), 400);
    }, 4000);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
