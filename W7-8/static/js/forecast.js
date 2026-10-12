/**
 * Energy Intelligence — Machine Learning & Forecasting Controller
 * Manages model training, leaderboard comparison, and 24-hour recursive predictions.
 */

const ForecastController = {
  async trainModels() {
    const btn = document.getElementById('trainModelsBtn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="status-dot"></span> Training Models...';
    }

    App.showToast('Executing chronological model training across splits...');

    try {
      const selectedModelKeys = [];
      document.querySelectorAll('.model-checkbox:checked').forEach(cb => {
        selectedModelKeys.push(cb.value);
      });

      const res = await fetch('/api/forecast/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_column: AppState.activeTarget,
          model_keys: selectedModelKeys.length > 0 ? selectedModelKeys : null,
          include_weather: true
        })
      });

      const data = await res.json();
      if (!data.success) {
        App.showToast(data.error || 'Training failed', true);
        return;
      }

      AppState.modelResults = data;
      App.showToast(`Training complete! Best model selected: ${data.best_model_name}`);

      this.updateArenaUI(data);
      this.updateDiagnosticsUI(data);

      // Auto-generate forward forecast with best model
      await this.generateForecast(data.best_model);

    } catch (err) {
      console.error('Error during model training:', err);
      App.showToast('Training process failed', true);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="play"></i> Train & Evaluate Models';
        lucide.createIcons();
      }
    }
  },

  async generateForecast(modelKey = null) {
    const btn = document.getElementById('generateForecastBtn');
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Generating 24h Forecast...';
    }

    try {
      const target = AppState.activeTarget;
      const res = await fetch('/api/forecast/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_column: target,
          model_key: modelKey || AppState.modelResults?.best_model || 'seasonal_naive',
          horizon: 24,
          use_weather_forecast: true
        })
      });

      const data = await res.json();
      if (!data.success) {
        App.showToast(data.error || 'Prediction failed', true);
        return;
      }

      AppState.forecastResults = data;
      this.updateForecastUI(data);

    } catch (err) {
      console.error('Error generating forecast:', err);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Generate 24h Forecast';
      }
    }
  },

  updateArenaUI(data) {
    const tbody = document.getElementById('arenaTableBody');
    if (!tbody || !data.arena_results) return;

    tbody.innerHTML = '';
    const models = Object.values(data.arena_results);

    // Sort by validation MAE ascending
    models.sort((a, b) => a.val_metrics.mae - b.val_metrics.mae);

    models.forEach((m, idx) => {
      const isBest = (m.model_key === data.best_model);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${idx + 1}</strong></td>
        <td>
          <strong>${m.display_name}</strong>
          ${isBest ? '<span class="badge badge-teal" style="margin-left:8px;">Champion</span>' : ''}
        </td>
        <td>${m.train_duration_sec}s</td>
        <td><strong>${m.val_metrics.mae} kW</strong></td>
        <td>${m.val_metrics.rmse} kW</td>
        <td>${m.val_metrics.wape}%</td>
        <td>${m.val_metrics.r2}</td>
        <td>${isBest ? `<span class="badge badge-emerald">${data.test_metrics.mae} kW</span>` : '—'}</td>
      `;
      tbody.appendChild(tr);
    });

    // Render Arena Comparison Bar Chart
    ChartEngine.renderArenaComparison('chartModelArenaBar', data.arena_results);
  },

  updateDiagnosticsUI(data) {
    // Test KPI cards
    const tm = data.test_metrics || {};
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val !== undefined ? val : '—';
    };

    setVal('kpiTestMae', `${tm.mae || '—'} kW`);
    setVal('kpiTestRmse', `${tm.rmse || '—'} kW`);
    setVal('kpiTestWape', `${tm.wape || '—'}%`);
    setVal('kpiTestR2', tm.r2 || '—');

    // Overview last evaluation MAE
    setVal('overviewLastMae', `${tm.mae || '—'} kW`);

    // Render Diagnostics charts
    const bestModel = data.arena_results[data.best_model];
    if (bestModel) {
      ChartEngine.renderActualVsPredicted(
        'chartActualVsPredicted',
        bestModel.val_actuals,
        bestModel.val_predictions
      );
    }

    if (data.residuals_diagnostic) {
      ChartEngine.renderResidualHistogram(
        'chartResidualDist',
        data.residuals_diagnostic.histogram
      );
    }
  },

  updateForecastUI(data) {
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val !== undefined ? val : '—';
    };

    setVal('overviewNextHour', `${data.forecast_series[0]?.predicted_demand || '—'} kW`);
    setVal('overviewExpectedPeak', `${data.peak_demand || '—'} kW`);

    // Forecast Lab KPI cards
    setVal('forecastPeakVal', `${data.peak_demand} kW`);
    setVal('forecastPeakTime', data.peak_hour);
    setVal('forecastMeanVal', `${data.mean_demand} kW`);
    setVal('forecastMinVal', `${data.min_demand} kW`);

    // Render Detailed Forecast Chart
    ChartEngine.renderForecastCurve('chartForecastCurve', data.forecast_series, data.units);

    // Render Overview Chart
    ChartEngine.renderOverviewTimeline(
      'chartOverviewTimeline',
      data.recent_historical_series,
      data.forecast_series,
      data.units
    );
  },

  initEventListeners() {
    const trainBtn = document.getElementById('trainModelsBtn');
    if (trainBtn) {
      trainBtn.addEventListener('click', () => this.trainModels());
    }

    const forecastBtn = document.getElementById('generateForecastBtn');
    if (forecastBtn) {
      forecastBtn.addEventListener('click', () => this.generateForecast());
    }

    const horizonSelect = document.getElementById('forecastHorizonSelect');
    if (horizonSelect) {
      horizonSelect.addEventListener('change', (e) => {
        this.generateForecast();
      });
    }
  }
};
