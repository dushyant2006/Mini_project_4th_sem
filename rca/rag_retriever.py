# ============================================================
# rca/rag_retriever.py
# PURPOSE: Stores and retrieves similar past incidents
#          using vector similarity search (RAG)
#
# How it works:
#   1. Past incidents are converted to text embeddings (vectors)
#   2. When new anomaly occurs, we search for similar vectors
#   3. Top matches = most similar past incidents
#   4. These are fed to the RCA agent for context
# ============================================================

import json
import os
import sys
from typing import List, Dict
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── Sample Past Incidents (knowledge base) ───────────────────
# In a real system these come from PagerDuty/Jira history
# For now we hardcode realistic examples

PAST_INCIDENTS = [
    {
        "id": "INC-001",
        "date": "2024-03-12",
        "service": "payment-service",
        "anomaly_type": "cpu_usage_anomaly",
        "root_cause": "Database connection pool exhausted due to slow queries during peak traffic",
        "symptoms": "High CPU, increased latency, DB connection errors, cascade to order-service",
        "resolution": "Increased DB connection pool size from 10 to 50, optimized slow queries, restarted payment-service pod",
        "duration_minutes": 45,
        "severity": 2,
    },
    {
        "id": "INC-002",
        "date": "2024-04-22",
        "service": "payment-service",
        "anomaly_type": "request_latency_ms_anomaly",
        "root_cause": "Third-party payment gateway experiencing degraded performance",
        "symptoms": "Latency spike above 3000ms, timeout errors, increased error rate",
        "resolution": "Enabled circuit breaker, switched to backup payment provider, incident resolved in 30 mins",
        "duration_minutes": 30,
        "severity": 2,
    },
    {
        "id": "INC-003",
        "date": "2024-05-08",
        "service": "auth-service",
        "anomaly_type": "memory_usage_pct_anomaly",
        "root_cause": "Memory leak in JWT token validation cache — tokens not expiring correctly",
        "symptoms": "Gradual memory increase from 55% to 99%, eventual OOM crash",
        "resolution": "Patched token expiry bug, restarted auth-service, added memory alerting",
        "duration_minutes": 120,
        "severity": 1,
    },
    {
        "id": "INC-004",
        "date": "2024-06-15",
        "service": "order-service",
        "anomaly_type": "error_rate_pct_anomaly",
        "root_cause": "Upstream payment-service returning 503 — cascade failure from payment outage",
        "symptoms": "Error rate jumped to 35%, orders failing, customers unable to checkout",
        "resolution": "Identified payment-service as root cause, added retry logic with exponential backoff",
        "duration_minutes": 25,
        "severity": 2,
    },
    {
        "id": "INC-005",
        "date": "2024-07-03",
        "service": "api-gateway",
        "anomaly_type": "cpu_usage_anomaly",
        "root_cause": "Traffic spike from marketing campaign overwhelmed API gateway",
        "symptoms": "CPU 95%, request queue backed up, increased latency across all services",
        "resolution": "Scaled api-gateway horizontally to 5 replicas, enabled rate limiting",
        "duration_minutes": 15,
        "severity": 3,
    },
    {
        "id": "INC-006",
        "date": "2024-08-19",
        "service": "inventory-service",
        "anomaly_type": "request_latency_ms_anomaly",
        "root_cause": "Full table scan on inventory database — missing index on product_id column",
        "symptoms": "Query latency 5000ms+, order-service timeouts, inventory checks failing",
        "resolution": "Added database index on product_id, query time dropped to 12ms",
        "duration_minutes": 60,
        "severity": 3,
    },
]


class RAGRetriever:
    """
    Simple RAG retriever using keyword and service matching.

    In Phase 6 we'll upgrade this to use real vector embeddings
    (sentence-transformers + FAISS) for semantic search.
    For now, keyword matching gives good results.
    """

    def __init__(self):
        self.incidents = PAST_INCIDENTS
        print(f"✅ RAG Retriever initialized with "
              f"{len(self.incidents)} past incidents")

    def search(self, service: str,
               anomaly_type: str,
               top_k: int = 3) -> List[Dict]:
        """
        Finds most similar past incidents.

        Scoring:
            +3 points if same service
            +2 points if same anomaly type
            +1 point for each matching keyword
        """
        scored = []

        for incident in self.incidents:
            score = 0

            # Same service = strong match
            if incident["service"] == service:
                score += 3

            # Same anomaly type = strong match
            if incident["anomaly_type"] == anomaly_type:
                score += 2

            # Keyword matching in symptoms and root cause
            search_text = (
                incident["symptoms"] + " " +
                incident["root_cause"]
            ).lower()

            keywords = anomaly_type.replace("_", " ").split()
            keywords += service.replace("-", " ").split()

            for kw in keywords:
                if kw in search_text:
                    score += 1

            scored.append((score, incident))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)

        # Return top_k results
        return [inc for score, inc in scored[:top_k] if score > 0]

    def format_for_agent(self, incidents: List[Dict]) -> str:
        """
        Formats retrieved incidents as readable text
        for the RCA agent to use as context.
        """
        if not incidents:
            return "No similar past incidents found."

        lines = ["SIMILAR PAST INCIDENTS:"]
        lines.append("=" * 50)

        for inc in incidents:
            lines.append(f"\n[{inc['id']}] — {inc['date']}")
            lines.append(f"Service    : {inc['service']}")
            lines.append(f"Root Cause : {inc['root_cause']}")
            lines.append(f"Symptoms   : {inc['symptoms']}")
            lines.append(f"Resolution : {inc['resolution']}")
            lines.append(f"Duration   : {inc['duration_minutes']} minutes")
            lines.append("-" * 40)

        return "\n".join(lines)