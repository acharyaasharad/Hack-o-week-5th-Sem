"""Model registry managing instantiation of classification and regression algorithms:
Dummy baselines, Logistic Regression, Ridge/Lasso, Decision Trees, Bagging, Random Forest,
Gradient Boosting, HistGradientBoosting, XGBoost, and LightGBM.
"""

from typing import Dict, Any, List, Optional
import inspect
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, Ridge, Lasso, LinearRegression
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import (
    BaggingClassifier,
    BaggingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
    GradientBoostingClassifier,
    GradientBoostingRegressor,
)
import logging

import config

logger = logging.getLogger(__name__)

# Check XGBoost & LightGBM availability
XGB_AVAILABLE = False
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

LGBM_AVAILABLE = False
try:
    import lightgbm as lgb
    LGBM_AVAILABLE = True
except ImportError:
    LGBM_AVAILABLE = False

class ModelRegistry:
    @staticmethod
    def get_supported_models(task: str = "classification") -> List[Dict[str, Any]]:
        """Returns catalog of models and supported parameters for the active task."""
        if task == "classification":
            models = [
                {"id": "dummy", "name": "Dummy Baseline", "family": "Baseline", "description": "Predicts most frequent class label."},
                {"id": "logistic_l2", "name": "Logistic Regression (L2)", "family": "Linear", "description": "Ridge regularized linear classifier."},
                {"id": "logistic_l1", "name": "Logistic Regression (L1)", "family": "Linear", "description": "Lasso regularized linear classifier (sparse coefficients)."},
                {"id": "decision_tree", "name": "Decision Tree", "family": "Tree", "description": "Single recursive decision tree (high variance)."},
                {"id": "bagging", "name": "Bagging (Bootstrap Aggregation)", "family": "Bagging", "description": "Ensemble of independent trees on bootstrap samples."},
                {"id": "random_forest", "name": "Random Forest", "family": "Bagging", "description": "Ensemble of decorrelated randomized trees."},
                {"id": "gradient_boosting", "name": "Gradient Boosting", "family": "Boosting", "description": "Sequential additive gradient tree boosting."},
            ]
            if XGB_AVAILABLE:
                models.append({"id": "xgboost", "name": "XGBoost", "family": "Boosting", "description": "Extreme Gradient Boosting with regularized objective."})
            if LGBM_AVAILABLE:
                models.append({"id": "lightgbm", "name": "LightGBM", "family": "Boosting", "description": "Fast histogram-based gradient boosted trees."})
            return models
        else:
            models = [
                {"id": "dummy", "name": "Dummy Baseline", "family": "Baseline", "description": "Predicts mean target value."},
                {"id": "linear", "name": "Linear Regression (OLS)", "family": "Linear", "description": "Ordinary least squares regression."},
                {"id": "ridge", "name": "Ridge Regression (L2)", "family": "Linear", "description": "L2 regularized regression shrinking weights."},
                {"id": "lasso", "name": "Lasso Regression (L1)", "family": "Linear", "description": "L1 regularized regression yielding sparse weights."},
                {"id": "decision_tree", "name": "Decision Tree Regressor", "family": "Tree", "description": "Single piece-wise constant decision tree."},
                {"id": "bagging", "name": "Bagging Regressor", "family": "Bagging", "description": "Bootstrap aggregation of regression trees."},
                {"id": "random_forest", "name": "Random Forest Regressor", "family": "Bagging", "description": "Averaging ensemble of randomized regression trees."},
                {"id": "gradient_boosting", "name": "Gradient Boosting Regressor", "family": "Boosting", "description": "Sequential residual boosting regressor."},
            ]
            if XGB_AVAILABLE:
                models.append({"id": "xgboost", "name": "XGBoost Regressor", "family": "Boosting", "description": "Regularized tree boosting for continuous targets."})
            if LGBM_AVAILABLE:
                models.append({"id": "lightgbm", "name": "LightGBM Regressor", "family": "Boosting", "description": "Histogram-based boosting for continuous targets."})
            return models

    @staticmethod
    def create_estimator(model_id: str, task: str = "classification", params: Optional[Dict[str, Any]] = None) -> Any:
        """Instantiates the specific estimator with version-compatible parameters."""
        params = params or {}
        rand = int(params.get("random_state", config.RANDOM_STATE))

        if task == "classification":
            if model_id == "dummy":
                return DummyClassifier(strategy="most_frequent")
            elif model_id == "logistic_l2":
                c = float(params.get("C", 1.0))
                return LogisticRegression(penalty="l2", C=c, max_iter=1000, random_state=rand)
            elif model_id == "logistic_l1":
                c = float(params.get("C", 1.0))
                return LogisticRegression(penalty="l1", solver="saga", C=c, max_iter=1000, random_state=rand)
            elif model_id == "decision_tree":
                max_depth = params.get("max_depth")
                max_depth = int(max_depth) if max_depth is not None else None
                return DecisionTreeClassifier(max_depth=max_depth, random_state=rand)
            elif model_id == "bagging":
                n_est = int(params.get("n_estimators", 15))
                # Check version compatibility: estimator vs base_estimator
                sig = inspect.signature(BaggingClassifier.__init__)
                base_tree = DecisionTreeClassifier(random_state=rand)
                if "estimator" in sig.parameters:
                    return BaggingClassifier(estimator=base_tree, n_estimators=n_est, random_state=rand)
                return BaggingClassifier(base_estimator=base_tree, n_estimators=n_est, random_state=rand)
            elif model_id == "random_forest":
                n_est = int(params.get("n_estimators", 50))
                max_depth = params.get("max_depth")
                max_depth = int(max_depth) if max_depth is not None else None
                return RandomForestClassifier(n_estimators=n_est, max_depth=max_depth, random_state=rand)
            elif model_id == "gradient_boosting":
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                return GradientBoostingClassifier(n_estimators=n_est, learning_rate=lr, random_state=rand)
            elif model_id == "xgboost":
                if not XGB_AVAILABLE:
                    raise ImportError("xgboost package is not installed.")
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                max_depth = int(params.get("max_depth", 6))
                reg_alpha = float(params.get("reg_alpha", 0.0))
                reg_lambda = float(params.get("reg_lambda", 1.0))
                return xgb.XGBClassifier(
                    n_estimators=n_est,
                    learning_rate=lr,
                    max_depth=max_depth,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    random_state=rand,
                    eval_metric="logloss"
                )
            elif model_id == "lightgbm":
                if not LGBM_AVAILABLE:
                    raise ImportError("lightgbm package is not installed.")
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                reg_alpha = float(params.get("reg_alpha", 0.0))
                reg_lambda = float(params.get("reg_lambda", 0.0))
                return lgb.LGBMClassifier(
                    n_estimators=n_est,
                    learning_rate=lr,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    random_state=rand,
                    verbose=-1
                )
            else:
                raise ValueError(f"Unknown classification model ID '{model_id}'")
        else: # Regression
            if model_id == "dummy":
                return DummyRegressor(strategy="mean")
            elif model_id == "linear":
                return LinearRegression()
            elif model_id == "ridge":
                alpha = float(params.get("alpha", 1.0))
                return Ridge(alpha=alpha, random_state=rand)
            elif model_id == "lasso":
                alpha = float(params.get("alpha", 1.0))
                return Lasso(alpha=alpha, random_state=rand)
            elif model_id == "decision_tree":
                max_depth = params.get("max_depth")
                max_depth = int(max_depth) if max_depth is not None else None
                return DecisionTreeRegressor(max_depth=max_depth, random_state=rand)
            elif model_id == "bagging":
                n_est = int(params.get("n_estimators", 15))
                sig = inspect.signature(BaggingRegressor.__init__)
                base_tree = DecisionTreeRegressor(random_state=rand)
                if "estimator" in sig.parameters:
                    return BaggingRegressor(estimator=base_tree, n_estimators=n_est, random_state=rand)
                return BaggingRegressor(base_estimator=base_tree, n_estimators=n_est, random_state=rand)
            elif model_id == "random_forest":
                n_est = int(params.get("n_estimators", 50))
                max_depth = params.get("max_depth")
                max_depth = int(max_depth) if max_depth is not None else None
                return RandomForestRegressor(n_estimators=n_est, max_depth=max_depth, random_state=rand)
            elif model_id == "gradient_boosting":
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                return GradientBoostingRegressor(n_estimators=n_est, learning_rate=lr, random_state=rand)
            elif model_id == "xgboost":
                if not XGB_AVAILABLE:
                    raise ImportError("xgboost package is not installed.")
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                max_depth = int(params.get("max_depth", 6))
                reg_alpha = float(params.get("reg_alpha", 0.0))
                reg_lambda = float(params.get("reg_lambda", 1.0))
                return xgb.XGBRegressor(
                    n_estimators=n_est,
                    learning_rate=lr,
                    max_depth=max_depth,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    random_state=rand
                )
            elif model_id == "lightgbm":
                if not LGBM_AVAILABLE:
                    raise ImportError("lightgbm package is not installed.")
                n_est = int(params.get("n_estimators", 50))
                lr = float(params.get("learning_rate", 0.1))
                reg_alpha = float(params.get("reg_alpha", 0.0))
                reg_lambda = float(params.get("reg_lambda", 0.0))
                return lgb.LGBMRegressor(
                    n_estimators=n_est,
                    learning_rate=lr,
                    reg_alpha=reg_alpha,
                    reg_lambda=reg_lambda,
                    random_state=rand,
                    verbose=-1
                )
            else:
                raise ValueError(f"Unknown regression model ID '{model_id}'")
