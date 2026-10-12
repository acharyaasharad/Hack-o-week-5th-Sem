/**
 * reports.js - Handles exporting model comparison CSV and generating standalone HTML reports
 */

const ReportManager = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const exportCsvBtn = document.getElementById('btn-export-comparison-csv');
    if (exportCsvBtn) {
      exportCsvBtn.addEventListener('click', () => {
        this.exportComparisonCSV();
      });
    }

    const exportHtmlBtn = document.getElementById('btn-export-html-report');
    if (exportHtmlBtn) {
      exportHtmlBtn.addEventListener('click', () => {
        this.exportHTMLReport();
      });
    }
  },

  async exportComparisonCSV() {
    if (ModelArena.leaderboardResults.length === 0) {
      App.showNotification('No comparison results to export. Run Model Arena first.', 'warning');
      return;
    }

    try {
      const res = await fetch('/api/export/comparison', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          leaderboard: ModelArena.leaderboardResults
        })
      });
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `model_comparison_${DatasetManager.activeDataset || 'results'}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      App.showNotification('Comparison CSV downloaded!', 'success');
    } catch (err) {
      App.showNotification('Export failed: ' + err.message, 'danger');
    }
  },

  async exportHTMLReport() {
    if (!ModelArena.selectedWinnerId) {
      App.showNotification('Train models first to generate an experiment report.', 'warning');
      return;
    }

    App.showLoading(true, 'Compiling comprehensive experiment report...');

    try {
      const res = await fetch('/api/export/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: DatasetManager.activeDataset,
          task: DatasetManager.activeTask,
          target: document.getElementById('select-target-column').value,
          features: DatasetManager.getSelectedFeatures(),
          winner_id: ModelArena.selectedWinnerId,
          leaderboard: ModelArena.leaderboardResults
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        window.open(data.report_url, '_blank');
        App.showNotification('Report generated and opened!', 'success');
      } else {
        App.showNotification(data.error || 'Report generation error', 'danger');
      }
    } catch (err) {
      App.showNotification('Export failed: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  }
};
