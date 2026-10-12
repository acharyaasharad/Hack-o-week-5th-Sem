/**
 * regularization.js - Regularization Lab and L1/L2 strength sweeps
 */

const RegularizationLab = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    const runRegBtn = document.getElementById('btn-run-reg-sweep');
    if (runRegBtn) {
      runRegBtn.addEventListener('click', () => {
        this.runRegularizationSweep();
      });
    }

    const modelSelect = document.getElementById('select-reg-model');
    if (modelSelect) {
      modelSelect.addEventListener('change', (e) => {
        this.updateParamFields(e.target.value);
      });
    }
  },

  updateParamFields(modelId) {
    const paramSelect = document.getElementById('select-reg-param');
    paramSelect.innerHTML = '';

    if (modelId.includes('logistic') || modelId.includes('ridge') || modelId.includes('lasso')) {
      const opt = document.createElement('option');
      opt.value = modelId.includes('logistic') ? 'C' : 'alpha';
      opt.textContent = modelId.includes('logistic') ? 'C (Inverse penalty)' : 'alpha (Penalty strength)';
      paramSelect.appendChild(opt);
    } else if (modelId.includes('xgb') || modelId.includes('lgbm')) {
      const opt1 = document.createElement('option');
      opt1.value = 'reg_alpha';
      opt1.textContent = 'reg_alpha (L1 Regularization)';
      const opt2 = document.createElement('option');
      opt2.value = 'reg_lambda';
      opt2.textContent = 'reg_lambda (L2 Regularization)';
      paramSelect.appendChild(opt1);
      paramSelect.appendChild(opt2);
    } else {
      const opt = document.createElement('option');
      opt.value = 'ccp_alpha';
      opt.textContent = 'ccp_alpha (Cost-complexity pruning)';
      paramSelect.appendChild(opt);
    }
  },

  async runRegularizationSweep() {
    if (!DatasetManager.activeDataset) {
      App.showNotification('Please load a dataset first!', 'warning');
      return;
    }

    const modelId = document.getElementById('select-reg-model').value;
    const paramName = document.getElementById('select-reg-param').value;
    const valuesStr = document.getElementById('input-reg-param-values').value;
    const target = document.getElementById('select-target-column').value;
    const features = DatasetManager.getSelectedFeatures();

    let values;
    try {
      values = valuesStr.split(',').map(s => Number(s.trim()));
    } catch (e) {
      App.showNotification('Invalid comma-separated values', 'warning');
      return;
    }

    App.showLoading(true, `Running regularization strength sweep for ${modelId}...`);

    try {
      const res = await fetch('/api/regularization/sweep', {
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
        Charts.renderRegularizationSweep('chart-regularization-sweep', data.results, data.param_name, data.metric_name);
        this.renderExplanation(data.explanation);
        App.showNotification('Regularization sweep complete!', 'success');
      } else {
        App.showNotification(data.error || 'Regularization sweep failed', 'danger');
      }
    } catch (err) {
      App.showNotification('Sweep error: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  renderExplanation(expl) {
    const box = document.getElementById('reg-explanation-box');
    if (!box) return;
    if (!expl) {
      box.style.display = 'none';
      return;
    }
    box.style.display = 'block';
    box.innerHTML = `
      <div class="alert alert-info">
        <h4>Observed Regularization Behavior</h4>
        <p style="margin-top:4px;">${expl}</p>
      </div>
    `;
  }
};
