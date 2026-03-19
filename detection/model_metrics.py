# ============================================================
# detection/model_metrics.py
# PURPOSE: Track ML model performance metrics per the report
#          Tracks Precision, Recall, F1-Score for each model
# ============================================================

import json
import os
from datetime import datetime, timezone
from typing import Dict

METRICS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "model_metrics.json"
)


class ModelMetricsTracker:
    """
    Tracks detection performance for all 3 ML models.

    Metrics:
      Precision = TP / (TP + FP)
      Recall    = TP / (TP + FN)
      F1-Score  = 2 * P * R / (P + R)
    """

    MODELS = ["isolation_forest", "lstm_autoencoder", "prophet"]

    def __init__(self):
        os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
        self.metrics = self._load()
        print(f"✅ Model Metrics Tracker initialized "
              f"({len(self.metrics)} models tracked)")

    def _default(self) -> Dict:
        return {
            model: {
                "true_positives":   0,
                "false_positives":  0,
                "false_negatives":  0,
                "total_detections": 0,
                "precision":        0.0,
                "recall":           0.0,
                "f1_score":         0.0,
                "last_updated":     datetime.now(timezone.utc).isoformat()
            }
            for model in self.MODELS
        }

    def _load(self) -> Dict:
        if not os.path.exists(METRICS_FILE):
            default = self._default()
            self._save(default)
            return default
        try:
            with open(METRICS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return self._default()

    def _save(self, data: Dict):
        with open(METRICS_FILE, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _recalculate(self, model: str):
        m  = self.metrics[model]
        tp = m["true_positives"]
        fp = m["false_positives"]
        fn = m["false_negatives"]

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1        = (2 * precision * recall / (precision + recall)
                     if (precision + recall) > 0 else 0.0)

        self.metrics[model].update({
            "precision":    round(precision, 4),
            "recall":       round(recall, 4),
            "f1_score":     round(f1, 4),
            "last_updated": datetime.now(timezone.utc).isoformat()
        })

    def record_detection(self, model: str, is_true_positive: bool = True):
        """Call this every time a model makes a detection."""
        if model not in self.metrics:
            return
        self.metrics[model]["total_detections"] += 1
        if is_true_positive:
            self.metrics[model]["true_positives"] += 1
        else:
            self.metrics[model]["false_positives"] += 1
        self._recalculate(model)
        self._save(self.metrics)

    def record_miss(self, model: str):
        """Call when a known anomaly was not detected."""
        if model not in self.metrics:
            return
        self.metrics[model]["false_negatives"] += 1
        self._recalculate(model)
        self._save(self.metrics)

    def get_summary(self) -> Dict:
        return {
            "models": self.metrics,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "interpretation": {
                "precision": "Of all detections, what % were real anomalies",
                "recall":    "Of all real anomalies, what % were detected",
                "f1_score":  "Balanced score — higher is better (max 1.0)",
            }
        }


