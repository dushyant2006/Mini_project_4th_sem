
import json
import sys
import os
import time
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import AnomalyEvent
from rca.agent.rca_agent import RCAAgent

TOPIC_ANOMALIES = "anomalies.detected"
TOPIC_RCA       = "rca.results"

# Collect anomalies for this many seconds before analyzing
# Gives time for cascade anomalies to arrive too
COLLECTION_WINDOW_SECONDS = 30


def run_rca_engine():
    print("=" * 60)
    print("  PROJECT 71 — RCA ENGINE")
    print("=" * 60)
    print(f"  Input : {TOPIC_ANOMALIES}")
    print(f"  Output: {TOPIC_RCA}")
    print(f"  Window: {COLLECTION_WINDOW_SECONDS}s collection window")
    print("=" * 60)

    # Initialize RCA Agent
    agent = RCAAgent()

    # Kafka consumer — reads anomalies
    consumer = KafkaConsumer(
        TOPIC_ANOMALIES,
        bootstrap_servers="localhost:9092",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="rca-engine",
        enable_auto_commit=True,
        api_version=(2, 0, 0),
    )

    # Kafka producer — publishes RCA results
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(
            v, default=str
        ).encode("utf-8"),
        api_version=(2, 0, 0),
    )

    print("\n✅ RCA Engine running... Press Ctrl+C to stop\n")
    print("-" * 60)

    # Buffer to collect anomalies before analyzing
    anomaly_buffer = []
    last_analysis_time = time.time()

    try:
        while True:
            records = consumer.poll(timeout_ms=1000)

            # Collect incoming anomalies
            for tp, messages in records.items():
                for msg in messages:
                    data = msg.value
                    try:
                        anomaly = AnomalyEvent(**data)
                        anomaly_buffer.append(anomaly)
                        print(f"📨 Received anomaly: "
                              f"{anomaly.service} | "
                              f"{anomaly.anomaly_type} | "
                              f"severity={anomaly.severity}")
                    except Exception as e:
                        print(f"⚠️ Failed to parse anomaly: {e}")

            # Analyze when window expires AND we have anomalies
            elapsed = time.time() - last_analysis_time
            if elapsed >= COLLECTION_WINDOW_SECONDS and anomaly_buffer:

                print(f"\n🔬 Analyzing {len(anomaly_buffer)} "
                      f"collected anomalies...")

                # Run RCA
                report = agent.analyze(anomaly_buffer)

                # Print full report
                _print_report(report)

                # Publish to Kafka
                producer.send(TOPIC_RCA, value=report)
                producer.flush()
                print(f"\n📤 RCA report published to {TOPIC_RCA}")

                # Clear buffer for next window
                anomaly_buffer = []
                last_analysis_time = time.time()

            elif not anomaly_buffer and elapsed > 10:
                print(f"⏳ Waiting for anomalies... "
                      f"({int(elapsed)}s since last analysis)")
                last_analysis_time = time.time()

    except KeyboardInterrupt:
        print("\n⛔ RCA Engine stopped.")
    finally:
        consumer.close()
        producer.close()


def _print_report(report: dict):
    """Prints a formatted RCA report to terminal"""
    if report.get("status") == "no_anomalies":
        return

    print("\n" + "🚨" * 30)
    print(f"  INCIDENT REPORT — SEV-{report.get('severity', '?')}")
    print("🚨" * 30)
    print(f"  ID        : {report.get('incident_id')}")
    print(f"  Time      : {report.get('timestamp')}")
    print(f"  Service   : {report.get('root_cause_service')}")
    print(f"  Team      : {report.get('owning_team')}")
    print(f"\n  ROOT CAUSE:")
    print(f"  {report.get('root_cause_summary')}")
    print(f"\n  BLAST RADIUS:")
    br = report.get("blast_radius", {})
    print(f"  Directly affected  : {br.get('directly_affected', [])}")
    print(f"  Indirectly affected: {br.get('indirectly_affected', [])}")
    print(f"\n  TOP HYPOTHESES:")
    for i, h in enumerate(report.get("hypotheses", []), 1):
        print(f"  {i}. {h}")
    print(f"\n  RECOMMENDED FIXES:")
    for i, f in enumerate(report.get("recommended_fixes", []), 1):
        print(f"  {i}. {f}")
    print(f"\n  SIMILAR PAST INCIDENTS: "
          f"{report.get('similar_incidents', [])}")
    print("=" * 60)


if __name__ == "__main__":
    run_rca_engine()