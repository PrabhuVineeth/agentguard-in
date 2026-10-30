"""Gradient boosting baseline on handcrafted graph features (Component C Baseline)."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from agentguard.graph.trajectory_graph import TrajectoryGraph


class GraphFeatureBaseline:
    """Component C Baseline: Gradient Boosted Trees on topological trajectory graph features."""

    def __init__(self, include_untrusted_flag: bool = True):
        self.include_untrusted_flag = include_untrusted_flag
        self.model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=3,
            random_state=42,
        )
        self.feature_names: List[str] = []
        self.is_fitted = False

    def _extract_vector(self, graph: TrajectoryGraph) -> List[float]:
        feats = graph.extract_handcrafted_features(include_untrusted_flag=self.include_untrusted_flag)
        if not self.feature_names:
            self.feature_names = sorted(feats.keys())
        return [feats[k] for k in self.feature_names]

    def train(self, graphs: List[TrajectoryGraph], labels: List[int]):
        """Fit gradient boosting model on graph features."""
        X = np.array([self._extract_vector(g) for g in graphs])
        y = np.array(labels)
        self.model.fit(X, y)
        self.is_fitted = True

    def score(self, graph: TrajectoryGraph) -> float:
        """Return predicted probability of hijacked trajectory [0.0, 1.0]."""
        if not self.is_fitted:
            return 0.5
        x = np.array([self._extract_vector(graph)])
        prob = self.model.predict_proba(x)[0, 1]
        return float(prob)

    def save(self, model_dir: Path):
        """Save model weights and feature names."""
        import joblib
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, model_dir / "gradient_boosting.joblib")
        with open(model_dir / "baseline_config.json", "w", encoding="utf-8") as f:
            json.dump({
                "include_untrusted_flag": self.include_untrusted_flag,
                "feature_names": self.feature_names,
            }, f, indent=2)

    def load(self, model_dir: Path):
        """Load trained weights from disk."""
        import joblib
        self.model = joblib.load(model_dir / "gradient_boosting.joblib")
        with open(model_dir / "baseline_config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)
            self.include_untrusted_flag = cfg.get("include_untrusted_flag", True)
            self.feature_names = cfg.get("feature_names", [])
        self.is_fitted = True
