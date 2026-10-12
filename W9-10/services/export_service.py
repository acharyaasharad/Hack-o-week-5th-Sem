"""Export service generating downloadable CSV data and standalone HTML intelligence reports.
Preserves dataset attribution, parameter configurations, cluster profiles, and evaluation metrics.
"""

from typing import Dict, Any, List, Optional
import time
import io
import pandas as pd
import logging

import config

logger = logging.getLogger(__name__)

class ExportService:
    @staticmethod
    def export_labeled_dataset_csv(df: pd.DataFrame, labels: List[int]) -> str:
        """Appends cluster labels and exports full CSV."""
        df_out = df.copy()
        df_out["Cluster_Label"] = labels
        df_out["Cluster_Name"] = [
            "Noise_Outlier" if l == -1 else f"Cluster_{l}" for l in labels
        ]
        return df_out.to_csv(index=False)

    @staticmethod
    def export_cluster_profiles_csv(profiles: Dict[str, Any]) -> str:
        """Exports cluster profile metrics and spending averages to CSV."""
        rows = []
        clusters_data = profiles.get("clusters", {})
        
        for name, data in clusters_data.items():
            row = {
                "Cluster": name,
                "Cluster_ID": data["cluster_id"],
                "Is_Noise": data["is_noise"],
                "Customer_Count": data["customer_count"],
                "Percentage_of_Total": f"{data['percentage_of_total']}%",
                "Description": data["derived_description"],
            }
            # Append means
            for feature, mean_val in data["means"].items():
                row[f"Mean_{feature}"] = mean_val
            # Append medians
            for feature, med_val in data["medians"].items():
                row[f"Median_{feature}"] = med_val
            rows.append(row)

        df_prof = pd.DataFrame(rows)
        return df_prof.to_csv(index=False)

    @staticmethod
    def generate_html_report(
        dataset_name: str,
        dataset_source: str,
        total_rows: int,
        features_used: List[str],
        result: Dict[str, Any],
        profiles: Dict[str, Any],
    ) -> str:
        """Generates a comprehensive, self-contained HTML executive report."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        algo_name = result.get("algorithm_name", "Clustering")
        n_clusters = result.get("cluster_count", 0)
        noise_pct = result.get("noise_percentage", 0.0)
        metrics = result.get("metrics", {})
        sil = metrics.get("silhouette_score")
        db = metrics.get("davies_bouldin_index")
        ch = metrics.get("calinski_harabasz_score")
        exec_time = result.get("execution_time_seconds", 0.0)
        prep = result.get("preprocessing", {})
        
        # Build cluster profile cards HTML
        cluster_cards_html = []
        for name, pdata in profiles.get("clusters", {}).items():
            means_items = "".join([f"<li><strong>{k}:</strong> ${v:,.2f}</li>" for k, v in pdata["means"].items()])
            actions_items = "".join([f"<li>{a}</li>" for a in pdata.get("suggested_actions", [])])
            card = f"""
            <div class="report-card">
                <h3>{name} ({pdata['customer_count']} customers &bull; {pdata['percentage_of_total']}%)</h3>
                <p><em>{pdata['derived_description']}</em></p>
                <div class="grid-2">
                    <div>
                        <h4>Category Average Spend</h4>
                        <ul>{means_items}</ul>
                    </div>
                    <div>
                        <h4>Strategic Action Recommendations</h4>
                        <ul>{actions_items}</ul>
                    </div>
                </div>
            </div>
            """
            cluster_cards_html.append(card)

        report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Customer Segmentation Executive Report — {algo_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background-color: #f8fafc;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: #ffffff;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
        }}
        header {{
            border-bottom: 2px solid #0284c7;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{ margin: 0 0 10px 0; color: #0f172a; font-size: 28px; }}
        h2 {{ color: #0369a1; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #0f172a; margin-top: 0; }}
        .badge {{
            display: inline-block;
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 25px 0;
        }}
        .metric-card {{
            background: #f1f5f9;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #0284c7;
        }}
        .metric-val {{
            font-size: 26px;
            font-weight: bold;
            color: #0f172a;
            margin-top: 5px;
        }}
        .report-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        ul {{ padding-left: 20px; margin: 8px 0; }}
        footer {{
            margin-top: 50px;
            border-top: 1px solid #cbd5e1;
            padding-top: 20px;
            font-size: 12px;
            color: #64748b;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="badge">Unsupervised Machine Learning Intelligence</span>
            <h1>Customer Segmentation & Intelligence Report</h1>
            <p>Generated on <strong>{timestamp}</strong> &bull; Framework: scikit-learn Pipeline &bull; Dataset: {dataset_name}</p>
        </header>

        <section>
            <h2>1. Executive Summary & Configuration</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div>Algorithm</div>
                    <div class="metric-val">{algo_name}</div>
                </div>
                <div class="metric-card">
                    <div>Customer Cohorts</div>
                    <div class="metric-val">{n_clusters}</div>
                </div>
                <div class="metric-card">
                    <div>Noise / Outliers</div>
                    <div class="metric-val">{noise_pct}%</div>
                </div>
                <div class="metric-card">
                    <div>Execution Time</div>
                    <div class="metric-val">{exec_time}s</div>
                </div>
            </div>

            <p><strong>Clustering Features Used:</strong> {', '.join(features_used)}</p>
            <p><strong>Preprocessing Pipeline:</strong> Scaler={prep.get('scaling_method')}, Log-Transform={prep.get('log_transform')}, Imputer={prep.get('numeric_impute_strategy')}.</p>
        </section>

        <section>
            <h2>2. Quantitative Validation Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div>Silhouette Score</div>
                    <div class="metric-val">{sil if sil is not None else 'N/A'}</div>
                    <small>Optimal: Higher (Range: -1 to 1)</small>
                </div>
                <div class="metric-card">
                    <div>Davies–Bouldin Index</div>
                    <div class="metric-val">{db if db is not None else 'N/A'}</div>
                    <small>Optimal: Lower (Min: 0)</small>
                </div>
                <div class="metric-card">
                    <div>Calinski–Harabasz Score</div>
                    <div class="metric-val">{ch if ch is not None else 'N/A'}</div>
                    <small>Optimal: Higher</small>
                </div>
            </div>
            <p><em>Note: Unsupervised clustering metrics measure geometric separation and density in scaled space; they are heuristic indicators, not absolute business verifications.</em></p>
        </section>

        <section>
            <h2>3. Discovered Customer Segments & Profiles</h2>
            {''.join(cluster_cards_html)}
        </section>

        <footer>
            <p><strong>Dataset Attribution:</strong> {dataset_source}</p>
            <p>Customer Segmentation & Intelligence Dashboard &bull; Antigravity Platform &bull; Version {config.VERSION}</p>
        </footer>
    </div>
</body>
</html>
"""
        return report_html
