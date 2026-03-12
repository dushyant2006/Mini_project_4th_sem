
import numpy as np
import torch
import torch.nn as nn
from typing import List, Optional, Dict
from datetime import datetime, timezone
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import AnomalyEvent
from detection.data_buffer import MetricBuffer


# LSTM Autoencoder Architecture 

class LSTMEncoder(nn.Module):
    """
    Encodes a sequence of metric values into a compressed
    hidden representation (latent space).
    """
    def __init__(self, input_size: int, hidden_size: int,
                 num_layers: int):
        super().__init__()
        # LSTM processes sequences step by step
        # input_size  = 1 (one metric value per timestep)
        # hidden_size = size of internal memory
        # num_layers  = depth of the network
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,   # input shape: (batch, seq_len, features)
            dropout=0.2 if num_layers > 1 else 0
        )

    def forward(self, x):
        # outputs shape: (batch, seq_len, hidden_size)
        # hidden shape:  (num_layers, batch, hidden_size)
        outputs, (hidden, cell) = self.lstm(x)
        # Return last hidden state as the encoded representation
        return hidden[-1]   # shape: (batch, hidden_size)


class LSTMDecoder(nn.Module):
    """
    Decodes the compressed representation back into
    a sequence of metric values.
    """
    def __init__(self, hidden_size: int, output_size: int,
                 seq_len: int, num_layers: int):
        super().__init__()
        self.seq_len = seq_len
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
        )
        # Linear layer maps hidden states to actual values
        self.output_layer = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # Repeat the encoded vector seq_len times as input
        # shape: (batch, seq_len, hidden_size)
        x = x.unsqueeze(1).repeat(1, self.seq_len, 1)
        outputs, _ = self.lstm(x)
        # Map to output values
        return self.output_layer(outputs)


class LSTMAutoencoder(nn.Module):
    """
    Complete Autoencoder = Encoder + Decoder

    Input sequence  → Encoder → compressed vector → Decoder → reconstructed sequence
    Compare input vs reconstructed → reconstruction error
    High error = anomaly!
    """
    def __init__(self, seq_len: int = 20, hidden_size: int = 32,
                 num_layers: int = 1):
        super().__init__()
        self.seq_len = seq_len
        self.encoder = LSTMEncoder(1, hidden_size, num_layers)
        self.decoder = LSTMDecoder(hidden_size, 1, seq_len, num_layers)

    def forward(self, x):
        encoded   = self.encoder(x)
        decoded   = self.decoder(encoded)
        return decoded


# ── Detector Class ────────────────────────────────────────────

