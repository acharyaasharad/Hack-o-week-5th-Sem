/**
 * model_arena.js - Controls model selection, arena training, leaderboard, and test evaluations
 */

const ModelArena = {
  availableModels: [],
  leaderboardResults: [],
  selectedWinnerId: null,

  init() {
    this.bindEvents();
    this.fetchAvailableModels();
  },

  bindEvents() {
    const runBtn = document.getElementById('btn-run-arena');
    if (runBtn) {
      runBtn.addEventListener('click', () => {
        this.runArenaComparison();
      });
    }

    const testEvalBtn = document.getElementById('btn-eval-heldout-test');
    if (testEvalBtn) {
      testEvalBtn.addEventListener('click', () => {
        this.runHeldoutTestEvaluation();
      });
    }
  },

  async fetchAvailableModels() {
    const task = DatasetManager.activeTask || 'classification';
    try {
      const res = await fetch(`/api/models?task=${task}`);
      const data = await res.json();
      if (data.status === 'success') {
        this.availableModels = data.models;
        this.renderModelCheckboxes(data.models);
        this.populateModelSelectors(data.models);
      }
    } catch (err) {
      console.error('Failed to fetch models', err);
    }
  },

  renderModelCheckboxes(models) {
    const box = document.getElementById('arena-models-list');
    if (!box) return;
    box.innerHTML = '';

    models.forEach(m => {
      const label = document.createElement('label');
      label.className = 'chip';
      const isDisabled = !m.is_available;
      const checkedAttr = (m.is_available && !m.model_id.includes('dummy')) ? 'checked' : '';

      label.innerHTML = `
        <input type="checkbox" value="${m.model_id}" ${checkedAttr} ${isDisabled ? 'disabled' : ''}>
        <span>${m.display_name} ${isDisabled ? '<small style="color:#ef4444">(Not installed)</small>' : ''}</span>
      `;
      box.appendChild(label);
    });
  },

  populateModelSelectors(models) {
    const selectors = ['select-gen-model', 'select-reg-model', 'select-pred-model'];
    selectors.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        el.innerHTML = '';
        models.filter(m => m.is_available).forEach(m => {
          const opt = document.createElement('option');
          opt.value = m.model_id;
          opt.textContent = m.display_name;
          el.appendChild(opt);
        });
      }
    });
  },

  async runArenaComparison() {
    if (!DatasetManager.activeDataset) {
      App.showNotification('Please load a dataset first!', 'warning');
      return;
    }

    const selectedFeatures = DatasetManager.getSelectedFeatures();
    if (selectedFeatures.length === 0) {
      App.showNotification('Please select at least one feature column.', 'warning');
      return;
    }

    const checkedInputs = document.querySelectorAll('#arena-models-list input[type="checkbox"]:checked');
    const modelIds = Array.from(checkedInputs).map(i => i.value);
    if (modelIds.length === 0) {
      App.showNotification('Please select at least one model to train.', 'warning');
      return;
    }

    const target = document.getElementById('select-target-column').value;
    const task = DatasetManager.activeTask;

    App.showLoading(true, `Training ${modelIds.length} candidate models... This fits models on training data only.`);

    try {
      const res = await fetch('/api/models/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          task: task,
          target: target,
          features: selectedFeatures,
          models: modelIds
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        this.leaderboardResults = data.leaderboard;
        this.selectedWinnerId = data.winner_id;
        this.renderLeaderboardTable(data.leaderboard, data.winner_id);
        Charts.renderLeaderboard('chart-arena-leaderboard', data.leaderboard);
        App.updateTrainedCount(data.leaderboard.length);
        App.showNotification(`Training complete! Best validation model: ${data.winner_name}`, 'success');
      } else {
        App.showNotification(data.error || 'Arena training failed', 'danger');
      }
    } catch (err) {
      App.showNotification('Training error: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  },

  renderLeaderboardTable(leaderboard, winnerId) {
    const tbody = document.getElementById('arena-leaderboard-body');
    if (!tbody) return;
    tbody.innerHTML = '';

    leaderboard.forEach((row, idx) => {
      const tr = document.createElement('tr');
      const isWinner = row.model_id === winnerId;
      if (isWinner) tr.style.background = '#f0fdf4';

      const metrics = row.metrics || {};
      const gap = metrics.generalization_gap !== null ? Number(metrics.generalization_gap).toFixed(4) : '-';
      const valScore = metrics.val_score !== null ? Number(metrics.val_score).toFixed(4) : '-';
      const trainScore = metrics.train_score !== null ? Number(metrics.train_score).toFixed(4) : '-';
      const testScore = row.test_score !== null ? Number(row.test_score).toFixed(4) : '<span style="color:#94a3b8">Pending Held-out Test</span>';

      tr.innerHTML = `
        <td><strong>#${idx + 1}</strong></td>
        <td>
          <strong>${row.display_name}</strong>
          ${isWinner ? '<span class="badge" style="background:#10b981; color:#fff; margin-left:6px">Validation Winner</span>' : ''}
          <div style="font-size:11px; color:#64748b">${row.family}</div>
        </td>
        <td><strong style="color:#0284c7">${valScore}</strong></td>
        <td>${trainScore}</td>
        <td>${gap}</td>
        <td>${testScore}</td>
        <td>${row.fit_time ? row.fit_time.toFixed(3) + 's' : '-'}</td>
      `;
      tbody.appendChild(tr);
    });
  },

  async runHeldoutTestEvaluation() {
    if (!this.selectedWinnerId) {
      App.showNotification('Train the arena models first to select a validation winner.', 'warning');
      return;
    }

    App.showLoading(true, `Running strictly final held-out test evaluation on winner...`);

    try {
      const res = await fetch('/api/models/final-evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: this.selectedWinnerId })
      });
      const data = await res.json();
      if (data.status === 'success') {
        App.showNotification(`Held-out test score evaluated: ${data.test_score.toFixed(4)}`, 'success');
        // Update table row
        const row = this.leaderboardResults.find(r => r.model_id === this.selectedWinnerId);
        if (row) row.test_score = data.test_score;
        this.renderLeaderboardTable(this.leaderboardResults, this.selectedWinnerId);

        // Render inspector charts if applicable
        if (data.metrics && data.metrics.confusion_matrix) {
          Charts.renderConfusionMatrix('chart-inspector-confusion', data.metrics.confusion_matrix);
        }
      } else {
        App.showNotification(data.error || 'Evaluation error', 'danger');
      }
    } catch (err) {
      App.showNotification('Evaluation request failed: ' + err.message, 'danger');
    } finally {
      App.showLoading(false);
    }
  }
};
