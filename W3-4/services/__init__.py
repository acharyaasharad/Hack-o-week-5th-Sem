"""MovieScope Services Package"""
from .data_manager import DataManager
from .analytics import AnalyticsEngine
from .recommender import MovieRecommender

__all__ = ["DataManager", "AnalyticsEngine", "MovieRecommender"]
