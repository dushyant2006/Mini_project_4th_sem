# ============================================================
# detection/detection_engine.py
# PURPOSE: Main detection loop — reads metrics from Kafka,
#          feeds them to ML models, publishes anomalies
#
# HOW TO RUN:
#   python detection/detection_engine.py
# ============================================================

import json
import sys
import os
import time
from kafka import KafkaConsumer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from detection.data_buffer        import MetricBuffer
from detection.isolation_forest   import IsolationForestDetector
from detection.lstm_autoencoder   import LSTMDetector
from detection.anomaly_publisher  import AnomalyPublisher

TOPIC_METRICS   = "telemetry.metrics"
TOPIC_ANOMALIES = "anomalies.detected"

# Run ML analysis every N metric messages received
ANALYZE_EVERY = 10


def run_detection_engine():
    print("=" * 60)
    print("  PROJECT 71 — ANOMALY DETECTION ENGINE")
    print("=" * 60)
    print("  Models: Isolation Forest + LSTM Autoencoder")
    print("  Input:  telemetry.metrics (Kafka)")
    print("  Output: anomalies.detected (Kafka)")
    print("=" * 60)

    # ── Initialize components ──────────────────────────────
    buffer    = MetricBuffer(window_size=20)
    iso_det   = IsolationForestDetector(buffer, contamination=0.1)
    lstm_det  = LSTMDetector(buffer, seq_len=20)
    publisher = AnomalyPublisher()

    # ── Kafka Consumer (reads metrics) ─────────────────────
    consumer = KafkaConsumer(
        TOPIC_METRICS,
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="detection-engine",
        enable_auto_commit=True,
        api_version=(2, 0, 0),
    )

    print("\n✅ Detection engine running... Press Ctrl+C to stop\n")
    print("-" * 60)

    msg_count    = 0
    anomaly_count = 0

    try:
        while True:
            records = consumer.poll(timeout_ms=1000)

            if not records:
                continue

            for tp, messages in records.items():
                for msg in messages:
                    data = msg.value

                    service     = data.get("service", "")
                    metric_name = data.get("metric_name", "")
                    value       = data.get("value", 0.0)
                    timestamp   = data.get("timestamp")

                    # Add to buffer
                    buffer.add(service, metric_name, value)
                    msg_count += 1

                    # Print progress every 35 messages (one full batch)
                    if msg_count % 35 == 0:
                        print(f"📥 Buffered {msg_count} metrics across "
                              f"{len(buffer.get_all_services())} services")

                    # Run ML analysis every ANALYZE_EVERY messages
                    if msg_count % ANALYZE_EVERY == 0:

                        # Run Isolation Forest
                        iso_anomalies = iso_det.analyze_all()

                        # Run LSTM
                        lstm_anomalies = lstm_det.analyze_all()

                        # Combine results
                        all_anomalies = iso_anomalies + lstm_anomalies

                        if all_anomalies:
                            anomaly_count += len(all_anomalies)
                            publisher.publish_batch(all_anomalies)
                            print(f"\n{'='*60}")
                            print(f"🚨 {len(all_anomalies)} ANOMALIES DETECTED "
                                  f"(total: {anomaly_count})")
                            print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print(f"\n⛔ Detection engine stopped.")
        print(f"   Total metrics processed : {msg_count}")
        print(f"   Total anomalies detected: {anomaly_count}")
    finally:
        consumer.close()
        publisher.close()


if __name__ == "__main__":
    run_detection_engine()
