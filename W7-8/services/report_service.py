"""Report generation service for exporting executive HTML audits and CSV forecast data."""

from pathlib import Path
from typing import Dict, Any, List, Optional
import io
import csv
import logging
import pandas as pd

import config

logger = logging.getLogger(__name__)


class ReportService:
    """Creates downloadable HTML executive reports and CSV prediction datasets."""

    @staticmethod
    def generate_html_report(
        dataset_meta: Dict[str, Any],
        model_results: Dict[str, Any],
        forecast_results: Optional[Dict[str, Any]] = None,
        optimization_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Renders an executive standalone HTML analytical report."""
        best_model = model_results.get("best_model_name", "Seasonal Naive")
        test_metrics = model_results.get("test_metrics", {})
        arena = model_results.get("arena_results", {})

        # Model comparison rows
        arena_rows_html = ""
        for m_key, m_val in arena.items():
            vm = m_val.get("val_metrics", {})
            is_best = (m_key == model_results.get("best_model"))
            badge = '<span style="background:#0d9488;color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;">Selected</span>' if is_best else ""
            arena_rows_html += f"""
            <tr>
              <td><strong>{m_val.get('display_name', m_key)}</strong> {badge}</td>
              <td>{m_val.get('train_duration_sec', 0.0)}s</td>
              <td>{vm.get('mae', '—')}</td>
              <td>{vm.get('rmse', '—')}</td>
              <td>{vm.get('wape', '—')}%</td>
              <td>{vm.get('r2', '—')}</td>
            </tr>
            """

        # Forecast rows
        forecast_rows_html = ""
        if forecast_results and "forecast_series" in forecast_results:
            for pt in forecast_results["forecast_series"][:24]:
                forecast_rows_html += f"""
                <tr>
                  <td>{pt.get('step')}</td>
                  <td>{pt.get('timestamp')}</td>
                  <td><strong>{pt.get('predicted_demand')} kW</strong></td>
                  <td>{pt.get('lower_bound')} kW</td>
                  <td>{pt.get('upper_bound')} kW</td>
                </tr>
                """

        # Optimization summary
        opt_summary_html = ""
        if optimization_results and optimization_results.get("success"):
            sm = optimization_results.get("summary", {})
            opt_summary_html = f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:24px;">
              <h3 style="margin-top:0;color:#0f172a;">Load Optimization Scenario Summary</h3>
              <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;">
                <div style="background:#fff;padding:12px;border:1px solid #e2e8f0;border-radius:6px;">
                  <div style="font-size:12px;color:#64748b;">Peak Reduction</div>
                  <div style="font-size:18px;font-weight:700;color:#0d9488;">{sm.get('peak_reduction_pct')}%</div>
                  <div style="font-size:11px;color:#475569;">From {sm.get('baseline_peak')} to {sm.get('optimized_peak')} kW</div>
                </div>
                <div style="background:#fff;padding:12px;border:1px solid #e2e8f0;border-radius:6px;">
                  <div style="font-size:12px;color:#64748b;">Cost Savings</div>
                  <div style="font-size:18px;font-weight:700;color:#059669;">{sm.get('cost_savings_pct')}%</div>
                  <div style="font-size:11px;color:#475569;">${sm.get('optimized_cost')} vs ${sm.get('baseline_cost')}</div>
                </div>
                <div style="background:#fff;padding:12px;border:1px solid #e2e8f0;border-radius:6px;">
                  <div style="font-size:12px;color:#64748b;">Energy Delivered</div>
                  <div style="font-size:18px;font-weight:700;color:#0284c7;">{sm.get('scheduled_energy')} kWh</div>
                  <div style="font-size:11px;color:#475569;">100% Conserved</div>
                </div>
                <div style="background:#fff;padding:12px;border:1px solid #e2e8f0;border-radius:6px;">
                  <div style="font-size:12px;color:#64748b;">Optimizer Status</div>
                  <div style="font-size:18px;font-weight:700;color:#0f172a;">Optimal</div>
                  <div style="font-size:11px;color:#475569;">SciPy HiGHS Solver</div>
                </div>
              </div>
            </div>
            """

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Energy Demand Forecasting & Optimization Executive Report</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      color: #0f172a;
      background: #f8fafc;
      padding: 32px 16px;
    }}
    .container {{
      max-width: 960px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
      padding: 40px;
    }}
    h1 {{ color: #0f172a; margin-top: 0; font-size: 26px; border-bottom: 2px solid #0d9488; padding-bottom: 12px; }}
    h2 {{ color: #1e293b; font-size: 18px; margin-top: 28px; margin-bottom: 12px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 24px; font-size: 14px; }}
    th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
    th {{ background: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 12px; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background: #ecfdf5; color: #065f46; }}
    .disclaimer {{ background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 14px; border-radius: 6px; font-size: 13px; color: #92400e; margin-top: 32px; }}
    .meta-box {{ display: flex; gap: 24px; font-size: 13px; color: #64748b; margin-bottom: 24px; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>Energy Demand Forecasting & Optimization Executive Report</h1>
    
    <div class="meta-box">
      <div><strong>Dataset:</strong> {dataset_meta.get('source_name', 'Tetouan City')}</div>
      <div><strong>Target:</strong> {dataset_meta.get('target_column', 'Zone1Power')}</div>
      <div><strong>Resolution:</strong> 1-Hour Mean Aggregation</div>
      <div><strong>Selected Model:</strong> <span class="badge">{best_model}</span></div>
    </div>

    <h2>1. Model Comparison & Arena Leaderboard</h2>
    <table>
      <thead>
        <tr>
          <th>Algorithm</th>
          <th>Train Duration</th>
          <th>Validation MAE</th>
          <th>Validation RMSE</th>
          <th>Validation WAPE</th>
          <th>Validation R²</th>
        </tr>
      </thead>
      <tbody>
        {arena_rows_html}
      </tbody>
    </table>

    <div style="background:#f1f5f9;padding:12px 16px;border-radius:6px;font-size:13px;margin-bottom:24px;">
      <strong>Held-out Test Performance ({best_model}):</strong>
      MAE: <strong>{test_metrics.get('mae', '—')} kW</strong> | 
      RMSE: <strong>{test_metrics.get('rmse', '—')} kW</strong> | 
      WAPE: <strong>{test_metrics.get('wape', '—')}%</strong> | 
      R²: <strong>{test_metrics.get('r2', '—')}</strong>
    </div>

    {opt_summary_html}

    <h2>2. 24-Hour Forward Forecast Horizon</h2>
    <table>
      <thead>
        <tr>
          <th>Hour Step</th>
          <th>Timestamp</th>
          <th>Forecast Demand</th>
          <th>95% Lower Bound</th>
          <th>95% Upper Bound</th>
        </tr>
      </thead>
      <tbody>
        {forecast_rows_html if forecast_rows_html else '<tr><td colspan="5">No active forecast generated.</td></tr>'}
      </tbody>
    </table>

    <div class="disclaimer">
      <strong>Analytical Disclaimer & System Limitations:</strong><br>
      This report was generated by the Energy Demand Forecasting & Optimization platform.
      Predictions represent recursive statistical and machine learning extrapolations. Future weather covariates are obtained via Open-Meteo forecasts.
      Load shifting optimization results simulate demand-side management via linear programming; cost savings are illustrative estimations based on configured Time-Of-Use tariffs, not guaranteed commercial billing reductions.
    </div>
  </div>
</body>
</html>
"""
        return html

    @staticmethod
    def export_forecast_csv(forecast_series: List[Dict[str, Any]]) -> str:
        """Converts forecast series into CSV string."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["step", "timestamp", "predicted_demand_kw", "lower_bound_kw", "upper_bound_kw"])
        for pt in forecast_series:
            writer.writerow([
                pt.get("step"),
                pt.get("timestamp"),
                pt.get("predicted_demand"),
                pt.get("lower_bound"),
                pt.get("upper_bound"),
            ])
        return output.getvalue()
