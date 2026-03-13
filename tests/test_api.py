
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoints:

    def test_root_returns_200(self):
        """Test root endpoint returns 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint(self):
        """Test health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestIncidentEndpoints:

    def test_list_incidents_returns_200(self):
        """Test /incidents returns 200"""
        response = client.get("/incidents/")
        assert response.status_code == 200

    def test_list_incidents_has_structure(self):
        """Test /incidents returns correct structure"""
        response = client.get("/incidents/")
        data = response.json()
        assert "total"     in data
        assert "incidents" in data

    def test_recent_incidents(self):
        """Test /incidents/recent returns 200"""
        response = client.get("/incidents/recent")
        assert response.status_code == 200

    def test_incident_stats(self):
        """Test /incidents/stats returns 200"""
        response = client.get("/incidents/stats")
        assert response.status_code == 200

    def test_knowledge_base_endpoint(self):
        """Test /incidents/knowledge-base returns 200"""
        response = client.get("/incidents/knowledge-base")
        assert response.status_code == 200

    def test_invalid_incident_returns_404(self):
        """Test invalid incident ID returns 404"""
        response = client.get("/incidents/FAKE-ID-999")
        assert response.status_code == 404


class TestServiceEndpoints:

    def test_service_graph_returns_200(self):
        """Test /services/graph returns 200"""
        response = client.get("/services/graph")
        assert response.status_code == 200

    def test_service_graph_has_nodes(self):
        """Test service graph contains nodes and edges"""
        response = client.get("/services/graph")
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) > 0

    def test_service_list_returns_200(self):
        """Test /services/list returns 200"""
        response = client.get("/services/list")
        assert response.status_code == 200

    def test_blast_radius_payment_service(self):
        """Test blast radius for payment-service"""
        response = client.get("/services/payment-service/blast-radius")
        assert response.status_code == 200
        data = response.json()
        assert "total_affected" in data


class TestAnomalyEndpoints:

    def test_live_anomalies_returns_200(self):
        """Test /anomalies/live returns 200"""
        response = client.get("/anomalies/live")
        assert response.status_code == 200

    def test_anomaly_summary_returns_200(self):
        """Test /anomalies/summary returns 200"""
        response = client.get("/anomalies/summary")
        assert response.status_code == 200