# ============================================================
# detection/anomaly_publisher.py
# PURPOSE: Publishes detected anomalies to Kafka
#          so the RCA Agent can pick them up
# ============================================================

import json
from kafka import KafkaProducer
from datetime import datetime
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import AnomalyEvent

TOPIC_ANOMALIES = "anomalies.detected"


class AnomalyPublisher:
    """
    Sends AnomalyEvent objects to the anomalies.detected Kafka topic.
    The RCA Agent subscribes to this topic.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(
                v, default=str
            ).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            api_version=(2, 0, 0),
        )
        print("✅ Anomaly Publisher connected to Kafka!")

    def publish(self, anomaly: AnomalyEvent):
        """Sends one anomaly event to Kafka"""
        self.producer.send(
            topic=TOPIC_ANOMALIES,
            key=anomaly.service,
            value=anomaly.dict()
        )
        print(
            f"📤 PUBLISHED ANOMALY → {TOPIC_ANOMALIES} | "
            f"service={anomaly.service} | "
            f"type={anomaly.anomaly_type} | "
            f"severity={anomaly.severity}"
        )

    def publish_batch(self, anomalies: list):
        """Sends multiple anomaly events"""
        for anomaly in anomalies:
            self.publish(anomaly)
        if anomalies:
            self.producer.flush()

    def close(self):
        self.producer.close()