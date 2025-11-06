"""
Unit tests for health API endpoints.

Tests the frontend-focused health check endpoints with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch

from minerva_backend.api.main import backend_app


@pytest.fixture
def client(test_container):
    """Create test client with mocked dependencies."""
    backend_app.state.container = test_container
    test_container.wire(modules=["minerva_backend.api.dependencies"])
    return TestClient(backend_app)


class TestHealthCheck:
    """Test main health check endpoint."""
    
    @patch('minerva_backend.containers.Container')
    def test_health_check_success(self, mock_container_class, client, mock_neo4j_connection, mock_curation_manager):
        """Test successful health check with all services healthy."""
        # Arrange
        from minerva_backend.processing.models import CurationStats
        mock_curation_manager.get_curation_stats.return_value = CurationStats(
            pending_entities=5,
            pending_relationships=3,
            completed=10
        )
        
        # Mock container services
        mock_container = Mock()
        mock_db_connection = Mock()
        mock_db_connection.health_check.return_value = True
        mock_llm_service = Mock()
        mock_llm_service.is_available = AsyncMock(return_value=True)
        mock_temporal_orchestrator = Mock()
        mock_temporal_orchestrator.is_available = AsyncMock(return_value=True)
        
        mock_container.db_connection.return_value = mock_db_connection
        mock_container.llm_service.return_value = mock_llm_service
        mock_container.pipeline_orchestrator.return_value = mock_temporal_orchestrator
        mock_container_class.return_value = mock_container
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "dashboard_info" in data
        assert "uptime_seconds" in data
        assert "version" in data
        
        # Check service statuses
        services = data["services"]
        assert services["database"]["status"] == "healthy"
        assert services["curation"]["status"] == "healthy"
        assert services["ollama"]["status"] == "healthy"
        assert services["temporal"]["status"] == "healthy"
        
        # Check dashboard info
        dashboard_info = data["dashboard_info"]
        assert dashboard_info["curation_backlog"] == 8  # 5 + 3
        assert "journals processed today" in dashboard_info["recent_activity"]
    
    def test_health_check_database_unhealthy(self, client, mock_curation_manager, test_container):
        """Test health check when database is unhealthy."""
        # Arrange
        mock_curation_manager.get_curation_stats.return_value = {
            "pending_entities": 0,
            "pending_relationships": 0,
            "completed_today": 0
        }
        
        # Mock database connection to return unhealthy
        mock_db_connection = Mock()
        mock_db_connection.health_check.return_value = False
        test_container.db_connection.override(mock_db_connection)
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["database"]["status"] == "unhealthy"
    
    @patch('minerva_backend.containers.Container')
    def test_health_check_curation_error(self, mock_container_class, client, mock_curation_manager):
        """Test health check when curation manager fails."""
        # Arrange
        mock_curation_manager.get_curation_stats.side_effect = Exception("Curation error")
        
        # Mock container services
        mock_container = Mock()
        mock_db_connection = Mock()
        mock_db_connection.health_check.return_value = True
        mock_llm_service = Mock()
        mock_llm_service.is_available = AsyncMock(return_value=True)
        mock_temporal_orchestrator = Mock()
        mock_temporal_orchestrator.is_available = AsyncMock(return_value=True)
        
        mock_container.db_connection.return_value = mock_db_connection
        mock_container.llm_service.return_value = mock_llm_service
        mock_container.pipeline_orchestrator.return_value = mock_temporal_orchestrator
        mock_container_class.return_value = mock_container
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["services"]["curation"]["status"] == "unhealthy"
        assert "Curation error" in data["services"]["curation"]["message"]
    
    @patch('minerva_backend.containers.Container')
    def test_health_check_response_structure(self, mock_container_class, client, mock_curation_manager):
        """Test that health check response has correct structure."""
        # Arrange
        mock_curation_manager.get_curation_stats.return_value = {
            "pending_entities": 2,
            "pending_relationships": 1,
            "completed_today": 5
        }
        
        # Mock container services
        mock_container = Mock()
        mock_db_connection = Mock()
        mock_db_connection.health_check.return_value = True
        mock_llm_service = Mock()
        mock_llm_service.is_available = AsyncMock(return_value=True)
        mock_temporal_orchestrator = Mock()
        mock_temporal_orchestrator.is_available = AsyncMock(return_value=True)
        
        mock_container.db_connection.return_value = mock_db_connection
        mock_container.llm_service.return_value = mock_llm_service
        mock_container.pipeline_orchestrator.return_value = mock_temporal_orchestrator
        mock_container_class.return_value = mock_container
        
        # Act
        response = client.get("/api/health/")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        required_fields = ["status", "services", "dashboard_info", "uptime_seconds", "version", "timestamp"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Check status is valid
        assert data["status"] in ["healthy", "unhealthy"]
        
        # Check services structure
        services = data["services"]
        expected_services = ["database", "curation", "ollama", "temporal"]
        for service in expected_services:
            assert service in services
            assert "status" in services[service]
            assert "message" in services[service]
            assert services[service]["status"] in ["healthy", "unhealthy", "unknown"]


class TestCurationHealth:
    """Test curation-specific health check endpoint."""
    
    def test_curation_health_success(self, client, mock_curation_manager):
        """Test successful curation health check."""
        # Arrange
        from minerva_backend.processing.models import CurationStats
        mock_curation_manager.get_curation_stats.return_value = CurationStats(
            pending_entities=10,
            pending_relationships=5,
            completed=3
        )
        
        # Act
        response = client.get("/api/health/curation")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "statistics" in data
        assert "recommendations" in data
        assert "timestamp" in data
        
        # Check statistics
        stats = data["statistics"]
        assert stats["pending_entities"] == 10
        assert stats["pending_relationships"] == 5
        assert stats["total_pending"] == 15
        assert stats["completed_today"] == 3
    
    def test_curation_health_high_backlog(self, client, mock_curation_manager):
        """Test curation health check with high backlog (no degraded status)."""
        # Arrange
        from minerva_backend.processing.models import CurationStats
        mock_curation_manager.get_curation_stats.return_value = CurationStats(
            pending_entities=100,
            pending_relationships=50,
            completed=2
        )
        
        # Act
        response = client.get("/api/health/curation")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"  # No degraded status for backlog
        assert data["statistics"]["total_pending"] == 150
        
        # Check recommendations
        recommendations = data["recommendations"]
        assert any("backlog" in rec.lower() for rec in recommendations)
        # Note: "oldest" recommendations are disabled in current implementation
        # as oldest_pending_age_hours is not available in CurationStats model
    
    def test_curation_health_exception(self, client, mock_curation_manager):
        """Test curation health check when exception occurs."""
        # Arrange
        mock_curation_manager.get_curation_stats.side_effect = Exception("Curation error")
        
        # Act
        response = client.get("/api/health/curation")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert "error" in data
        assert data["statistics"]["total_pending"] == 0


class TestHealthEndpoints:
    """Test health endpoint functionality."""
    
    def test_health_endpoints_exist(self, client):
        """Test that health endpoints are properly registered."""
        # Test that endpoints exist by checking OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Test that health endpoints are registered
        assert "/api/health/" in paths
        assert "/api/health/curation" in paths
    
    def test_health_endpoints_use_correct_methods(self, client):
        """Test that health endpoints use GET methods."""
        # All health endpoints should be GET
        endpoints = [
            "/api/health/",
            "/api/health/curation"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 405 Method Not Allowed
            assert response.status_code != 405
