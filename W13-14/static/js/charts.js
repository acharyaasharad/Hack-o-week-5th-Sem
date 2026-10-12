/**
 * charts.js - Plotly visualization helpers for Ensemble Lab
 */

const Charts = {
  theme: {
    font: { family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif', color: '#334155' },
    margin: { t: 40, r: 30, l: 50, b: 50 },
    paper_bgcolor: 'transparent',
    plot_bgcolor: '#f8fafc'
  },

  renderLeaderboard(containerId, models) {
    if (!models || models.length === 0) {
      document.getElementById(containerId).innerHTML = '<div class="alert alert-info">No trained models to plot.</div>';
      return;
    }

    const names = models.map(m => m.display_name || m.model_id);
    const valScores = models.map(m => m.metrics.val_score);
    const trainScores = models.map(m => m.metrics.train_score);

    const traceVal = {
      x: names,
      y: valScores,
      name: 'Validation Score',
      type: 'bar',
      marker: { color: '#06b6d4' }
    };

    const traceTrain = {
      x: names,
      y: trainScores,
      name: 'Training Score',
      type: 'bar',
      marker: { color: '#64748b' }
    };

    const layout = {
      ...this.theme,
      title: 'Model Arena: Train vs Validation Performance',
      barmode: 'group',
      yaxis: { title: 'Evaluation Score' }
    };

    Plotly.newPlot(containerId, [traceTrain, traceVal], layout, { responsive: true });
  },

  renderComplexityCurve(containerId, sweepResults, paramName, metricName) {
    if (!sweepResults || sweepResults.length === 0) return;

    const xVals = sweepResults.map(r => r.param_value);
    const trainVals = sweepResults.map(r => r.train_score);
    const valVals = sweepResults.map(r => r.val_score);

    const traceTrain = {
      x: xVals,
      y: trainVals,
      mode: 'lines+markers',
      name: 'Training ' + metricName,
      line: { color: '#3b82f6', width: 2.5 }
    };

    const traceVal = {
      x: xVals,
      y: valVals,
      mode: 'lines+markers',
      name: 'Validation ' + metricName,
      line: { color: '#10b981', width: 2.5 }
    };

    const layout = {
      ...this.theme,
      title: `Model Complexity: ${paramName} vs Performance`,
      xaxis: { title: paramName },
      yaxis: { title: metricName }
    };

    Plotly.newPlot(containerId, [traceTrain, traceVal], layout, { responsive: true });
  },

  renderSyntheticDemo(containerId, demoData) {
    if (!demoData) return;

    const traces = [
      {
        x: demoData.x_train,
        y: demoData.y_train,
        mode: 'markers',
        name: 'Training Data',
        marker: { color: '#0f172a', size: 6, opacity: 0.7 }
      },
      {
        x: demoData.curve_x,
        y: demoData.curves.degree_1,
        mode: 'lines',
        name: `Degree 1 (Underfitting, RMSE: ${demoData.metrics.degree_1.val_rmse})`,
        line: { color: '#ef4444', width: 2, dash: 'dot' }
      },
      {
        x: demoData.curve_x,
        y: demoData.curves.degree_4,
        mode: 'lines',
        name: `Degree 4 (Optimal, RMSE: ${demoData.metrics.degree_4.val_rmse})`,
        line: { color: '#10b981', width: 3 }
      },
      {
        x: demoData.curve_x,
        y: demoData.curves.degree_12,
        mode: 'lines',
        name: `Degree 12 (Overfitting, RMSE: ${demoData.metrics.degree_12.val_rmse})`,
        line: { color: '#f59e0b', width: 2, dash: 'dash' }
      }
    ];

    const layout = {
      ...this.theme,
      title: 'Synthetic Demonstration: Polynomial Bias–Variance Tradeoff',
      xaxis: { title: 'X' },
      yaxis: { title: 'y' }
    };

    Plotly.newPlot(containerId, traces, layout, { responsive: true });
  },

  renderRegularizationSweep(containerId, sweepResults, paramName, metricName) {
    if (!sweepResults || sweepResults.length === 0) return;

    const xVals = sweepResults.map(r => r.param_value);
    const trainScores = sweepResults.map(r => r.train_score);
    const valScores = sweepResults.map(r => r.val_score);

    const traceTrain = {
      x: xVals,
      y: trainScores,
      mode: 'lines+markers',
      name: 'Training Score',
      line: { color: '#6366f1', width: 2 }
    };

    const traceVal = {
      x: xVals,
      y: valScores,
      mode: 'lines+markers',
      name: 'Validation Score',
      line: { color: '#06b6d4', width: 3 }
    };

    const traces = [traceTrain, traceVal];

    // If zero coefficients are tracked
    if (sweepResults[0].zero_coef_count !== null && sweepResults[0].zero_coef_count !== undefined) {
      const zeroCount = sweepResults.map(r => r.zero_coef_count);
      traces.push({
        x: xVals,
        y: zeroCount,
        mode: 'lines+markers',
        name: 'Zero-valued Coefs (Sparsity)',
        yaxis: 'y2',
        line: { color: '#ec4899', width: 2, dash: 'dot' }
      });
    }

    const layout = {
      ...this.theme,
      title: `Regularization Sweep: ${paramName} Impact`,
      xaxis: { title: paramName, type: 'log' },
      yaxis: { title: metricName },
      yaxis2: traces.length > 2 ? {
        title: 'Zero Coefficients',
        overlaying: 'y',
        side: 'right'
      } : undefined
    };

    Plotly.newPlot(containerId, traces, layout, { responsive: true });
  },

  renderFeatureImportance(containerId, importances, title = 'Feature Importance') {
    if (!importances || importances.length === 0) {
      document.getElementById(containerId).innerHTML = '<div class="alert alert-info">Feature importances not available for this model.</div>';
      return;
    }

    // Top 15 features
    const top = importances.slice(0, 15).reverse();
    const names = top.map(item => item.feature);
    const vals = top.map(item => Math.abs(item.importance || item.coefficient || 0));

    const trace = {
      x: vals,
      y: names,
      type: 'bar',
      orientation: 'h',
      marker: { color: '#3b82f6' }
    };

    const layout = {
      ...this.theme,
      title: title,
      xaxis: { title: 'Relative Magnitude' },
      margin: { ...this.theme.margin, l: 140 }
    };

    Plotly.newPlot(containerId, [trace], layout, { responsive: true });
  },

  renderConfusionMatrix(containerId, matrixData) {
    if (!matrixData || !matrixData.matrix) return;

    const trace = {
      z: matrixData.matrix,
      x: matrixData.labels,
      y: matrixData.labels,
      type: 'heatmap',
      colorscale: 'Blues',
      showscale: true
    };

    const layout = {
      ...this.theme,
      title: 'Confusion Matrix (Held-out Test)',
      xaxis: { title: 'Predicted Class' },
      yaxis: { title: 'Actual Class' }
    };

    Plotly.newPlot(containerId, [trace], layout, { responsive: true });
  },

  renderActualVsPredicted(containerId, actual, predicted) {
    if (!actual || !predicted || actual.length === 0) return;

    const tracePoints = {
      x: actual,
      y: predicted,
      mode: 'markers',
      name: 'Predictions',
      marker: { color: '#0284c7', size: 5, opacity: 0.6 }
    };

    const minVal = Math.min(...actual, ...predicted);
    const maxVal = Math.max(...actual, ...predicted);

    const traceLine = {
      x: [minVal, maxVal],
      y: [minVal, maxVal],
      mode: 'lines',
      name: 'Ideal (y = x)',
      line: { color: '#ef4444', dash: 'dash' }
    };

    const layout = {
      ...this.theme,
      title: 'Actual vs Predicted (Held-out Test)',
      xaxis: { title: 'Actual Values' },
      yaxis: { title: 'Predicted Values' }
    };

    Plotly.newPlot(containerId, [tracePoints, traceLine], layout, { responsive: true });
  }
};
