import random
import time
import math
import argparse
import uuid
import sys
import os
from datetime import datetime, timezone
from typing import List, Optional

# ── Fix import path so Python finds the ingestion package ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import LogEvent, MetricEvent, TraceSpan, LogLevel, SpanStatus
from ingestion.producer import TelemetryProducer

# ── Services ──────────────────────────────────────────────
SERVICES = [
    "api-gateway",
    "auth-service",
    "payment-service",
    "order-service",
    "inventory-service",
    "notification-service",
    "user-service",
]

SERVICE_DEPENDENCIES = {
    "api-gateway":          ["auth-service", "order-service"],
    "auth-service":         ["user-service"],
    "order-service":        ["payment-service", "inventory-service"],
    "payment-service":      ["notification-service"],
    "inventory-service":    [],
    "notification-service": [],
    "user-service":         [],
}

BASE_CPU = {
    "api-gateway": 35, "auth-service": 25, "payment-service": 45,
    "order-service": 30, "inventory-service": 20,
    "notification-service": 15, "user-service": 20,
}

BASE_LATENCY = {
    "api-gateway": 50, "auth-service": 30, "payment-service": 120,
    "order-service": 80, "inventory-service": 25,
    "notification-service": 20, "user-service": 25,
}

# ── Metric generation ─────────────────────────────────────
def generate_metrics(service: str, t: float,
                     anomaly_service: Optional[str] = None) -> List[MetricEvent]:

    cpu     = BASE_CPU.get(service, 30) + 15 * math.sin(2 * math.pi * t / 3600) + random.gauss(0, 3)
    latency = random.gauss(BASE_LATENCY.get(service, 60), 15)
    error   = random.uniform(0, 1.5)
    memory  = random.gauss(55, 8)
    rps     = random.gauss(200, 40)

    cpu    = max(0, min(100, cpu))
    memory = max(10, min(98, memory))
    rps    = max(0, rps)

    # Inject anomaly on target service
    if anomaly_service and service == anomaly_service:
        cpu     = random.uniform(85, 99)
        latency = random.gauss(2800, 300)
        error   = random.uniform(20, 45)
        memory  = random.gauss(88, 5)

    # Cascade degradation on services that CALL the broken one
    if anomaly_service:
        if anomaly_service in SERVICE_DEPENDENCIES.get(service, []):
            latency *= random.uniform(2.5, 4.0)
            error   += random.uniform(5, 15)

    now  = datetime.now(timezone.utc)
    tags = {"host": f"{service}-pod-1", "env": "production"}

    return [
        MetricEvent(timestamp=now, service=service,
                    metric_name="cpu_usage",          value=round(max(0, cpu), 2),     unit="%",     tags=tags),
        MetricEvent(timestamp=now, service=service,
                    metric_name="request_latency_ms", value=round(max(1, latency), 2), unit="ms",    tags=tags),
        MetricEvent(timestamp=now, service=service,
                    metric_name="error_rate_pct",     value=round(max(0, error), 2),   unit="%",     tags=tags),
        MetricEvent(timestamp=now, service=service,
                    metric_name="memory_usage_pct",   value=round(memory, 2),           unit="%",     tags=tags),
        MetricEvent(timestamp=now, service=service,
                    metric_name="requests_per_sec",   value=round(rps, 2),              unit="req/s", tags=tags),
    ]

# ── Log generation ────────────────────────────────────────
NORMAL_LOGS = [
    (LogLevel.INFO,  "Request processed successfully in {ms}ms"),
    (LogLevel.INFO,  "Database query completed in {ms}ms"),
    (LogLevel.INFO,  "Cache hit for key: user_session_{id}"),
    (LogLevel.DEBUG, "Health check passed"),
    (LogLevel.INFO,  "Order #{id} created successfully"),
]

ANOMALY_LOGS = [
    (LogLevel.ERROR,    "Connection timeout after 30000ms"),
    (LogLevel.ERROR,    "Database connection pool exhausted (50/50)"),
    (LogLevel.CRITICAL, "Unhandled exception in PaymentProcessor.charge()"),
    (LogLevel.CRITICAL, "Circuit breaker OPEN — stopping requests"),
    (LogLevel.ERROR,    "Query timeout after 30s on transactions table"),
]

