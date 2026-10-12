"""ChartService generating server-side analytical charts via Matplotlib & Seaborn.
Uses non-interactive Agg backend for thread safety, leak prevention, and high-DPI rendering.
"""

from pathlib import Path
from typing import Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import logging

import config
from services.data_manager import DataManager

logger = logging.getLogger(__name__)


class ChartService:
    """Generates server-side statistical charts saved as high-resolution PNGs."""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.charts_dir = config.CHARTS_DIR
        self.charts_dir.mkdir(parents=True, exist_ok=True)

        # Apply dark football analytics style palette
        self.theme = config.THEME

    def set_data_manager(self, data_manager: DataManager) -> None:
        """Updates active DataManager."""
        self.data_manager = data_manager

    def _setup_figure_style(self, fig, ax, title: str, xlabel: str, ylabel: str) -> None:
        """Applies cohesive dark pitch theme styling to Matplotlib axes."""
        fig.patch.set_facecolor(self.theme["card_bg"])
        ax.set_facecolor(self.theme["card_bg"])

        ax.set_title(title, fontsize=13, fontweight="bold", color=self.theme["text"], pad=14)
        ax.set_xlabel(xlabel, fontsize=10.5, color=self.theme["text_muted"], labelpad=8)
        ax.set_ylabel(ylabel, fontsize=10.5, color=self.theme["text_muted"], labelpad=8)

        ax.tick_params(colors=self.theme["text_muted"], labelsize=9.5)
        ax.grid(color=self.theme["grid"], linestyle="--", linewidth=0.7, alpha=0.7)

        for spine in ax.spines.values():
            spine.set_color(self.theme["border"])

    def generate_correlation_heatmap(self, filename: str = "correlation_heatmap.png") -> Path:
        """Chart 1: Numerical Feature Correlation Matrix via Seaborn."""
        out_path = self.charts_dir / filename
        df = self.data_manager.get_players_df()

        fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=150)

        cols = ["age", "minutes_played", "goals", "assists", "xg", "xa", "key_passes", "rating"]
        valid_cols = [c for c in cols if c in df.columns]

        if df.empty or len(valid_cols) < 3:
            ax.text(0.5, 0.5, "Insufficient numeric data for correlation", ha="center", va="center", color="white")
            self._setup_figure_style(fig, ax, "Correlation Heatmap", "", "")
        else:
            labels_map = {
                "age": "Age",
                "minutes_played": "Minutes",
                "goals": "Goals",
                "assists": "Assists",
                "xg": "xG",
                "xa": "xA",
                "key_passes": "Key Passes",
                "rating": "Rating",
            }
            corr = df[valid_cols].rename(columns=labels_map).corr()

            # Green-teal pitch colormap (NO PURPLE)
            sns.heatmap(
                corr,
                annot=True,
                fmt=".2f",
                cmap="YlGnBu",
                vmin=-1.0,
                vmax=1.0,
                linewidths=1.2,
                linecolor=self.theme["card_bg"],
                cbar_kws={"shrink": 0.8},
                ax=ax,
            )

            fig.patch.set_facecolor(self.theme["card_bg"])
            ax.set_facecolor(self.theme["card_bg"])
            ax.set_title("Tactical Metric Correlation Matrix", fontsize=13, fontweight="bold", color=self.theme["text"], pad=14)
            ax.tick_params(colors=self.theme["text_muted"], labelsize=9.5)

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_position_comparison(self, filename: str = "position_comparison.png") -> Path:
        """Chart 2: Grouped Bar Chart of Goals & Assists by Position."""
        out_path = self.charts_dir / filename
        df = self.data_manager.get_players_df()

        fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=150)

        if df.empty:
            ax.text(0.5, 0.5, "No player data available", ha="center", va="center", color="white")
            self._setup_figure_style(fig, ax, "Goals & Assists by Position", "Position", "Count")
        else:
            grouped = df.groupby("position").agg(
                total_goals=("goals", "sum"),
                total_assists=("assists", "sum"),
            ).reindex(["Goalkeeper", "Defender", "Midfielder", "Forward"]).fillna(0)

            positions = grouped.index.tolist()
            x = np.arange(len(positions))
            width = 0.35

            bars1 = ax.bar(x - width/2, grouped["total_goals"], width, label="Total Goals", color=self.theme["accent_emerald"], edgecolor="#059669")
            bars2 = ax.bar(x + width/2, grouped["total_assists"], width, label="Total Assists", color=self.theme["accent_lime"], edgecolor="#65a30d")

            # Annotations
            for bar in list(bars1) + list(bars2):
                h = bar.get_height()
                if h > 0:
                    ax.annotate(
                        f"{int(h)}",
                        xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 2),
                        textcoords="offset points",
                        ha="center",
                        va="bottom",
                        fontsize=8.5,
                        color=self.theme["text"],
                    )

            ax.set_xticks(x)
            ax.set_xticklabels(positions)
            ax.legend(facecolor=self.theme["card_bg"], edgecolor=self.theme["border"], labelcolor=self.theme["text"])
            self._setup_figure_style(fig, ax, "Aggregate Scoring & Creative Output by Position", "Tactical Position", "Total Count")

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_rating_distribution(self, filename: str = "rating_distribution.png") -> Path:
        """Chart 3: Player Rating Histogram & KDE Distribution via Seaborn."""
        out_path = self.charts_dir / filename
        df = self.data_manager.get_players_df()

        fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)

        if df.empty or "rating" not in df.columns:
            ax.text(0.5, 0.5, "No rating data available", ha="center", va="center", color="white")
            self._setup_figure_style(fig, ax, "Rating Distribution", "Rating", "Frequency")
        else:
            sns.histplot(
                data=df,
                x="rating",
                bins=12,
                kde=True,
                color=self.theme["accent_emerald"],
                edgecolor="#065f46",
                alpha=0.85,
                ax=ax,
            )
            self._setup_figure_style(
                fig,
                ax,
                "Player Performance Rating Distribution (0.0 to 10.0 Scale)",
                "Match Rating (★)",
                "Number of Players",
            )

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path

    def generate_age_performance_scatter(self, filename: str = "age_performance.png") -> Path:
        """Chart 4: Age versus Performance Rating Scatter Plot with Trendline."""
        out_path = self.charts_dir / filename
        df = self.data_manager.get_players_df()

        fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)

        if df.empty or len(df) < 3:
            ax.text(0.5, 0.5, "Insufficient data for scatter plot", ha="center", va="center", color="white")
            self._setup_figure_style(fig, ax, "Age vs Rating", "Age", "Rating")
        else:
            sns.scatterplot(
                data=df,
                x="age",
                y="rating",
                hue="position",
                palette={
                    "Goalkeeper": "#f59e0b",
                    "Defender": "#06b6d4",
                    "Midfielder": "#10b981",
                    "Forward": "#f43f5e",
                },
                s=60,
                alpha=0.85,
                edgecolor="#0f172a",
                ax=ax,
            )

            # Regression line
            sns.regplot(
                data=df,
                x="age",
                y="rating",
                scatter=False,
                color=self.theme["accent_lime"],
                ax=ax,
                line_kws={"linewidth": 1.6, "linestyle": "--"},
            )

            ax.legend(facecolor=self.theme["card_bg"], edgecolor=self.theme["border"], labelcolor=self.theme["text"])
            self._setup_figure_style(
                fig,
                ax,
                "Age Profile vs Performance Rating with Linear Trend",
                "Player Age (Years)",
                "Performance Rating (★)",
            )

        plt.tight_layout()
        fig.savefig(out_path, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        return out_path
