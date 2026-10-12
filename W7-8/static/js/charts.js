/**
 * Energy Intelligence — Plotly.js Chart Renderers
 * Pure Plotly configurations with light workspace styling and teal/emerald accents.
 * Strictly NO PURPLE GRADIENTS.
 */

const ChartEngine = {
  // Common Plotly Layout Defaults
  baseLayout: {
    font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color: '#334155', size: 12 },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    margin: { l: 55, r: 25, t: 35, b: 45 },
    xaxis: {
      gridcolor: '#f1f5f9',
      zerolinecolor: '#e2e8f0',
      linecolor: '#cbd5e1',
      tickfont: { color: '#64748b' }
    },
    yaxis: {
      gridcolor: '#f1f5f9',
      zerolinecolor: '#e2e8f0',
      linecolor: '#cbd5e1',
      tickfont: { color: '#64748b' }
    },
    legend: { orientation: 'h', y: 1.12, x: 0.05, font: { color: '#0f172a', size: 11 } }
  },

  config: { responsive: true, displayModeBar: false },

  // 1. Overview Historical vs Forecast
  renderOverviewTimeline(containerId, histSeries, forecastSeries, units = 'kW') {
    const el = document.getElementById(containerId);
    if (!el) return;

    const traces = [];

    if (histSeries && histSeries.length > 0) {
      traces.push({
        x: histSeries.map(d => d.timestamp),
        y: histSeries.map(d => d.actual_demand),
        mode: 'lines',
        name: 'Historical Actual',
        line: { color: '#0f172a', width: 2 }
      });
    }

    if (forecastSeries && forecastSeries.length > 0) {
      traces.push({
        x: forecastSeries.map(d => d.timestamp),
        y: forecastSeries.map(d => d.predicted_demand),
        mode: 'lines+markers',
        name: '24h Forecast Prediction',
        line: { color: '#0d9488', width: 2.5, dash: 'solid' },
        marker: { size: 5, color: '#0d9488' }
      });

      // Upper bound
      traces.push({
        x: forecastSeries.map(d => d.timestamp),
        y: forecastSeries.map(d => d.upper_bound),
        mode: 'lines',
        name: '95% Upper Bound',
        line: { color: 'rgba(13, 148, 136, 0.25)', width: 1 },
        showlegend: false
      });

      // Lower bound
      traces.push({
        x: forecastSeries.map(d => d.timestamp),
        y: forecastSeries.map(d => d.lower_bound),
        mode: 'lines',
        name: '95% Confidence Envelope',
        fill: 'tonexty',
        fillcolor: 'rgba(13, 148, 136, 0.12)',
        line: { color: 'rgba(13, 148, 136, 0.25)', width: 1 }
      });
    }

    const layout = {
      ...this.baseLayout,
      yaxis: { ...this.baseLayout.yaxis, title: `Demand (${units})` }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 2. Forecast Lab Detailed Curve
  renderForecastCurve(containerId, forecastSeries, units = 'kW') {
    const el = document.getElementById(containerId);
    if (!el || !forecastSeries || forecastSeries.length === 0) return;

    const x = forecastSeries.map(d => d.timestamp);
    const yPred = forecastSeries.map(d => d.predicted_demand);
    const yUpper = forecastSeries.map(d => d.upper_bound);
    const yLower = forecastSeries.map(d => d.lower_bound);

    const traces = [
      {
        x, y: yPred,
        mode: 'lines+markers',
        name: 'Forecast Model',
        line: { color: '#0d9488', width: 3 },
        marker: { size: 6, color: '#0f766e' }
      },
      {
        x, y: yUpper,
        mode: 'lines',
        name: 'Upper Bound',
        line: { color: 'transparent' },
        showlegend: false
      },
      {
        x, y: yLower,
        mode: 'lines',
        name: '95% Interval',
        fill: 'tonexty',
        fillcolor: 'rgba(13, 148, 136, 0.15)',
        line: { color: 'transparent' }
      }
    ];

    const layout = {
      ...this.baseLayout,
      yaxis: { ...this.baseLayout.yaxis, title: `Forecast Demand (${units})` }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 3. Hourly Profile (Weekday vs Weekend)
  renderHourlyProfile(containerId, profileData, units = 'kW') {
    const el = document.getElementById(containerId);
    if (!el || !profileData || profileData.length === 0) return;

    const hours = profileData.map(d => d.hour_label);
    const traces = [
      {
        x: hours,
        y: profileData.map(d => d.weekday_avg),
        mode: 'lines+markers',
        name: 'Weekday Average',
        line: { color: '#0284c7', width: 2.5 },
        marker: { size: 5 }
      },
      {
        x: hours,
        y: profileData.map(d => d.weekend_avg),
        mode: 'lines+markers',
        name: 'Weekend Average',
        line: { color: '#d97706', width: 2.5 },
        marker: { size: 5 }
      },
      {
        x: hours,
        y: profileData.map(d => d.overall_avg),
        mode: 'lines',
        name: 'Overall Average',
        line: { color: '#64748b', width: 1.5, dash: 'dot' }
      }
    ];

    const layout = {
      ...this.baseLayout,
      yaxis: { ...this.baseLayout.yaxis, title: `Average Demand (${units})` }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 4. 24x7 Demand Heatmap
  renderHeatmap(containerId, heatmapData) {
    const el = document.getElementById(containerId);
    if (!el || !heatmapData || !heatmapData.matrix) return;

    const z = heatmapData.matrix.map(row => row.hourly_demand);
    const y = heatmapData.matrix.map(row => row.day);
    const x = heatmapData.hours;

    const trace = {
      z: z,
      x: x,
      y: y,
      type: 'heatmap',
      colorscale: [
        [0.0, '#f0fdf4'],
        [0.2, '#bbf7d0'],
        [0.5, '#34d399'],
        [0.8, '#0d9488'],
        [1.0, '#064e3b']
      ],
      colorbar: { title: 'Demand', titleside: 'right', thickness: 12, len: 0.9 }
    };

    const layout = {
      ...this.baseLayout,
      margin: { l: 85, r: 25, t: 25, b: 45 },
      xaxis: { ...this.baseLayout.xaxis, tickangle: -45 }
    };

    Plotly.newPlot(containerId, [trace], layout, this.config);
  },

  // 5. Scatter: Actual vs Predicted
  renderActualVsPredicted(containerId, actuals, predictions, units = 'kW') {
    const el = document.getElementById(containerId);
    if (!el || !actuals || !predictions) return;

    const minVal = Math.min(...actuals, ...predictions);
    const maxVal = Math.max(...actuals, ...predictions);

    const traces = [
      {
        x: actuals,
        y: predictions,
        mode: 'markers',
        name: 'Evaluation Points',
        marker: { color: '#0d9488', size: 6, opacity: 0.6 }
      },
      {
        x: [minVal, maxVal],
        y: [minVal, maxVal],
        mode: 'lines',
        name: 'Perfect Match (1:1)',
        line: { color: '#e11d48', width: 2, dash: 'dash' }
      }
    ];

    const layout = {
      ...this.baseLayout,
      xaxis: { ...this.baseLayout.xaxis, title: `Actual Demand (${units})` },
      yaxis: { ...this.baseLayout.yaxis, title: `Predicted Demand (${units})` }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 6. Residual Distribution Histogram
  renderResidualHistogram(containerId, histogramBins) {
    const el = document.getElementById(containerId);
    if (!el || !histogramBins || histogramBins.length === 0) return;

    const x = histogramBins.map(b => `${b.range_min} to ${b.range_max}`);
    const y = histogramBins.map(b => b.count);

    const trace = {
      x, y,
      type: 'bar',
      marker: { color: '#0d9488' }
    };

    const layout = {
      ...this.baseLayout,
      xaxis: { ...this.baseLayout.xaxis, tickangle: -45 },
      yaxis: { ...this.baseLayout.yaxis, title: 'Count' }
    };

    Plotly.newPlot(containerId, [trace], layout, this.config);
  },

  // 7. Model Arena Leaderboard Bar Chart
  renderArenaComparison(containerId, arenaResults) {
    const el = document.getElementById(containerId);
    if (!el || !arenaResults) return;

    const models = Object.values(arenaResults);
    const names = models.map(m => m.display_name);
    const mae = models.map(m => m.val_metrics.mae);
    const rmse = models.map(m => m.val_metrics.rmse);

    const traces = [
      {
        x: names,
        y: mae,
        name: 'Validation MAE',
        type: 'bar',
        marker: { color: '#0d9488' }
      },
      {
        x: names,
        y: rmse,
        name: 'Validation RMSE',
        type: 'bar',
        marker: { color: '#0284c7' }
      }
    ];

    const layout = {
      ...this.baseLayout,
      barmode: 'group',
      yaxis: { ...this.baseLayout.yaxis, title: 'Error Metric (kW)' }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 8. Load Optimization: Baseline vs Optimal Combined Demand
  renderOptimizationSchedule(containerId, hourlyData, units = 'kW') {
    const el = document.getElementById(containerId);
    if (!el || !hourlyData || hourlyData.length === 0) return;

    const hours = hourlyData.map(d => d.hour_label);
    const traces = [
      {
        x: hours,
        y: hourlyData.map(d => d.base_demand),
        mode: 'lines',
        name: 'Base Load',
        line: { color: '#94a3b8', width: 2, dash: 'dot' }
      },
      {
        x: hours,
        y: hourlyData.map(d => d.baseline_combined),
        mode: 'lines+markers',
        name: 'Baseline Schedule',
        line: { color: '#e11d48', width: 2 },
        marker: { size: 5 }
      },
      {
        x: hours,
        y: hourlyData.map(d => d.balanced_combined),
        mode: 'lines+markers',
        name: 'Optimized Schedule',
        line: { color: '#059669', width: 2.5 },
        marker: { size: 6 }
      }
    ];

    const layout = {
      ...this.baseLayout,
      yaxis: { ...this.baseLayout.yaxis, title: `Total Demand (${units})` }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 9. Scheduled Flexible Load Bar Chart
  renderFlexibleEnergyBars(containerId, hourlyData) {
    const el = document.getElementById(containerId);
    if (!el || !hourlyData || hourlyData.length === 0) return;

    const hours = hourlyData.map(d => d.hour_label);
    const traces = [
      {
        x: hours,
        y: hourlyData.map(d => d.baseline_flex),
        type: 'bar',
        name: 'Baseline Greedy Load',
        marker: { color: '#fca5a5' }
      },
      {
        x: hours,
        y: hourlyData.map(d => d.balanced_flex),
        type: 'bar',
        name: 'Optimized Shifted Load',
        marker: { color: '#10b981' }
      }
    ];

    const layout = {
      ...this.baseLayout,
      barmode: 'group',
      yaxis: { ...this.baseLayout.yaxis, title: 'Allocated Energy (kWh)' }
    };

    Plotly.newPlot(containerId, traces, layout, this.config);
  },

  // 10. Tariff Curve
  renderTariffCurve(containerId, hourlyData) {
    const el = document.getElementById(containerId);
    if (!el || !hourlyData || hourlyData.length === 0) return;

    const trace = {
      x: hourlyData.map(d => d.hour_label),
      y: hourlyData.map(d => d.tariff),
      type: 'bar',
      marker: {
        color: hourlyData.map(d => d.tariff > 0.20 ? '#e11d48' : (d.tariff > 0.10 ? '#d97706' : '#059669'))
      }
    };

    const layout = {
      ...this.baseLayout,
      yaxis: { ...this.baseLayout.yaxis, title: 'Tariff Rate ($/kWh)' }
    };

    Plotly.newPlot(containerId, [trace], layout, this.config);
  }
};
