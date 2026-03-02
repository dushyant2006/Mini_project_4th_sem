# ============================================================
# rca/agent/rca_agent.py
# PURPOSE: AI agent that reasons about failures to find
#          root cause and recommend fixes
#
# The agent follows this reasoning chain:
#   1. What service is failing?
#   2. What metrics are anomalous?
#   3. Which services are affected (blast radius)?
#   4. Which service failed FIRST? (root vs cascade)
#   5. What happened in similar past incidents?
#   6. Conclusion: root cause + recommended fix
# ============================================================

import sys
import os
from typing import List, Dict, Optional
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ingestion.models import AnomalyEvent
from rca.graph.graph_builder import ServiceDependencyGraph
from rca.rag_retriever import RAGRetriever


# ── Root cause hypothesis templates ──────────────────────────
# Mapped by anomaly type — gives the agent a starting hypothesis

HYPOTHESES = {
    "cpu_usage_anomaly": [
        "Database connection pool exhausted causing CPU spin",
        "Infinite loop or runaway process",
        "Traffic spike overwhelming service capacity",
        "Memory pressure causing excessive garbage collection",
    ],
    "request_latency_ms_anomaly": [
        "Upstream dependency slow or unavailable",
        "Database query performance degradation",
        "Network congestion or packet loss",
        "Resource contention (CPU/memory/IO)",
    ],
    "error_rate_pct_anomaly": [
        "Upstream service returning errors (cascade failure)",
        "Invalid input or schema change breaking requests",
        "Authentication/authorization failures",
        "Rate limiting or quota exceeded",
    ],
    "memory_usage_pct_anomaly": [
        "Memory leak in application code",
        "Large data set loaded into memory",
        "Cache growing unbounded",
        "JVM heap misconfiguration",
    ],
    "lstm_cpu_usage_pattern_anomaly": [
        "Gradual resource leak detected by pattern analysis",
        "Unusual traffic pattern emerging",
    ],
    "lstm_request_latency_ms_pattern_anomaly": [
        "Progressive performance degradation pattern detected",
        "Gradual upstream dependency slowdown",
    ],
}

# Fix recommendations per anomaly type
FIX_RECOMMENDATIONS = {
    "cpu_usage_anomaly": [
        "Check and increase database connection pool size",
        "Identify and kill runaway processes",
        "Scale service horizontally (add more replicas)",
        "Enable CPU profiling to identify hot spots",
    ],
    "request_latency_ms_anomaly": [
        "Check upstream service health and dependencies",
        "Review recent database query performance",
        "Enable circuit breaker to prevent cascade failures",
        "Add retry logic with exponential backoff",
    ],
    "error_rate_pct_anomaly": [
        "Check upstream service status immediately",
        "Review error logs for specific exception types",
        "Verify no breaking schema or API changes were deployed",
        "Implement graceful degradation if upstream is unstable",
    ],
    "memory_usage_pct_anomaly": [
        "Restart service pod to clear memory leak temporarily",
        "Trigger heap dump for memory leak analysis",
        "Review recent code changes for memory allocation issues",
        "Increase memory limit as temporary mitigation",
    ],
}


