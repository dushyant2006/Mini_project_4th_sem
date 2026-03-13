import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.models import MetricEvent, LogEvent, AnomalyEvent
from datetime import datetime, timezone


class TestMetricEvent:

    def test_metric_event_creation(self):
        """Test basic MetricEvent creation"""
        event = MetricEvent(
            timestamp=datetime.now(timezone.utc),
            service="payment-service",
            metric_name="cpu_usage",
            value=85.5,
            unit="percent"
        )
        assert event.service == "payment-service"
        assert event.metric_name == "cpu_usage"
        assert event.value == 85.5

    def test_metric_event_dict(self):
        """Test MetricEvent converts to dict via model_dump"""
        event = MetricEvent(
            timestamp=datetime.now(timezone.utc),
            service="api-gateway",
            metric_name="request_latency_ms",
            value=120.0,
            unit="ms"
        )
        d = event.model_dump()
        assert d["service"] == "api-gateway"
        assert d["metric_name"] == "request_latency_ms"
        assert "timestamp" in d

    def test_anomaly_event_severity_range(self):
        """Test AnomalyEvent severity is between 1-4"""
        event = AnomalyEvent(
            timestamp=datetime.now(timezone.utc),
            service="order-service",
            anomaly_type="cpu_usage_anomaly",
            severity=2,
            metric_name="cpu_usage",
            observed_value=95.0,
            expected_value=40.0,
            description="CPU spike detected"
        )
        assert 1 <= event.severity <= 4

    def test_anomaly_event_observed_above_expected(self):
        """Test anomaly where observed > expected"""
        event = AnomalyEvent(
            timestamp=datetime.now(timezone.utc),
            service="payment-service",
            anomaly_type="latency_anomaly",
            severity=3,
            metric_name="request_latency_ms",
            observed_value=2500.0,
            expected_value=200.0,
            description="Latency spike"
        )
        assert event.observed_value > event.expected_value

    def test_log_event_creation(self):
        """Test LogEvent creation"""
        event = LogEvent(
            timestamp=datetime.now(timezone.utc),
            service="auth-service",
            level="ERROR",
            message="Connection timeout",
            trace_id="abc123"
        )
        assert event.level == "ERROR"
        assert event.service == "auth-service"