class LSTMDetector:
    """
    Manages LSTM Autoencoders for multiple service+metric combos.

    One model per service per metric — each learns
    the normal pattern of that specific metric.
    """

    def __init__(self, buffer: MetricBuffer,
                 seq_len: int = 20,
                 hidden_size: int = 32,
                 threshold_multiplier: float = 2.5):
        """
        Parameters:
            buffer               : shared MetricBuffer
            seq_len              : sequence length (must match WINDOW_SIZE)
            hidden_size          : LSTM memory size
            threshold_multiplier : how many std devs above mean = anomaly
                                  Lower = more sensitive
        """
        self.buffer               = buffer
        self.seq_len              = seq_len
        self.hidden_size          = hidden_size
        self.threshold_multiplier = threshold_multiplier

        # One model per service+metric
        self.models:     Dict[str, LSTMAutoencoder] = {}
        # Store reconstruction error history for thresholding
        self.error_history: Dict[str, List[float]]  = {}

        # Use CPU (no GPU needed for this project size)
        self.device = torch.device("cpu")

        print("✅ LSTM Autoencoder Detector initialized")

    def _key(self, service: str, metric: str) -> str:
        return f"{service}::{metric}"

    def _get_or_create_model(self, key: str) -> LSTMAutoencoder:
        """Gets existing model or creates a new one"""
        if key not in self.models:
            self.models[key] = LSTMAutoencoder(
                seq_len=self.seq_len,
                hidden_size=self.hidden_size
            ).to(self.device)
            self.error_history[key] = []
        return self.models[key]

    def _normalize(self, values: List[float]):
        """Normalize to 0-1 range for better training"""
        arr = np.array(values, dtype=np.float32)
        mn, mx = arr.min(), arr.max()
        if mx - mn < 1e-8:
            return arr, mn, mx
        return (arr - mn) / (mx - mn), mn, mx

    def train_step(self, service: str, metric: str,
                   values: List[float]):
        """
        Performs one training step on the current window.
        We train continuously on live data — the model
        constantly adapts to what "normal" looks like.
        """
        if len(values) < self.seq_len:
            return

        key   = self._key(service, metric)
        model = self._get_or_create_model(key)
        model.train()

        # Normalize values
        norm_values, _, _ = self._normalize(values)

        # Convert to PyTorch tensor
        # Shape: (1, seq_len, 1) = (batch=1, sequence, features=1)
        x = torch.FloatTensor(norm_values).unsqueeze(0).unsqueeze(-1)

        # Simple SGD optimizer
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        # One forward + backward pass
        optimizer.zero_grad()
        reconstructed = model(x)
        loss = criterion(reconstructed, x)
        loss.backward()
        optimizer.step()

    def get_reconstruction_error(self, service: str,
                                  metric: str,
                                  values: List[float]) -> float:
        """
        Returns reconstruction error for current sequence.
        Higher error = more anomalous.
        """
        if len(values) < self.seq_len:
            return 0.0

        key   = self._key(service, metric)
        model = self._get_or_create_model(key)
        model.eval()

        norm_values, _, _ = self._normalize(values)
        x = torch.FloatTensor(norm_values).unsqueeze(0).unsqueeze(-1)

        with torch.no_grad():
            reconstructed = model(x)
            error = nn.MSELoss()(reconstructed, x).item()

        # Store error in history for dynamic thresholding
        self.error_history[key].append(error)
        # Keep only last 50 errors
        if len(self.error_history[key]) > 50:
            self.error_history[key].pop(0)

        return error

    def is_anomalous(self, service: str,
                     metric: str,
                     values: List[float]) -> tuple:
        """
        Returns (is_anomaly: bool, error: float, threshold: float)

        Threshold is dynamic — based on historical error distribution.
        This prevents false alarms as the system adapts.
        """
        error = self.get_reconstruction_error(service, metric, values)
        key   = self._key(service, metric)
        history = self.error_history.get(key, [])

        # Need at least 10 errors to compute a reliable threshold
        if len(history) < 10:
            return False, error, float('inf')

        import statistics
        mean_err  = statistics.mean(history)
        std_err   = statistics.stdev(history) if len(history) > 1 else 0
        threshold = mean_err + self.threshold_multiplier * std_err

        return error > threshold, error, threshold

    def analyze_metric(self, service: str,
                       metric: str) -> Optional[AnomalyEvent]:
        """
        Trains on current window then checks for anomaly.
        Returns AnomalyEvent if anomalous, None otherwise.
        """
        if not self.buffer.is_ready(service, metric, min_samples=15):
            return None

        values = self.buffer.get_window(service, metric)

        # Train on all but last point
        self.train_step(service, metric, values[:-1])

        # Check if latest sequence is anomalous
        is_anom, error, threshold = self.is_anomalous(
            service, metric, values
        )

        if not is_anom:
            return None

        stats    = self.buffer.get_stats(service, metric)
        expected = stats.get("mean", 0)
        latest   = values[-1]

        print(f"🧠 LSTM ANOMALY | {service} | {metric} | "
              f"error={error:.4f} threshold={threshold:.4f}")

        return AnomalyEvent(
            timestamp=datetime.now(timezone.utc),
            service=service,
            anomaly_type=f"lstm_{metric}_pattern_anomaly",
            severity=3,
            metric_name=metric,
            observed_value=round(latest, 2),
            expected_value=round(expected, 2),
            description=(
                f"LSTM detected abnormal {metric} pattern on {service}. "
                f"Reconstruction error {error:.4f} exceeds "
                f"threshold {threshold:.4f}"
            ),
        )

    def analyze_all(self) -> List[AnomalyEvent]:
        """Runs LSTM check on all services × metrics"""
        anomalies = []
        metrics   = ["cpu_usage", "request_latency_ms", "error_rate_pct"]

        for service in self.buffer.get_all_services():
            for metric in metrics:
                result = self.analyze_metric(service, metric)
                if result:
                    anomalies.append(result)

        return anomalies