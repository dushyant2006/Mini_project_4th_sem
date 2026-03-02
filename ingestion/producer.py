import json
import os
from kafka import KafkaProducer
from kafka.errors import KafkaTimeoutError

TOPIC_LOGS    = "telemetry.logs"
TOPIC_METRICS = "telemetry.metrics"
TOPIC_TRACES  = "telemetry.traces"


class TelemetryProducer:

    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            retries=3,
            linger_ms=10,
            api_version=(2, 0, 0),
        )
        print("✅ Kafka Producer connected!")

    def send_metric(self, metric):
        try:
            self.producer.send(
                topic=TOPIC_METRICS,
                key=metric.service,
                value=metric.dict()
            )
        except Exception as e:
            print(f"❌ Metric send error: {e}")

    def send_log(self, log):
        try:
            self.producer.send(
                topic=TOPIC_LOGS,
                key=log.service,
                value=log.dict()
            )
        except Exception as e:
            print(f"❌ Log send error: {e}")

    def send_trace(self, span):
        try:
            self.producer.send(
                topic=TOPIC_TRACES,
                key=span.trace_id,
                value=span.dict()
            )
        except Exception as e:
            print(f"❌ Trace send error: {e}")

    def flush(self):
        self.producer.flush()

    def close(self):
        self.producer.close()
        print("Kafka Producer closed.")