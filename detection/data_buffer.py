# ============================================================
# detection/data_buffer.py
# PURPOSE: Collects incoming metrics into sliding windows
#          so ML models can analyze trends over time
#
# Example:
#   payment-service CPU readings over last 20 samples:
#   [45, 46, 44, 47, 45, 89, 94, 96, 95, 97] ← spike detected!
# ============================================================

from collections import deque, defaultdict
from typing import Dict, List, Optional
from datetime import datetime
import threading


# How many data points to keep per service per metric
# 20 samples × 5 seconds = last 100 seconds of data
WINDOW_SIZE = 20


class MetricBuffer:
    """
    Stores the last WINDOW_SIZE readings for every
    (service, metric_name) combination.

    Structure:
        buffer["payment-service"]["cpu_usage"] = deque([45.2, 46.1, 94.7...])
        buffer["api-gateway"]["request_latency_ms"] = deque([52, 48, 55...])
    """

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size

        # defaultdict automatically creates empty deques for new keys
        # So we never get KeyError when accessing a new service/metric
        self.buffer: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=window_size))
        )

        # Track timestamps for each reading
        self.timestamps: Dict[str, Dict[str, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=window_size))
        )

        # Thread lock — prevents data corruption when
        # multiple threads read/write simultaneously
        self.lock = threading.Lock()

    def add(self, service: str, metric_name: str,
            value: float, timestamp: datetime = None):
        """
        Adds one metric reading to the buffer.

        deque with maxlen automatically removes oldest item
        when full — this is our sliding window!
        """
        with self.lock:
            self.buffer[service][metric_name].append(value)
            self.timestamps[service][metric_name].append(
                timestamp or datetime.utcnow()
            )

    def get_window(self, service: str,
                   metric_name: str) -> List[float]:
        """
        Returns the current window of values for a
        service+metric combination as a plain list.

        Returns empty list if not enough data yet.
        """
        with self.lock:
            values = list(self.buffer[service][metric_name])
            return values

    def is_ready(self, service: str,
                 metric_name: str,
                 min_samples: int = 10) -> bool:
        """
        Returns True only when we have enough data points
        to make a meaningful ML prediction.

        We wait for at least min_samples before running ML
        to avoid false alarms at startup.
        """
        with self.lock:
            return len(self.buffer[service][metric_name]) >= min_samples

    def get_latest(self, service: str,
                   metric_name: str) -> Optional[float]:
        """Returns the most recent value for a metric"""
        with self.lock:
            buf = self.buffer[service][metric_name]
            return buf[-1] if buf else None

    def get_all_services(self) -> List[str]:
        """Returns list of all services seen so far"""
        with self.lock:
            return list(self.buffer.keys())

    def get_stats(self, service: str,
                  metric_name: str) -> Dict:
        """
        Returns basic statistics for a metric window.
        Used by anomaly detectors to compare current
        value against historical baseline.
        """
        import statistics
        with self.lock:
            values = list(self.buffer[service][metric_name])
            if len(values) < 2:
                return {}
            return {
                "mean":   statistics.mean(values),
                "stdev":  statistics.stdev(values),
                "min":    min(values),
                "max":    max(values),
                "count":  len(values),
                "latest": values[-1]
            }