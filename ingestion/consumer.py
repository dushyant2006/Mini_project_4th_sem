import json
import os
import sys
from kafka import KafkaConsumer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TOPIC_LOGS    = "telemetry.logs"
TOPIC_METRICS = "telemetry.metrics"
TOPIC_TRACES  = "telemetry.traces"


class TelemetryConsumer:

    def __init__(self):
        self.consumer = KafkaConsumer(
            TOPIC_LOGS,
            TOPIC_METRICS,
            TOPIC_TRACES,
            bootstrap_servers="localhost:9092",
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            auto_offset_reset="latest",
            group_id="telemetry-processor",
            enable_auto_commit=True,
            consumer_timeout_ms=2000,
            api_version=(2, 0, 0),
        )
        print("✅ Consumer connected! Waiting for messages...\n")

    def run(self):
        print("-" * 70)
        try:
            while True:
                records = self.consumer.poll(timeout_ms=1000)

                if not records:
                    continue

                for tp, messages in records.items():
                    for msg in messages:
                        topic = msg.topic
                        data  = msg.value

                        if topic == TOPIC_METRICS:
                            svc  = data.get("service", "?")
                            name = data.get("metric_name", "?")
                            val  = data.get("value", 0)
                            unit = data.get("unit", "")
                            print(f"📊 METRIC | {svc:<26}| {name:<28}| {val} {unit}")

                        elif topic == TOPIC_LOGS:
                            svc  = data.get("service", "?")
                            lvl  = data.get("level", "INFO")
                            msg2 = data.get("message", "")
                            icon = "🔴" if lvl in ["ERROR", "CRITICAL"] else "🟡" if lvl == "WARNING" else "🟢"
                            print(f"{icon} LOG    | {svc:<26}| {lvl:<10}| {msg2}")

                        elif topic == TOPIC_TRACES:
                            svc  = data.get("service", "?")
                            op   = data.get("operation", "?")
                            dur  = data.get("duration_ms", 0)
                            st   = data.get("status", "OK")
                            icon = "❌" if st == "ERROR" else "✅"
                            print(f"{icon} TRACE  | {svc:<26}| {op:<36}| {dur}ms")

        except KeyboardInterrupt:
            print("\n⛔ Consumer stopped.")
        finally:
            self.consumer.close()


if __name__ == "__main__":
    c = TelemetryConsumer()
    c.run()