/**
 * Energy Intelligence — Load Shifting & Optimization Controller
 * Coordinates SciPy linear programming solver, Time-Of-Use tariff adjustments,
 * and before/after peak & cost reduction benchmarks.
 */

const OptimizationController = {
  currentTariffs: [
    0.08, 0.08, 0.08, 0.08, 0.08, 0.08, 0.08,
    0.14, 0.14, 0.14, 0.14, 0.14, 0.14, 0.14,
    0.14, 0.14, 0.14,
    0.28, 0.28, 0.28, 0.28, 0.28,
    0.14, 0.14
  ],

  async runOptimization() {
    const btn = document.getElementById('runOptimizerBtn');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = '<span class="status-dot"></span> Solving Linear Program...';
    }

    try {
      const requiredEnergy = parseFloat(document.getElementById('optRequiredEnergy').value) || 60.0;
      const maxPower = parseFloat(document.getElementById('optMaxPower').value) || 12.0;
      const startHour = parseInt(document.getElementById('optStartHour').value, 10) || 0;
      const endHour = parseInt(document.getElementById('optEndHour').value, 10) || 23;
      const peakPenalty = parseFloat(document.getElementById('optPeakPenalty').value) || 0.5;

      const objectiveRadios = document.getElementsByName('optObjective');
      let objective = 'balanced';
      for (const r of objectiveRadios) {
        if (r.checked) objective = r.value;
      }

      // Collect unavailable hours
      const unavail = [];
      document.querySelectorAll('.unavail-hour-checkbox:checked').forEach(cb => {
        unavail.push(parseInt(cb.value, 10));
      });

      // Pull base demand from current forecast or defaults
      let baseDemand = null;
      if (AppState.forecastResults && AppState.forecastResults.forecast_series) {
        baseDemand = AppState.forecastResults.forecast_series.map(pt => pt.predicted_demand);
      }

      App.showToast('Solving constrained load optimization via SciPy linprog...');

      const res = await fetch('/api/optimization/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_demand: baseDemand,
          required_energy: requiredEnergy,
          max_power: maxPower,
          start_hour: startHour,
          end_hour: endHour,
          unavailable_hours: unavail,
          tariffs: this.currentTariffs,
          objective: objective,
          peak_penalty_weight: peakPenalty
        })
      });

      const data = await res.json();
      if (!data.success) {
        App.showToast(data.error || 'Optimization infeasible or failed', true);
        const errBox = document.getElementById('optErrorMsg');
        if (errBox) {
          errBox.textContent = data.error;
          errBox.style.display = 'block';
        }
        return;
      }

      const errBox = document.getElementById('optErrorMsg');
      if (errBox) errBox.style.display = 'none';

      AppState.optimizationResults = data;
      App.showToast(`Optimal solution found! Peak reduced by ${data.summary.peak_reduction_pct}%`);

      this.updateOptimizationUI(data);

    } catch (err) {
      console.error('Error during optimization:', err);
      App.showToast('Solver execution failed', true);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = '<i data-lucide="zap"></i> Run Constrained Optimization';
        lucide.createIcons();
      }
    }
  },

  updateOptimizationUI(data) {
    const sm = data.summary;
    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val !== undefined ? val : '—';
    };

    // Optimization Lab KPI cards
    setVal('kpiPeakReduction', `${sm.peak_reduction_pct}%`);
    setVal('kpiPeakValues', `${sm.baseline_peak} kW → ${sm.optimized_peak} kW`);
    setVal('kpiCostSavings', `${sm.cost_savings_pct}%`);
    setVal('kpiCostValues', `$${sm.baseline_cost} → $${sm.optimized_cost}`);
    setVal('kpiEnergyDelivered', `${sm.scheduled_energy} kWh`);
    setVal('kpiEnergyConserved', sm.energy_conserved ? '100% Conserved' : 'Mismatch');

    // Overview Optimization KPI
    setVal('overviewOptSavings', `${sm.cost_savings_pct}%`);

    // Render Charts
    ChartEngine.renderOptimizationSchedule('chartOptCombinedSchedule', data.hourly_schedule);
    ChartEngine.renderFlexibleEnergyBars('chartOptFlexibleBars', data.hourly_schedule);
    ChartEngine.renderTariffCurve('chartOptTariffCurve', data.hourly_schedule);

    // Scenario Comparison Charts
    ChartEngine.renderOptimizationSchedule('chartScenarioCompare', data.hourly_schedule);

    // Populate Detailed Hourly Schedule Table
    this.renderHourlyScheduleTable(data.hourly_schedule);
  },

  renderHourlyScheduleTable(schedule) {
    const tbody = document.getElementById('optScheduleTableBody');
    if (!tbody || !schedule) return;

    tbody.innerHTML = '';
    schedule.forEach(row => {
      const tr = document.createElement('tr');
      const isShifted = row.balanced_flex > 0;
      tr.innerHTML = `
        <td><strong>${row.hour_label}</strong></td>
        <td>$${row.tariff.toFixed(2)}/kWh</td>
        <td>${row.base_demand} kW</td>
        <td>${row.baseline_flex} kWh</td>
        <td style="${isShifted ? 'color:#059669;font-weight:700;' : ''}">${row.balanced_flex} kWh</td>
        <td>${row.baseline_combined} kW</td>
        <td><strong>${row.balanced_combined} kW</strong></td>
        <td>
          ${row.is_unavailable ? '<span class="badge badge-rose">Forbidden</span>' :
            (row.is_within_window ? '<span class="badge badge-emerald">Eligible</span>' : '<span class="badge badge-amber">Outside Window</span>')}
        </td>
      `;
      tbody.appendChild(tr);
    });
  },

  initEventListeners() {
    const runBtn = document.getElementById('runOptimizerBtn');
    if (runBtn) {
      runBtn.addEventListener('click', () => this.runOptimization());
    }

    // Sliders dynamic display
    const sliders = [
      { id: 'optRequiredEnergy', disp: 'optReqEnergyVal', suffix: ' kWh' },
      { id: 'optMaxPower', disp: 'optMaxPowerVal', suffix: ' kW' },
      { id: 'optPeakPenalty', disp: 'optPeakPenaltyVal', suffix: '' }
    ];

    sliders.forEach(s => {
      const el = document.getElementById(s.id);
      const disp = document.getElementById(s.disp);
      if (el && disp) {
        el.addEventListener('input', (e) => {
          disp.textContent = e.target.value + s.suffix;
        });
      }
    });
  }
};
