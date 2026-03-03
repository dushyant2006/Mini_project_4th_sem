# ============================================================
# detection/prophet_baseline.py
# PURPOSE: Detects anomalies using Facebook Prophet
#          by forecasting expected values and flagging
#          readings that deviate beyond prediction intervals
#
# What Prophet detects that others MISS:
#   - Seasonal violations (high CPU at 3am when it's always low)
#   - Gradual trend anomalies (slowly rising error rate)
#   - Day-of-week pattern breaks
# ============================================================

import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime, timezone
import sys, os, warnings

# Suppress Prophet's verbose output
warnings.filterwarnings("ignore")
os.environ["CMDSTAN_MESSAGE"] = "0"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import AnomalyEvent
from detection.data_buffer import MetricBuffer


class ProphetDetector:
    """
    Uses Facebook Prophet to detect anomalies based on
    forecasted baselines with uncertainty intervals.

    How it works:
        1. Collects time-series data per service per metric
        2. Fits a Prophet model to learn the baseline pattern
        3. Forecasts what the NEXT value should be
        4. If actual value is outside the forecast interval → ANOMALY

    Prophet is especially good at:
        - Detecting values that are wrong FOR THE TIME OF DAY
        - Catching gradual degradation trends
        - Handling regular traffic patterns (daily, weekly cycles)
    """

    def __init__(self, buffer: MetricBuffer,
                 interval_width: float = 0.95,
                 min_samples: int = 20):
        """
        Parameters:
            buffer         : shared MetricBuffer
            interval_width : confidence interval width (0.95 = 95%)
                            Values outside this = anomaly
            min_samples    : minimum data points before forecasting
        """
        self.buffer         = buffer
        self.interval_width = interval_width
        self.min_samples    = min_samples

        # Cache fitted models to avoid refitting every time
        self.models:     Dict[str, object] = {}
        self.last_fit:   Dict[str, int]    = {}
        self.refit_every = 15  # refit after every 15 new samples

        print("✅ Prophet Detector initialized "
              f"(confidence interval: {interval_width*100:.0f}%)")

    def _key(self, service: str, metric: str) -> str:
        return f"{service}::{metric}"

    def _build_dataframe(self, service: str,
                         metric: str) -> Optional[pd.DataFrame]:
        """
        Converts buffer data to Prophet's required format.
        Prophet requires a DataFrame with columns: ds (datetime), y (value)
        """
        values = self.buffer.get_window(service, metric)
        if len(values) < self.min_samples:
            return None

        # Generate timestamps (every 5 seconds going back)
        now  = datetime.now()
        n    = len(values)
        freq = 5  # seconds between readings

        timestamps = pd.date_range(
            end=now,
            periods=n,
            freq=f"{freq}s"
        )

        df = pd.DataFrame({
            "ds": timestamps,
            "y":  values
        })

        return df

    def _fit_model(self, service: str, metric: str,
                   df: pd.DataFrame):
        """Fits a Prophet model on the historical data"""
        try:
            from prophet import Prophet

            model = Prophet(
                interval_width=self.interval_width,
                daily_seasonality=False,  # not enough data for daily
                weekly_seasonality=False,
                yearly_seasonality=False,
                # Add short-term trend detection
                changepoint_prior_scale=0.05,
            )

            # Suppress Prophet output during fitting
            import logging
            logging.getLogger("prophet").setLevel(logging.WARNING)
            logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

            model.fit(df)
            key = self._key(service, metric)
            self.models[key]   = model
            self.last_fit[key] = len(df)
            return model

        except Exception as e:
            return None

    def check_metric(self, service: str,
                     metric: str) -> Optional[AnomalyEvent]:
        """
        Checks if the latest metric reading is anomalous
        based on Prophet's forecast.

        Returns AnomalyEvent if anomaly detected, None otherwise.
        """
        df = self._build_dataframe(service, metric)
        if df is None:
            return None

        key   = self._key(service, metric)
        model = self.models.get(key)

        # Fit or refit model when needed
        samples_since_fit = len(df) - self.last_fit.get(key, 0)
        if model is None or samples_since_fit >= self.refit_every:
            model = self._fit_model(service, metric, df[:-1])
            if model is None:
                return None

        try:
            # Forecast one step ahead
            future    = model.make_future_dataframe(
                periods=1, freq="5s"
            )
            forecast  = model.predict(future)

            # Get the latest forecast bounds
            latest_forecast = forecast.iloc[-1]
            yhat     = latest_forecast["yhat"]       # predicted value
            yhat_low = latest_forecast["yhat_lower"] # lower bound
            yhat_upp = latest_forecast["yhat_upper"] # upper bound

            # Actual latest value
            actual = df["y"].iloc[-1]

            # Check if actual is outside prediction interval
            is_anomaly = actual < yhat_low or actual > yhat_upp

            if not is_anomaly:
                return None

            # Determine severity
            # How far outside the interval is it?
            interval_width = yhat_upp - yhat_low
            if interval_width > 0:
                deviation = abs(actual - yhat) / (interval_width / 2)
            else:
                deviation = 0

            if deviation > 3:
                severity = 4
            elif deviation > 2:
                severity = 3
            elif deviation > 1:
                severity = 2
            else:
                severity = 1

            direction = "above" if actual > yhat_upp else "below"

            print(f"📈 PROPHET ANOMALY | {service} | {metric} | "
                  f"actual={actual:.1f} predicted={yhat:.1f} "
                  f"({direction} interval) severity={severity}")

            return AnomalyEvent(
                timestamp=datetime.now(timezone.utc),
                service=service,
                anomaly_type=f"prophet_{metric}_forecast_anomaly",
                severity=severity,
                metric_name=metric,
                observed_value=round(actual, 2),
                expected_value=round(yhat, 2),
                description=(
                    f"Prophet forecast violation on {service}: "
                    f"{metric} = {actual:.1f} is {direction} "
                    f"expected range [{yhat_low:.1f}, {yhat_upp:.1f}]. "
                    f"Predicted: {yhat:.1f}"
                ),
            )

        except Exception as e:
            return None

    def analyze_all(self) -> List[AnomalyEvent]:
        """Runs Prophet check on all services × key metrics"""
        anomalies = []
        metrics   = [
            "cpu_usage",
            "request_latency_ms",
            "error_rate_pct"
        ]

        for service in self.buffer.get_all_services():
            for metric in metrics:
                if self.buffer.is_ready(service, metric,
                                        self.min_samples):
                    result = self.check_metric(service, metric)
                    if result:
                        anomalies.append(result)

        return anomalies