class RCAAgent:
    """
    Reasons about anomalies to determine root cause.

    Works WITHOUT an external LLM API in Phase 5.
    Uses rule-based reasoning + graph analysis + RAG.

    Phase 6 will upgrade this to use Claude API for
    richer, more nuanced natural language explanations.
    """

    def __init__(self):
        self.graph   = ServiceDependencyGraph()
        self.rag     = RAGRetriever()
        self.graph.print_graph_summary()
        print("✅ RCA Agent initialized and ready!\n")

    def analyze(self, anomalies: List[AnomalyEvent]) -> Dict:
        """
        Main analysis function.

        Takes a list of AnomalyEvents and returns a
        complete RCA report as a dictionary.

        Steps:
            1. Group anomalies by service
            2. Find root cause service (failed first)
            3. Calculate blast radius
            4. Search past incidents
            5. Generate hypotheses
            6. Build final report
        """

        if not anomalies:
            return {"status": "no_anomalies"}

        print(f"\n{'='*60}")
        print(f"🔍 RCA AGENT STARTING ANALYSIS")
        print(f"   Analyzing {len(anomalies)} anomaly events")
        print(f"{'='*60}")

        # ── STEP 1: Group anomalies by service ────────────────
        print("\n📋 STEP 1: Grouping anomalies by service...")
        service_anomalies: Dict[str, List[AnomalyEvent]] = {}

        for anomaly in anomalies:
            svc = anomaly.service
            if svc not in service_anomalies:
                service_anomalies[svc] = []
            service_anomalies[svc].append(anomaly)

        for svc, anoms in service_anomalies.items():
            print(f"   {svc}: {len(anoms)} anomalies")

        # ── STEP 2: Find root cause service ───────────────────
        print("\n🔎 STEP 2: Identifying root cause service...")
        root_cause_service = self._find_root_cause_service(
            list(service_anomalies.keys())
        )
        print(f"   → Root cause service: {root_cause_service}")

        # ── STEP 3: Calculate blast radius ────────────────────
        print("\n💥 STEP 3: Calculating blast radius...")
        blast_radius = self.graph.get_blast_radius(root_cause_service)
        print(f"   → Directly affected : {blast_radius['directly_affected']}")
        print(f"   → Indirectly affected: {blast_radius['indirectly_affected']}")

        # ── STEP 4: Search past incidents ─────────────────────
        print("\n📚 STEP 4: Searching past incidents (RAG)...")
        primary_anomaly = max(anomalies, key=lambda a: a.severity)
        similar_incidents = self.rag.search(
            service=root_cause_service,
            anomaly_type=primary_anomaly.anomaly_type,
            top_k=2
        )
        print(f"   → Found {len(similar_incidents)} similar past incidents")
        if similar_incidents:
            for inc in similar_incidents:
                print(f"     [{inc['id']}] {inc['root_cause'][:60]}...")

        # ── STEP 5: Generate hypotheses ───────────────────────
        print("\n💡 STEP 5: Generating root cause hypotheses...")
        hypotheses = self._generate_hypotheses(
            root_cause_service,
            service_anomalies[root_cause_service],
            similar_incidents
        )
        for i, h in enumerate(hypotheses[:3], 1):
            print(f"   Hypothesis {i}: {h}")

        # ── STEP 6: Build final report ────────────────────────
        print("\n📝 STEP 6: Building RCA report...")
        report = self._build_report(
            anomalies=anomalies,
            service_anomalies=service_anomalies,
            root_cause_service=root_cause_service,
            blast_radius=blast_radius,
            similar_incidents=similar_incidents,
            hypotheses=hypotheses,
        )

        print(f"\n✅ RCA COMPLETE — Severity: SEV-{report['severity']}")
        print(f"   Root Cause: {report['root_cause_summary'][:80]}...")

        return report

    def _find_root_cause_service(self,
                                  affected_services: List[str]) -> str:
        """
        Determines which service is the ROOT cause
        vs which are cascade victims.

        Logic: The root cause service is the one that
        is DOWNSTREAM (called by others) — because when
        a downstream service fails, all upstream callers suffer.

        Example:
            payment-service fails → order-service suffers
            payment-service is downstream = root cause
            order-service is upstream = cascade victim
        """
        if len(affected_services) == 1:
            return affected_services[0]

        # Score each service: more downstream = more likely root cause
        scores = {}
        for service in affected_services:
            # Count how many of the OTHER affected services call this one
            callers = self.graph.get_upstream_services(service)
            # More callers affected = more likely this is the bottleneck
            overlap = len(set(callers) & set(affected_services))
            scores[service] = overlap

        # Service with most affected callers = root cause
        root = max(scores, key=lambda s: scores[s])
        return root

    def _generate_hypotheses(self,
                              service: str,
                              anomalies: List[AnomalyEvent],
                              similar_incidents: List[Dict]) -> List[str]:
        """Generates root cause hypotheses from anomaly types + past incidents"""
        hypotheses = []

        # From anomaly type templates
        for anomaly in anomalies:
            templates = HYPOTHESES.get(anomaly.anomaly_type, [])
            hypotheses.extend(templates)

        # From similar past incidents (RAG)
        for incident in similar_incidents:
            hypotheses.insert(0, f"[Based on {incident['id']}] {incident['root_cause']}")

        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for h in hypotheses:
            if h not in seen:
                seen.add(h)
                unique.append(h)

        return unique[:5]

    def _determine_severity(self,
                             anomalies: List[AnomalyEvent],
                             blast_radius: Dict) -> int:
        """
        Determines incident severity (1=critical, 5=low)
        based on anomaly severity + blast radius.
        """
        max_anomaly_severity = max(a.severity for a in anomalies)
        affected_count = blast_radius.get("total_affected", 0)

        # More affected services = more severe
        if max_anomaly_severity >= 4 or affected_count >= 3:
            return 1    # SEV-1: Critical
        elif max_anomaly_severity >= 3 or affected_count >= 2:
            return 2    # SEV-2: High
        elif max_anomaly_severity >= 2:
            return 3    # SEV-3: Medium
        else:
            return 4    # SEV-4: Low

    def _build_report(self, anomalies, service_anomalies,
                      root_cause_service, blast_radius,
                      similar_incidents, hypotheses) -> Dict:
        """Assembles the final RCA report dictionary"""

        primary_anomaly = max(anomalies, key=lambda a: a.severity)
        severity        = self._determine_severity(anomalies, blast_radius)
        svc_info        = self.graph.get_service_info(root_cause_service)
        fixes           = FIX_RECOMMENDATIONS.get(
                              primary_anomaly.anomaly_type, []
                          )

        # Build human-readable root cause summary
        top_hypothesis = hypotheses[0] if hypotheses else "Unknown root cause"
        root_cause_summary = (
            f"{root_cause_service} experiencing "
            f"{primary_anomaly.anomaly_type.replace('_', ' ')}. "
            f"Most likely cause: {top_hypothesis}"
        )

        return {
            "incident_id":          f"INC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "timestamp":            datetime.now(timezone.utc).isoformat(),
            "severity":             severity,
            "root_cause_service":   root_cause_service,
            "root_cause_summary":   root_cause_summary,
            "owning_team":          svc_info.get("team", "unknown"),
            "hypotheses":           hypotheses[:3],
            "recommended_fixes":    fixes[:3],
            "blast_radius":         blast_radius,
            "anomaly_count":        len(anomalies),
            "affected_services":    list(service_anomalies.keys()),
            "similar_incidents":    [i["id"] for i in similar_incidents],
            "primary_anomaly": {
                "type":           primary_anomaly.anomaly_type,
                "observed_value": primary_anomaly.observed_value,
                "expected_value": primary_anomaly.expected_value,
                "severity":       primary_anomaly.severity,
            },
            "status": "root_cause_identified"
        }