CASCADE_LOGS = [
    (LogLevel.ERROR,   "Upstream {dep} returned HTTP 503"),
    (LogLevel.WARNING, "Slow response from {dep}: {ms}ms"),
    (LogLevel.ERROR,   "Failed to complete request: upstream unavailable"),
]

def generate_logs(service: str,
                  anomaly_service: Optional[str] = None,
                  trace_id: Optional[str] = None) -> List[LogEvent]:

    now   = datetime.now(timezone.utc)
    logs  = []
    count = random.randint(1, 3)

    is_anomaly  = anomaly_service and service == anomaly_service
    is_cascade  = anomaly_service and anomaly_service in SERVICE_DEPENDENCIES.get(service, [])

    for _ in range(count):
        if is_anomaly:
            level, msg = random.choice(ANOMALY_LOGS)
        elif is_cascade:
            level, msg = random.choice(CASCADE_LOGS)
            msg = msg.replace("{dep}", anomaly_service)
        else:
            level, msg = random.choice(NORMAL_LOGS)

        msg = msg.replace("{ms}", str(random.randint(10, 200)))
        msg = msg.replace("{id}", str(random.randint(1000, 9999)))

        logs.append(LogEvent(
            timestamp=now, service=service,
            level=level, message=msg,
            trace_id=trace_id,
            metadata={"env": "production"}
        ))
    return logs

# ── Trace generation ──────────────────────────────────────
def generate_trace(entry: str = "api-gateway",
                   anomaly_service: Optional[str] = None):

    trace_id = str(uuid.uuid4())
    spans    = []

    def make_span(service: str, parent_id: Optional[str] = None):
        span_id  = str(uuid.uuid4())
        duration = max(1, random.gauss(BASE_LATENCY.get(service, 60), 15))
        status   = SpanStatus.OK
        err_msg  = None

        if anomaly_service and service == anomaly_service:
            duration = random.gauss(2800, 400)
            if random.random() < 0.70:
                status  = SpanStatus.ERROR
                err_msg = "DB connection pool exhausted"

        spans.append(TraceSpan(
            trace_id=trace_id, span_id=span_id,
            parent_span_id=parent_id, service=service,
            operation=f"handle_{service.replace('-','_')}",
            duration_ms=round(duration, 2),
            status=status, error_message=err_msg,
            tags={"env": "production"}
        ))
        for dep in SERVICE_DEPENDENCIES.get(service, []):
            make_span(dep, parent_id=span_id)

    make_span(entry)
    return spans, trace_id

# ── Main loop ─────────────────────────────────────────────
def run(anomaly_service: Optional[str] = None, interval: int = 5):
    print("=" * 55)
    print("  PROJECT 71 — TELEMETRY SIMULATOR")
    print("=" * 55)
    if anomaly_service:
        print(f"  ⚠️  ANOMALY MODE → {anomaly_service} is failing!")
    else:
        print("  ✅  NORMAL MODE  → All services healthy")
    print(f"  📡  Sending to Kafka every {interval}s")
    print("=" * 55)

    producer = TelemetryProducer()
    t = 0

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ── Generating batch ──")

            spans, trace_id = generate_trace("api-gateway", anomaly_service)

            m_count = l_count = 0
            for service in SERVICES:
                for m in generate_metrics(service, t, anomaly_service):
                    producer.send_metric(m)
                    m_count += 1
                for l in generate_logs(service, anomaly_service, trace_id):
                    producer.send_log(l)
                    l_count += 1
            for span in spans:
                producer.send_trace(span)

            producer.flush()

            print(f"  📊 Metrics : {m_count}")
            print(f"  📝 Logs    : {l_count}")
            print(f"  🔗 Spans   : {len(spans)}")
            print(f"  🆔 TraceID : {trace_id[:8]}...")

            time.sleep(interval)
            t += interval

    except KeyboardInterrupt:
        print("\n⛔ Simulator stopped.")
        producer.close()

# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--anomaly",  type=str, default=None)
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()
    run(args.anomaly, args.interval)