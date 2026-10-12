"""Export service generating downloadable CSV data and standalone HTML intelligence reports.
"""

from typing import Dict, Any, List, Optional
import time
import pandas as pd
import logging

import config

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    def export_comparison_csv(leaderboard: List[Dict[str, Any]]) -> str:
        """Exports model leaderboard comparison rows to CSV."""
        rows = []
        for item in leaderboard:
            row = {
                "Model": item["model_id"],
                "Task": item["task"],
                "Train_Score": item["primary_train_score"],
                "Validation_Score": item["primary_val_score"],
                "Generalization_Gap": item["generalization_gap"],
                "Training_Time_Seconds": item["train_time_seconds"],
            }
            # Append detailed metrics
            vm = item.get("val_metrics", {})
            for k, v in vm.items():
                if isinstance(v, (int, float)):
                    row[f"val_{k}"] = v
            rows.append(row)

        df = pd.DataFrame(rows)
        return df.to_csv(index=False)

    @staticmethod
    def generate_html_report(
        dataset_name: str,
        dataset_source: str,
        task: str,
        leaderboard: List[Dict[str, Any]],
        best_model: Dict[str, Any],
        test_evaluation: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generates self-contained executive HTML intelligence report."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        leaderboard_rows = "".join([
            f"<tr><td><strong>{m['model_id']}</strong></td><td>{m['primary_train_score']}</td>"
            f"<td><strong>{m['primary_val_score']}</strong></td><td>{m['generalization_gap']}</td>"
            f"<td>{m['train_time_seconds']}s</td></tr>"
            for m in leaderboard
        ])

        test_html = ""
        if test_evaluation and "test_metrics" in test_evaluation:
            tm = test_evaluation["test_metrics"]
            metrics_list = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in tm.items() if isinstance(v, (int, float))])
            test_html = f"""
            <div class="card" style="margin-top:20px; border-left:4px solid #10b981;">
                <h3>Final Evaluation on Held-Out Test Split</h3>
                <p>Model evaluated strictly on unseen test observations ({test_evaluation.get('test_samples')} rows):</p>
                <ul>{metrics_list}</ul>
            </div>
            """

        html_str = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ensemble Learning & Generalization Intelligence Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; color: #0f172a; background: #f8fafc; padding: 40px; margin: 0; }}
        .container {{ max-width: 960px; margin: 0 auto; background: #ffffff; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
        header {{ border-bottom: 2px solid #4f46e5; padding-bottom: 20px; margin-bottom: 30px; }}
        h1 {{ margin: 0 0 10px 0; font-size: 26px; }}
        h2 {{ color: #4f46e5; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; }}
        .badge {{ display: inline-block; background: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 13.5px; }}
        th {{ background: #f8fafc; padding: 10px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; }}
        footer {{ margin-top: 50px; border-top: 1px solid #cbd5e1; padding-top: 20px; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="badge">Machine Learning Generalization Lab</span>
            <h1>Ensemble Learning & Generalization Report</h1>
            <p>Generated on <strong>{timestamp}</strong> &bull; Dataset: <strong>{dataset_name}</strong> &bull; Task: <strong>{task.upper()}</strong></p>
        </header>

        <section>
            <h2>1. Model Arena Leaderboard</h2>
            <table>
                <thead>
                    <tr><th>Model</th><th>Train Score</th><th>Validation Score</th><th>Generalization Gap</th><th>Runtime</th></tr>
                </thead>
                <tbody>{leaderboard_rows}</tbody>
            </table>
        </section>

        {test_html}

        <section>
            <h2>2. Generalization & Bias–Variance Insights</h2>
            <ul>
                <li><strong>Generalization Gap:</strong> Measures difference between training score and validation score ($\text{{Score}}_{{train}} - \text{{Score}}_{{val}}$). A large positive gap signals variance / overfitting.</li>
                <li><strong>Ensemble Advantage:</strong> Bagging and Random Forests reduce model variance through bootstrap aggregation, while Gradient Boosting, XGBoost, and LightGBM progressively reduce bias and variance with shrinkage.</li>
            </ul>
        </section>

        <footer>
            <p><strong>Dataset Attribution:</strong> {dataset_source}</p>
            <p>Ensemble Learning & Generalization Lab &bull; Version {config.VERSION}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html_str
