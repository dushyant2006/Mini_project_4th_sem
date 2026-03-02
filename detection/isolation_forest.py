# ============================================================
# detection/isolation_forest.py
# PURPOSE: Detects anomalies in metric snapshots using
#          Isolation Forest algorithm
#
# How it works:
#   1. Collect last 20 readings per service per metric
#   2. Build an Isolation Forest model on that window
#   3. Ask: "Is the latest reading an anomaly?"
#   4. If yes → create AnomalyEvent
# ============================================================

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Optional, Dict
from datetime import datetime, timezone
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import MetricEvent, AnomalyEvent
from detection.data_buffer import MetricBuffer


# Which metrics to monitor for anomalies
MONITORED_METRICS = [
    "cpu_usage",
    "request_latency_ms",
    "error_rate_pct",
    "memory_usage_pct",
]

# Anomaly thresholds per metric
# If value exceeds these → definitely anomalous
HARD_THRESHOLDS = {
    "cpu_usage":          85.0,   # CPU above 85% = anomaly
    "request_latency_ms": 1000.0, # Latency above 1s = anomaly
    "error_rate_pct":     10.0,   # Error rate above 10% = anomaly
    "memory_usage_pct":   90.0,   # Memory above 90% = anomaly
}


class IsolationForestDetector:
    """
    Runs Isolation Forest on metric windows to detect anomalies.

    For each service × metric combination, it:
    1. Waits for 10+ data points (warmup period)
    2. Fits Isolation Forest on the window
    3. Checks if latest point is an outlier
    4. Also checks hard thresholds as backup
    """

    def __init__(self, buffer: MetricBuffer, contamination: float = 0.1):
        """
        Parameters:
            buffer       : shared MetricBuffer from data_buffer.py
            contamination: expected fraction of anomalies (0.1 = 10%)
                          Lower = less sensitive, Higher = more sensitive
        """
        self.buffer        = buffer
        self.contamination = contamination

        # Store fitted models per service+metric
        # So we don't refit from scratch every time
        self.models: Dict[str, IsolationForest] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        print("✅ Isolation Forest Detector initialized")

    def _model_key(self, service: str, metric: str) -> str:
        """Creates a unique key for storing models"""
        return f"{service}::{metric}"

    def _fit_model(self, service: str, metric: str,
                   values: List[float]) -> IsolationForest:
        """
        Fits (trains) an Isolation Forest on the current window.

        We refit every time to adapt to changing baselines.
        e.g. CPU naturally rises during peak hours — 
        the model should adapt so it doesn't false-alarm.
        """
        key = self._model_key(service, metric)

        # Reshape for sklearn: needs 2D array [[v1], [v2], ...]
        X = np.array(values).reshape(-1, 1)

        # Scale the data (important for ML algorithms)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Fit Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,      # makes results reproducible
            n_estimators=50,      # number of trees (fast but accurate)
        )
        model.fit(X_scaled)

        # Store for reuse
        self.models[key]  = model
        self.scalers[key] = scaler

        return model

    def check_metric(self, service: str,
                     metric: str) -> Optional[AnomalyEvent]:
        """
        Checks if the latest metric reading is anomalous.

        Returns an AnomalyEvent if anomaly detected, None otherwise.
        """

        # Not enough data yet — skip
        if not self.buffer.is_ready(service, metric, min_samples=10):
            return None

        values = self.buffer.get_window(service, metric)
        if len(values) < 2:
            return None

        latest  = values[-1]
        key     = self._model_key(service, metric)

        # --- METHOD 1: Hard Threshold Check ---
        # Simple but effective first line of defense
        threshold = HARD_THRESHOLDS.get(metric)
        threshold_triggered = threshold and latest > threshold

        # --- METHOD 2: Isolation Forest ---
        # Refit model on current window
        model  = self._fit_model(service, metric, values[:-1])
        scaler = self.scalers[key]

        # Check if latest point is anomalous
        X_latest = scaler.transform([[latest]])
        # predict returns 1 (normal) or -1 (anomaly)
        prediction = model.predict(X_latest)[0]
        if_anomaly = (prediction == -1)

        # --- COMBINE BOTH METHODS ---
        is_anomaly = threshold_triggered or if_anomaly

        if not is_anomaly:
            return None

        # --- BUILD ANOMALY EVENT ---
        stats = self.buffer.get_stats(service, metric)
        expected = stats.get("mean", 0)

        # Determine severity based on how far above normal
        ratio = latest / expected if expected > 0 else 1
        if ratio > 3 or threshold_triggered:
            severity = 4      # CRITICAL
        elif ratio > 2:
            severity = 3      # HIGH
        elif ratio > 1.5:
            severity = 2      # MEDIUM
        else:
            severity = 1      # LOW

        description = (
            f"{metric} = {latest:.1f} "
            f"(expected ~{expected:.1f}, "
            f"threshold = {threshold}) "
            f"on {service}"
        )

        print(f"🚨 ANOMALY DETECTED | {service} | {metric} | "
              f"value={latest:.1f} expected={expected:.1f} "
              f"severity={severity}")

        return AnomalyEvent(
            timestamp=datetime.now(timezone.utc),
            service=service,
            anomaly_type=f"{metric}_anomaly",
            severity=severity,
            metric_name=metric,
            observed_value=latest,
            expected_value=round(expected, 2),
            description=description,
        )

    def analyze_all(self) -> List[AnomalyEvent]:
        """
        Runs anomaly check on ALL services × ALL metrics.
        Call this every time a new batch of metrics arrives.

        Returns list of AnomalyEvents (empty if all normal).
        """
        anomalies = []

        for service in self.buffer.get_all_services():
            for metric in MONITORED_METRICS:
                result = self.check_metric(service, metric)
                if result:
                    anomalies.append(result)

        return anomalies