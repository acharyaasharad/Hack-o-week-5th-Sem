"""Experiment service managing persistent experiment history and run configurations.
"""

from typing import Dict, Any, List
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
                logger.warning("Failed loading experiments: %s", e)
                self._history = []

    def _save_history(self):
        try:
            with open(config.EXPERIMENTS_FILE, "w") as f:
                json.dump(self._history, f, indent=2)
        except Exception as e:
            logger.warning("Failed saving experiments: %s", e)

    def log_run(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        entry["id"] = f"EXP-{len(self._history)+1:03d}"
        entry["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._history.insert(0, entry)
        self._save_history()
        return entry

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history
