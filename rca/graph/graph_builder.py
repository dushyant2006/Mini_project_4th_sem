# ============================================================
# rca/graph/graph_builder.py
# PURPOSE: Builds and queries the service dependency graph
#
# The graph answers questions like:
#   "Which services does payment-service affect?"
#   "What is the upstream caller of order-service?"
#   "What is the full blast radius of this failure?"
# ============================================================

import networkx as nx
from typing import List, Dict, Set
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── Service dependency map ────────────────────────────────
# Same structure as simulate_telemetry.py
# Key   = service
# Value = list of services it CALLS (downstream)
SERVICE_DEPENDENCIES = {
    "api-gateway":          ["auth-service", "order-service"],
    "auth-service":         ["user-service"],
    "order-service":        ["payment-service", "inventory-service"],
    "payment-service":      ["notification-service"],
    "inventory-service":    [],
    "notification-service": [],
    "user-service":         [],
}

# Service metadata — used in incident reports
SERVICE_METADATA = {
    "api-gateway":          {"tier": "frontend",  "criticality": "high",   "team": "platform"},
    "auth-service":         {"tier": "backend",   "criticality": "high",   "team": "security"},
    "payment-service":      {"tier": "backend",   "criticality": "critical","team": "payments"},
    "order-service":        {"tier": "backend",   "criticality": "high",   "team": "orders"},
    "inventory-service":    {"tier": "backend",   "criticality": "medium", "team": "inventory"},
    "notification-service": {"tier": "backend",   "criticality": "low",    "team": "platform"},
    "user-service":         {"tier": "backend",   "criticality": "medium", "team": "identity"},
}


class ServiceDependencyGraph:
    """
    Represents the microservices architecture as a
    directed graph where edges mean "A calls B".

    Uses NetworkX — a Python graph library.

    Example graph:
        api-gateway → auth-service → user-service
        api-gateway → order-service → payment-service → notification-service
                                    → inventory-service
    """

    def __init__(self):
        # DiGraph = Directed Graph (edges have direction)
        # A → B means "A calls B"
        self.graph = nx.DiGraph()
        self._build_graph()
        print("✅ Service dependency graph built!")
        print(f"   Nodes (services): {self.graph.number_of_nodes()}")
        print(f"   Edges (calls):    {self.graph.number_of_edges()}")

    def _build_graph(self):
        """Builds the graph from SERVICE_DEPENDENCIES"""

        # Add all services as nodes with metadata
        for service, meta in SERVICE_METADATA.items():
            self.graph.add_node(service, **meta)

        # Add edges (A calls B = edge from A to B)
        for service, dependencies in SERVICE_DEPENDENCIES.items():
            for dep in dependencies:
                self.graph.add_edge(service, dep)

    def get_downstream_services(self, service: str) -> List[str]:
        """
        Returns all services that this service calls
        (directly or indirectly).

        Example: get_downstream_services("api-gateway")
        Returns: ["auth-service", "user-service",
                  "order-service", "payment-service",
                  "notification-service", "inventory-service"]
        """
        # nx.descendants finds ALL reachable nodes from a starting node
        try:
            descendants = nx.descendants(self.graph, service)
            return list(descendants)
        except nx.NetworkXError:
            return []

    def get_upstream_services(self, service: str) -> List[str]:
        """
        Returns all services that CALL this service
        (directly or indirectly).

        Example: get_upstream_services("payment-service")
        Returns: ["order-service", "api-gateway"]

        These are the services AFFECTED when payment-service fails!
        """
        # Reverse the graph to find who calls this service
        reversed_graph = self.graph.reverse()
        try:
            ancestors = nx.ancestors(reversed_graph, service)
            return list(ancestors)
        except nx.NetworkXError:
            return []

    def get_direct_callers(self, service: str) -> List[str]:
        """
        Returns ONLY the immediate callers of this service.

        Example: get_direct_callers("payment-service")
        Returns: ["order-service"]
        """
        # In reversed graph, neighbors = direct callers
        reversed_graph = self.graph.reverse()
        try:
            return list(reversed_graph.neighbors(service))
        except nx.NetworkXError:
            return []

    def get_blast_radius(self, failed_service: str) -> Dict:
        """
        Calculates the full blast radius of a service failure.

        Returns a dict with:
            - directly_affected: services that directly call failed one
            - indirectly_affected: services further up the chain
            - criticality_score: how critical is this failure?
        """
        direct   = self.get_direct_callers(failed_service)
        upstream = self.get_upstream_services(failed_service)
        indirect = [s for s in upstream if s not in direct]

        # Calculate criticality score
        meta = SERVICE_METADATA.get(failed_service, {})
        criticality_map = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        base_score = criticality_map.get(meta.get("criticality", "low"), 1)

        # More affected services = higher score
        impact_score = base_score * (len(upstream) + 1)

        return {
            "failed_service":      failed_service,
            "directly_affected":   direct,
            "indirectly_affected": indirect,
            "total_affected":      len(upstream),
            "criticality_score":   impact_score,
            "service_tier":        meta.get("tier", "unknown"),
            "owning_team":         meta.get("team", "unknown"),
        }

    def get_call_path(self, source: str, target: str) -> List[str]:
        """
        Finds the call path between two services.

        Example: get_call_path("api-gateway", "notification-service")
        Returns: ["api-gateway", "order-service",
                  "payment-service", "notification-service"]
        """
        try:
            path = nx.shortest_path(self.graph, source, target)
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_service_info(self, service: str) -> Dict:
        """Returns metadata for a service"""
        return SERVICE_METADATA.get(service, {})

    def print_graph_summary(self):
        """Prints a readable summary of the graph"""
        print("\n📊 SERVICE DEPENDENCY GRAPH")
        print("=" * 50)
        for service, deps in SERVICE_DEPENDENCIES.items():
            meta = SERVICE_METADATA.get(service, {})
            crit = meta.get("criticality", "?")
            if deps:
                print(f"  {service} ({crit})")
                for dep in deps:
                    print(f"    └── calls → {dep}")
            else:
                print(f"  {service} ({crit}) [no downstream]")
        print("=" * 50)