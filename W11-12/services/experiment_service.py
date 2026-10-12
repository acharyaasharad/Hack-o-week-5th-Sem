"""Experiment service managing history log of PCA and t-SNE configurations.
Tracks parameters, runtimes, explained variance, and trustworthiness.
"""

from typing import Dict, Any, List, Optional
import json
import time
import logging

import config

logger = logging.getLogger(__name__)

class ExperimentService:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []
        self._load_history()

    def _load_history(self):
        if config.EXPERIMENTS_FILE.exists():
            try:
                with open(config.EXPERIMENTS_FILE, "r") as f:
                    self._history = json.load(f)
            except Exception as e:
                logger.warning("Failed loading experiments history: %s", e)
                self._history = []

    def _save_history(self):
        try:
            with open(config.EXPERIMENTS_FILE, "w") as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.warning("Failed saving experiments history: %s", e)

    def log_run(
        self,
        method: str,
        dataset_name: str,
        n_samples: int,
        n_features: int,
        config_params: Dict[str, Any],
        metrics: Dict[str, Any],
        exec_time: float,
    ) -> Dict[str, Any]:
        """Logs a completed run into experiment history."""
        entry = {
            "id": f"EXP-{len(self._history)+1:03d}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": method.upper(),
            "dataset_name": dataset_name,
            "n_samples": n_samples,
            "n_features": n_features,
            "configuration": config_params,
            "metrics": metrics,
            "execution_time_seconds": exec_time,
        }
        self._history.insert(0, entry)
        self._save_history()
        return entry

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history
