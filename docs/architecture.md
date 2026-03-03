# System Architecture — Project 71

## Data Flow

1. **Telemetry Simulator** generates realistic microservice data
2. **Kafka Producer** sends logs, metrics, traces to 3 topics
3. **ML Engine** reads metrics, detects anomalies
4. **RCA Agent** groups anomalies, finds root cause
5. **GenAI Engine** writes human-readable report
6. **FastAPI** exposes all data via REST endpoints

## Kafka Topics

| Topic | Producer | Consumer | Content |
|---|---|---|---|
| `telemetry.logs` | Simulator | Detection Engine | Log events |
| `telemetry.metrics` | Simulator | Detection Engine | Metric readings |
| `telemetry.traces` | Simulator | Detection Engine | Trace spans |
| `anomalies.detected` | Detection Engine | RCA Engine | Anomaly events |
| `rca.results` | RCA Engine | Report Engine | RCA reports |

## Service Dependency Graph
```
api-gateway (HIGH)
├── auth-service (HIGH)
│   └── user-service (MEDIUM)
└── order-service (HIGH)
    ├── payment-service (CRITICAL) ← most common failure point
    │   └── notification-service (LOW)
    └── inventory-service (MEDIUM)