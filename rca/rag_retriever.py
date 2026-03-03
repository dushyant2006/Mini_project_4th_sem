
import os
import sys
from typing import List, Dict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rca.incident_store import IncidentStore


# ── Seed incidents (always present) ──────────────────────────
SEED_INCIDENTS = [
    {
        "id": "INC-001",
        "date": "2024-03-12",
        "service": "payment-service",
        "anomaly_type": "cpu_usage_anomaly",
        "root_cause": "Database connection pool exhausted due to slow queries during peak traffic",
        "symptoms": "High CPU, increased latency, DB connection errors, cascade to order-service",
        "resolution": "Increased DB connection pool size from 10 to 50, optimized slow queries",
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
        "resolution": "Enabled circuit breaker, switched to backup payment provider",
        "duration_minutes": 30,
        "severity": 2,
    },
    {
        "id": "INC-003",
        "date": "2024-05-08",
        "service": "auth-service",
        "anomaly_type": "memory_usage_pct_anomaly",
        "root_cause": "Memory leak in JWT token validation cache",
        "symptoms": "Gradual memory increase from 55% to 99%, eventual OOM crash",
        "resolution": "Patched token expiry bug, restarted auth-service",
        "duration_minutes": 120,
        "severity": 1,
    },
    {
        "id": "INC-004",
        "date": "2024-06-15",
        "service": "order-service",
        "anomaly_type": "error_rate_pct_anomaly",
        "root_cause": "Upstream payment-service returning 503 — cascade failure",
        "symptoms": "Error rate jumped to 35%, orders failing",
        "resolution": "Identified payment-service as root cause, added retry logic",
        "duration_minutes": 25,
        "severity": 2,
    },
    {
        "id": "INC-005",
        "date": "2024-07-03",
        "service": "api-gateway",
        "anomaly_type": "cpu_usage_anomaly",
        "root_cause": "Traffic spike from marketing campaign overwhelmed API gateway",
        "symptoms": "CPU 95%, request queue backed up",
        "resolution": "Scaled api-gateway to 5 replicas, enabled rate limiting",
        "duration_minutes": 15,
        "severity": 3,
    },
    {
        "id": "INC-006",
        "date": "2024-08-19",
        "service": "inventory-service",
        "anomaly_type": "request_latency_ms_anomaly",
        "root_cause": "Full table scan — missing index on product_id column",
        "symptoms": "Query latency 5000ms+, order-service timeouts",
        "resolution": "Added database index on product_id",
        "duration_minutes": 60,
        "severity": 3,
    },
]


class RAGRetriever:
    """
    Retrieves similar past incidents using keyword + service matching.

    Searches across:
        1. Seed incidents (6 hardcoded)
        2. Auto-learned incidents (grows with every new incident)

    The more incidents the system handles, the smarter it gets!
    """

    def __init__(self):
        # Load persistent incident store
        self.store = IncidentStore()
        print(f"✅ RAG Retriever ready — "
              f"{len(SEED_INCIDENTS)} seed + "
              f"{self.store.count()} learned incidents")

    @property
    def all_incidents(self) -> List[Dict]:
        """Combines seed + learned incidents for searching"""
        return SEED_INCIDENTS + self.store.get_all()

    def search(self, service: str,
               anomaly_type: str,
               top_k: int = 3) -> List[Dict]:
        """
        Finds most similar past incidents from BOTH
        seed and learned knowledge bases.

        Scoring:
            +3 points → same service
            +2 points → same anomaly type
            +1 point  → keyword match in symptoms/root cause
        """
        scored = []

        for incident in self.all_incidents:
            score = 0

            if incident.get("service") == service:
                score += 3

            if incident.get("anomaly_type") == anomaly_type:
                score += 2

            search_text = (
                incident.get("symptoms", "") + " " +
                incident.get("root_cause", "")
            ).lower()

            keywords = anomaly_type.replace("_", " ").split()
            keywords += service.replace("-", " ").split()

            for kw in keywords:
                if kw in search_text:
                    score += 1

            # Bonus: learned incidents are MORE relevant
            # (they came from THIS specific system)
            if incident.get("source") == "auto_learned":
                score += 1

            scored.append((score, incident))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [inc for score, inc in scored[:top_k] if score > 0]

    def save_new_incident(self, rca_report: Dict) -> str:
        """
        Called after every resolved incident to add it
        to the persistent knowledge base.

        This is how the system LEARNS over time.
        """
        return self.store.add_incident(rca_report)

    def get_stats(self) -> Dict:
        """Returns knowledge base statistics"""
        return {
            "seed_incidents":    len(SEED_INCIDENTS),
            "learned_incidents": self.store.count(),
            "total":             len(self.all_incidents),
        }

    def format_for_agent(self, incidents: List[Dict]) -> str:
        """Formats retrieved incidents as readable text"""
        if not incidents:
            return "No similar past incidents found."

        lines = ["SIMILAR PAST INCIDENTS:"]
        lines.append("=" * 50)

        for inc in incidents:
            source = "🧠 LEARNED" if inc.get(
                "source") == "auto_learned" else "📚 SEED"
            lines.append(f"\n[{inc['id']}] {source} — {inc['date']}")
            lines.append(f"Service    : {inc['service']}")
            lines.append(f"Root Cause : {inc['root_cause']}")
            lines.append(f"Symptoms   : {inc['symptoms']}")
            lines.append(f"Resolution : {inc['resolution']}")
            lines.append("-" * 40)

        return "\n".join(lines)