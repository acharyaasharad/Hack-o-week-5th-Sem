"""Export service generating downloadable CSV coordinates and standalone HTML reports.
Maintains row alignment by source _row_id and includes complete dataset attribution.
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
    def export_pca_csv(pca_result: Dict[str, Any]) -> str:
        """Exports PCA coordinates aligned with stable row IDs."""
        coords = pca_result.get("coordinates", [])
        df = pd.DataFrame(coords)
        return df.to_csv(index=False)

    @staticmethod
    def export_tsne_csv(tsne_result: Dict[str, Any]) -> str:
        """Exports t-SNE coordinates aligned with stable row IDs."""
        coords = tsne_result.get("coordinates", [])
        df = pd.DataFrame(coords)
        return df.to_csv(index=False)

    @staticmethod
    def export_combined_csv(comparison_result: Dict[str, Any]) -> str:
        """Exports aligned PCA and t-SNE coordinates in a single consolidated CSV."""
        pca_coords = comparison_result.get("pca", {}).get("coordinates", [])
        tsne_coords = comparison_result.get("tsne", {}).get("coordinates", [])

        df_pca = pd.DataFrame(pca_coords).rename(columns={"x": "pca_pc1", "y": "pca_pc2"})
        df_tsne = pd.DataFrame(tsne_coords).rename(columns={"x": "tsne_dim1", "y": "tsne_dim2"})

        # Merge on row_id
        if not df_pca.empty and not df_tsne.empty:
            merged = pd.merge(df_pca, df_tsne[["row_id", "tsne_dim1", "tsne_dim2"]], on="row_id", how="inner")
            return merged.to_csv(index=False)
        elif not df_pca.empty:
            return df_pca.to_csv(index=False)
        return df_tsne.to_csv(index=False)

    @staticmethod
    def export_loadings_csv(pca_result: Dict[str, Any]) -> str:
        """Exports PCA component loadings table."""
        loadings = pca_result.get("loadings", [])
        df = pd.DataFrame(loadings)
        return df.to_csv(index=False)

    @staticmethod
    def generate_html_report(
        dataset_name: str,
        dataset_source: str,
        total_rows: int,
        pca_result: Optional[Dict[str, Any]],
        tsne_result: Optional[Dict[str, Any]],
    ) -> str:
        """Generates a self-contained executive HTML intelligence report."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        # PCA section data
        pca_pc1 = pca_result.get("pc1_variance", "N/A") if pca_result else "N/A"
        pca_pc2 = pca_result.get("pc2_variance", "N/A") if pca_result else "N/A"
        pca_2d_tot = pca_result.get("total_2d_variance", "N/A") if pca_result else "N/A"
        pca_trust = pca_result.get("trustworthiness", "N/A") if pca_result else "N/A"
        pca_time = pca_result.get("execution_time_seconds", "N/A") if pca_result else "N/A"

        # t-SNE section data
        tsne_perp = tsne_result.get("perplexity", "N/A") if tsne_result else "N/A"
        tsne_iter = tsne_result.get("max_iter", "N/A") if tsne_result else "N/A"
        tsne_kl = tsne_result.get("kl_divergence", "N/A") if tsne_result else "N/A"
        tsne_trust = tsne_result.get("trustworthiness", "N/A") if tsne_result else "N/A"
        tsne_time = tsne_result.get("execution_time_seconds", "N/A") if tsne_result else "N/A"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dimensionality Reduction Intelligence Report — PCA & t-SNE Studio</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #0f172a;
            background: #f8fafc;
            line-height: 1.6;
            margin: 0;
            padding: 40px;
        }}
        .container {{
            max-width: 960px;
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
        h1 {{ margin: 0 0 10px 0; color: #0f172a; font-size: 26px; }}
        h2 {{ color: #0284c7; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px; }}
        .badge {{
            display: inline-block;
            background: #e0f2fe;
            color: #0369a1;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 600;
        }}
        .grid-2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 20px 0;
        }}
        .card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
        }}
        .metric-stat {{
            font-size: 24px;
            font-weight: bold;
            color: #0f172a;
            margin: 4px 0;
        }}
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
            <span class="badge">Unsupervised Machine Learning Studio</span>
            <h1>Dimensionality Reduction Analysis Report</h1>
            <p>Generated on <strong>{timestamp}</strong> &bull; Dataset: <strong>{dataset_name}</strong> ({total_rows} observations)</p>
        </header>

        <section>
            <h2>1. Comparative Executive Summary</h2>
            <div class="grid-2">
                <div class="card">
                    <h3>Principal Component Analysis (PCA)</h3>
                    <p>Linear orthogonal projection maximizing global variance.</p>
                    <div>2D Explained Variance:</div>
                    <div class="metric-stat">{pca_2d_tot}% (PC1: {pca_pc1}%, PC2: {pca_pc2}%)</div>
                    <div>Trustworthiness: <strong>{pca_trust}</strong></div>
                    <div>Runtime: <strong>{pca_time}s</strong></div>
                </div>

                <div class="card">
                    <h3>t-Distributed Stochastic Neighbor Embedding (t-SNE)</h3>
                    <p>Non-linear manifold embedding preserving local neighborhoods.</p>
                    <div>Configuration:</div>
                    <div class="metric-stat">Perplexity {tsne_perp} &bull; {tsne_iter} iters</div>
                    <div>Trustworthiness: <strong>{tsne_trust}</strong></div>
                    <div>KL Divergence: <strong>{tsne_kl}</strong> &bull; Runtime: <strong>{tsne_time}s</strong></div>
                </div>
            </div>
        </section>

        <section>
            <h2>2. Methodological & Interpretation Guidelines</h2>
            <ul>
                <li><strong>PCA</strong> preserves global distances and is inductive (supports transforming future out-of-sample records).</li>
                <li><strong>t-SNE</strong> reveals non-linear cluster geometry by matching local probabilities with Student-t distributions; however, cluster sizes and inter-cluster distances in t-SNE should not be over-interpreted as physical measurements.</li>
            </ul>
        </section>

        <footer>
            <p><strong>Dataset Attribution:</strong> {dataset_source}</p>
            <p>Dimensionality Reduction Visualizer — PCA & t-SNE Studio &bull; Version {config.VERSION}</p>
        </footer>
    </div>
</body>
</html>
"""
        return html_content
