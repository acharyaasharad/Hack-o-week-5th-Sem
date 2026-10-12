/**
 * prediction.js - Handles interactive single-row prediction forms and live inference
 */

const PredictionPlayground = {
  activeModelId: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    const buildFormBtn = document.getElementById('btn-build-pred-form');
    if (buildFormBtn) {
      buildFormBtn.addEventListener('click', () => {
        this.buildInputForm();
      });
    }

    const predictBtn = document.getElementById('btn-run-prediction');
    if (predictBtn) {
      predictBtn.addEventListener('click', () => {
        this.runPrediction();
      });
    }
  },

  buildInputForm() {
    this.activeModelId = document.getElementById('select-pred-model').value;
    const features = DatasetManager.getSelectedFeatures();
    const container = document.getElementById('pred-form-inputs');
    if (!container) return;
    container.innerHTML = '';

    if (features.length === 0) {
      container.innerHTML = '<div class="alert alert-warning">No features selected in Dataset Explorer.</div>';
      return;
    }

    features.forEach(f => {
      const colMeta = DatasetManager.columns.find(c => c.name === f) || { type: 'numeric' };
      const div = document.createElement('div');
      div.className = 'form-group';

      if (colMeta.type === 'categorical' && colMeta.unique_values) {
        div.innerHTML = `
          <label class="form-label">${f}</label>
          <select class="form-control select-control" data-feature="${f}">
            ${colMeta.unique_values.map(val => `<option value="${val}">${val}</option>`).join('')}
          </select>
        `;
      } else {
        div.innerHTML = `
          <label class="form-label">${f}</label>
          <input type="number" step="any" class="form-control" data-feature="${f}" placeholder="Enter numeric value">
        `;
      }
      container.appendChild(div);
    });

    document.getElementById('pred-controls-box').style.display = 'block';
  },

  async runPrediction() {
    if (!this.activeModelId) {
      App.showNotification('Please build the form first.', 'warning');
      return;
    }

    const inputs = document.querySelectorAll('#pred-form-inputs [data-feature]');
    const featurePayload = {};

    inputs.forEach(el => {
      const feat = el.getAttribute('data-feature');
      const val = el.value;
      featurePayload[feat] = isNaN(Number(val)) || val === '' ? val : Number(val);
    });

    App.showLoading(true, 'Computing model prediction via fitted pipeline...');

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_id: this.activeModelId,
          features: featurePayload
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.renderPredictionResult(data);
        App.showNotification('Prediction computed!', 'success');
      } else {
        App.showNotification(data.error || 'Prediction error', 'danger');
      }
    } catch (err) {
      App.showNotification('Prediction request failed: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  renderPredictionResult(res) {
    const box = document.getElementById('pred-result-display');
    if (!box) return;
    box.style.display = 'block';

    let probHtml = '';
    if (res.probabilities) {
      probHtml = '<div style="margin-top:10px;"><strong>Class Probabilities:</strong><ul style="margin-left:20px;">';
      for (const [cls, p] of Object.entries(res.probabilities)) {
        probHtml += `<li>Class ${cls}: ${(p * 100).toFixed(1)}%</li>`;
      }
      probHtml += '</ul></div>';
    }

    box.innerHTML = `
      <div class="alert alert-success">
        <h3>Model Prediction: <strong>${res.prediction}</strong></h3>
        ${probHtml}
        <small style="color:#64748b; display:block; margin-top:6px;">Model used: ${res.model_id} (Fitted pipeline with training imputation & encoding)</small>
      </div>
    `;
  }
};
