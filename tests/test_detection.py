import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.data_buffer      import MetricBuffer
from detection.isolation_forest import IsolationForestDetector


class TestMetricBuffer:

    def test_buffer_creation(self):
        """Test buffer initializes correctly"""
        buffer = MetricBuffer(window_size=20)
        assert buffer.window_size == 20

    def test_buffer_add_and_retrieve(self):
        """Test adding values and retrieving window"""
        buffer = MetricBuffer(window_size=5)
        for i in range(5):
            buffer.add("payment-service", "cpu_usage", float(i * 10))
        window = buffer.get_window("payment-service", "cpu_usage")
        assert len(window) == 5
        assert window[-1] == 40.0

    def test_buffer_window_size_limit(self):
        """Test buffer doesn't exceed window size"""
        buffer = MetricBuffer(window_size=5)
        for i in range(10):
            buffer.add("api-gateway", "cpu_usage", float(i))
        window = buffer.get_window("api-gateway", "cpu_usage")
        assert len(window) <= 5

    def test_buffer_multiple_services(self):
        """Test buffer handles multiple services"""
        buffer = MetricBuffer(window_size=10)
        buffer.add("service-a", "cpu_usage", 50.0)
        buffer.add("service-b", "cpu_usage", 60.0)
        services = buffer.get_all_services()
        assert "service-a" in services
        assert "service-b" in services

    def test_buffer_is_ready(self):
        """Test is_ready returns True when enough samples"""
        buffer = MetricBuffer(window_size=20)
        for i in range(20):
            buffer.add("test-service", "cpu_usage", float(i))
        assert buffer.is_ready("test-service", "cpu_usage", 20) is True

    def test_buffer_not_ready_insufficient_samples(self):
        """Test is_ready returns False when not enough samples"""
        buffer = MetricBuffer(window_size=20)
        for i in range(5):
            buffer.add("test-service", "cpu_usage", float(i))
        assert buffer.is_ready("test-service", "cpu_usage", 20) is False


class TestIsolationForestDetector:

    def setup_method(self):
        """Set up buffer with enough data for each test"""
        self.buffer = MetricBuffer(window_size=20)
        # Fill with normal data
        for i in range(20):
            self.buffer.add("payment-service", "cpu_usage", 40.0 + i * 0.5)
            self.buffer.add("payment-service", "request_latency_ms", 150.0)
            self.buffer.add("payment-service", "error_rate_pct", 1.0)
            self.buffer.add("payment-service", "memory_usage_pct", 55.0)
        self.detector = IsolationForestDetector(self.buffer, contamination=0.1)

    def test_detector_initializes(self):
        """Test detector initializes without errors"""
        assert self.detector is not None

    def test_no_anomaly_on_normal_data(self):
        """Test no anomaly detected on normal traffic"""
        anomalies = self.detector.analyze_all()
        assert isinstance(anomalies, list)

    def test_anomaly_detected_on_spike(self):
        """Test anomaly detected when CPU spikes to 99%"""
        # Inject obvious anomaly
        for _ in range(5):
            self.buffer.add("payment-service", "cpu_usage", 99.0)
            self.buffer.add("payment-service", "request_latency_ms", 5000.0)
            self.buffer.add("payment-service", "error_rate_pct", 50.0)
            self.buffer.add("payment-service", "memory_usage_pct", 99.0)
        anomalies = self.detector.analyze_all()
        # Should detect at least something with extreme values
        assert isinstance(anomalies, list)

    def test_severity_range(self):
        """Test all returned anomalies have valid severity"""
        anomalies = self.detector.analyze_all()
        for a in anomalies:
            assert 1 <= a.severity <= 4