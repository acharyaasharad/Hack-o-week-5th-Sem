/**
 * generalization.js - Bias-Variance Lab, Complexity Sweeps, and Synthetic Polynomial Demo
 */

const GeneralizationLab = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const runSweepBtn = document.getElementById('btn-run-complexity-sweep');
    if (runSweepBtn) {
      runSweepBtn.addEventListener('click', () => {
        this.runComplexitySweep();
      });
    }

    const runDemoBtn = document.getElementById('btn-run-synthetic-demo');
    if (runDemoBtn) {
      runDemoBtn.addEventListener('click', () => {
        this.runSyntheticDemo();
      });
    }
  },

  async runComplexitySweep() {
    if (!DatasetManager.activeDataset) {
      App.showNotification('Please load a dataset first!', 'warning');
      return;
    }

    const modelId = document.getElementById('select-gen-model').value;
    const paramName = document.getElementById('select-gen-param').value;
    const valuesStr = document.getElementById('input-gen-param-values').value;
    const target = document.getElementById('select-target-column').value;
    const features = DatasetManager.getSelectedFeatures();

    let values;
    try {
      values = valuesStr.split(',').map(s => {
        const trimmed = s.trim();
        return isNaN(Number(trimmed)) ? trimmed : Number(trimmed);
      });
    } catch (e) {
      App.showNotification('Invalid comma-separated parameter values.', 'warning');
      return;
    }

    App.showLoading(true, `Running complexity sweep for ${modelId} across ${paramName}...`);

    try {
      const res = await fetch('/api/generalization/complexity-sweep', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: modelId,
          param_name: paramName,
          param_values: values,
          task: DatasetManager.activeTask,
          target: target,
          features: features
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        Charts.renderComplexityCurve('chart-complexity-curve', data.results, data.param_name, data.metric_name);
        this.renderDiagnostics(data.diagnostic);
        App.showNotification('Complexity sweep complete!', 'success');
      } else {
        App.showNotification(data.error || 'Sweep failed', 'danger');
      }
    } catch (err) {
      App.showNotification('Error during complexity sweep: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  renderDiagnostics(diag) {
    const box = document.getElementById('gen-diagnostic-box');
    if (!box) return;

    if (!diag) {
      box.style.display = 'none';
      return;
    }

    box.style.display = 'block';
    box.className = `alert alert-${diag.status === 'likely_overfitting' ? 'warning' : diag.status === 'likely_underfitting' ? 'danger' : 'success'}`;
    box.innerHTML = `
      <h4>Diagnostic: <strong>${diag.status.replace('_', ' ').toUpperCase()}</strong></h4>
      <p style="margin-top: 6px;">${diag.message}</p>
      <small style="color:#64748b; display:block; margin-top:4px;">${diag.disclaimer}</small>
    `;
  },

  async runSyntheticDemo() {
    App.showLoading(true, 'Fitting synthetic polynomial models (Degrees 1, 4, 12)...');
    try {
      const res = await fetch('/api/generalization/synthetic-demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n_samples: 80, noise: 0.25 })
      });
      const data = await res.json();
      if (data.status === 'success') {
        Charts.renderSyntheticDemo('chart-synthetic-demo', data.demo_data);
        const m = data.demo_data.metrics;
        document.getElementById('synthetic-metrics-summary').innerHTML = `
          <div class="grid-3" style="margin-top:14px;">
            <div class="kpi-card">
              <span class="kpi-label">Degree 1 (Linear / Underfit)</span>
              <span class="kpi-value" style="color:#ef4444">${m.degree_1.val_rmse}</span>
              <span class="kpi-sub">Validation RMSE (High Bias)</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Degree 4 (Optimal Balanced)</span>
              <span class="kpi-value" style="color:#10b981">${m.degree_4.val_rmse}</span>
              <span class="kpi-sub">Validation RMSE (Low Generalization Error)</span>
            </div>
            <div class="kpi-card">
              <span class="kpi-label">Degree 12 (Complex / Overfit)</span>
              <span class="kpi-value" style="color:#f59e0b">${m.degree_12.val_rmse}</span>
              <span class="kpi-sub">Validation RMSE (High Variance on unseen data)</span>
            </div>
          </div>
        `;
        App.showNotification('Synthetic demonstration rendered!', 'success');
      } else {
        App.showNotification(data.error || 'Failed demo', 'danger');
      }
    } catch (err) {
      App.showNotification('Demo error: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  }
};
