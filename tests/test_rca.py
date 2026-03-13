# ============================================================
# tests/test_rca.py
# PURPOSE: Unit tests for RCA agent and graph builder
# ============================================================

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rca.graph.graph_builder import ServiceDependencyGraph
from rca.rag_retriever       import RAGRetriever


class TestServiceDependencyGraph:

    def setup_method(self):
        self.graph = ServiceDependencyGraph()

    def test_graph_has_services(self):
        """Test graph contains expected services"""
        services = list(self.graph.graph.nodes())
        assert "payment-service" in services
        assert "api-gateway"     in services
        assert "order-service"   in services

    def test_downstream_services(self):
        """Test downstream services of api-gateway"""
        downstream = self.graph.get_downstream_services("api-gateway")
        assert "order-service" in downstream
        assert "auth-service"  in downstream

    def test_upstream_services(self):
        """Test order-service calls payment-service (downstream)"""
        downstream = self.graph.get_downstream_services("order-service")
        assert "payment-service" in downstream

    def test_blast_radius_payment_service(self):
        """Test blast radius of payment-service failure"""
        blast = self.graph.get_blast_radius("payment-service")
        assert "total_affected"      in blast
        assert "directly_affected"   in blast
        assert "indirectly_affected" in blast
        assert blast["total_affected"] > 0

    def test_blast_radius_criticality_score(self):
        """Test criticality score is positive"""
        blast = self.graph.get_blast_radius("api-gateway")
        assert blast["criticality_score"] > 0

    def test_unknown_service_returns_empty(self):
        """Test unknown service returns empty results"""
        downstream = self.graph.get_downstream_services("fake-service")
        assert downstream == [] or downstream == set()


class TestRAGRetriever:

    def setup_method(self):
        self.rag = RAGRetriever()

    def test_rag_has_seed_incidents(self):
        """Test RAG has seed incidents loaded"""
        stats = self.rag.get_stats()
        assert stats["seed_incidents"] == 6

    def test_search_returns_results(self):
        """Test search returns relevant incidents"""
        results = self.rag.search(
            service="payment-service",
            anomaly_type="cpu_usage_anomaly",
            top_k=3
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_payment_service(self):
        """Test payment-service search returns payment incidents"""
        results = self.rag.search(
            service="payment-service",
            anomaly_type="cpu_usage_anomaly"
        )
        services = [r["service"] for r in results]
        assert "payment-service" in services

    def test_format_for_agent(self):
        """Test formatting returns readable string"""
        results = self.rag.search("auth-service", "memory_usage_pct_anomaly")
        formatted = self.rag.format_for_agent(results)
        assert isinstance(formatted, str)
        assert len(formatted) > 0

    def test_get_stats_structure(self):
        """Test stats returns correct keys"""
        stats = self.rag.get_stats()
        assert "seed_incidents"    in stats
        assert "learned_incidents" in stats
        assert "total"             in stats
