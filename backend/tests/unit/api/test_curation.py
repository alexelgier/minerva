"""
Unit tests for curation API endpoints.

Tests the human-in-the-loop curation endpoints with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from minerva_backend.api.main import backend_app


@pytest.fixture
def client(test_container):
    """Create test client with mocked dependencies."""
    backend_app.state.container = test_container
    test_container.wire(modules=["minerva_backend.api.dependencies"])
    return TestClient(backend_app)


class TestCurationStats:
    """Test curation statistics endpoints."""
    
    def test_get_curation_stats_success(self, client, mock_curation_manager):
        """Test successful curation stats retrieval."""
        # Arrange
        mock_stats = {
            "total_journals": 10,
            "pending_entities": 5,
            "pending_relationships": 3,
            "completed": 2,
            "entity_stats": {
                "total_extracted": 25,
                "accepted": 20,
                "rejected": 3,
                "pending": 2,
                "acceptance_rate": 0.87
            },
            "relationship_stats": {
                "total_extracted": 15,
                "accepted": 12,
                "rejected": 1,
                "pending": 2,
                "acceptance_rate": 0.92
            }
        }
        mock_curation_manager.get_curation_stats.return_value = mock_stats
        
        # Act
        response = client.get("/api/curation/stats")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data
        assert data["stats"]["total_journals"] == 10
        assert data["stats"]["pending_entities"] == 5
        assert data["stats"]["pending_relationships"] == 3
    
    def test_get_curation_stats_error(self, client, mock_curation_manager):
        """Test curation stats retrieval when manager fails."""
        # Arrange
        mock_curation_manager.get_curation_stats.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/curation/stats")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestPendingCuration:
    """Test pending curation tasks endpoints."""
    
    def test_get_pending_curation_success(self, client, mock_curation_manager):
        """Test successful pending curation tasks retrieval."""
        # Arrange
        mock_pending_journals = {
            "journal_1": {
                "journal_id": "journal_1",
                "date": "2025-09-29",
                "phase": "entities",
                "tasks": {
                    "task_1": {
                        "id": "task_1",
                        "journal_id": "journal_1",
                        "type": "entity",
                        "status": "pending",
                        "created_at": "2025-09-29T00:00:00Z",
                        "data": {"text": "test entity"}
                    }
                }
            }
        }
        mock_stats = {
            "total_journals": 1,
            "pending_entities": 1,
            "pending_relationships": 0
        }
        
        mock_curation_manager.get_all_pending_curation_tasks.return_value = mock_pending_journals
        mock_curation_manager.get_curation_stats.return_value = mock_stats
        
        # Act
        response = client.get("/api/curation/pending")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "journal_entries" in data
        assert "stats" in data
        assert len(data["journal_entries"]) == 1
        assert "journal_1" in data["journal_entries"]
    
    def test_get_pending_curation_error(self, client, mock_curation_manager):
        """Test pending curation tasks retrieval when manager fails."""
        # Arrange
        mock_curation_manager.get_all_pending_curation_tasks.side_effect = Exception("Database error")
        
        # Act
        response = client.get("/api/curation/pending")
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestEntityCuration:
    """Test entity curation endpoints."""
    
    def test_complete_entity_curation_success(self, client, mock_curation_manager):
        """Test successful entity curation completion."""
        # Arrange
        journal_id = "test_journal_123"
        mock_curation_manager.complete_entity_phase.return_value = None
        
        # Act
        response = client.post(f"/api/curation/entities/{journal_id}/complete")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Entity curation phase completed"
        assert data["journal_id"] == journal_id
        assert data["data"]["phase"] == "entity"
        assert data["data"]["status"] == "completed"
    
    def test_complete_entity_curation_invalid_id(self, client, mock_curation_manager):
        """Test entity curation completion with invalid journal ID."""
        # Arrange
        invalid_journal_id = "short"
        
        # Act
        response = client.post(f"/api/curation/entities/{invalid_journal_id}/complete")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Invalid journal ID format" in data["detail"]
    
    def test_handle_entity_curation_accept_success(self, client, mock_curation_manager):
        """Test successful entity acceptance."""
        # Arrange
        journal_id = "test_journal_123"
        entity_id = "test_entity_456"
        curated_data = {"name": "Updated Entity", "type": "person"}
        updated_uuid = "new_uuid_789"
        
        mock_curation_manager.accept_entity = AsyncMock(return_value=updated_uuid)
        
        action_data = {
            "action": "accept",
            "curated_data": curated_data
        }
        
        # Act
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Entity accepted and updated"
        assert data["journal_id"] == journal_id
        assert data["data"]["entity_id"] == entity_id
        assert data["data"]["action"] == "accept"
        assert data["data"]["updated_uuid"] == updated_uuid
    
    def test_handle_entity_curation_reject_success(self, client, mock_curation_manager):
        """Test successful entity rejection."""
        # Arrange
        journal_id = "test_journal_123"
        entity_id = "test_entity_456"
        
        action_data = {
            "action": "reject",
            "curated_data": {}
        }
        
        # Act
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Entity rejected"
        assert data["data"]["action"] == "reject"
    
    def test_handle_entity_curation_accept_missing_data(self, client, mock_curation_manager):
        """Test entity acceptance without curated data."""
        # Arrange
        journal_id = "test_journal_123"
        entity_id = "test_entity_456"
        
        action_data = {
            "action": "accept",
            "curated_data": {}
        }
        
        # Act
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data
    
    def test_handle_entity_curation_not_found(self, client, mock_curation_manager):
        """Test entity curation when entity is not found."""
        # Arrange
        journal_id = "test_journal_123"
        entity_id = "test_entity_456"
        
        # Configure the mock to return None (entity not found)
        mock_curation_manager.accept_entity = AsyncMock(return_value=None)
        
        action_data = {
            "action": "accept",
            "curated_data": {"name": "Test Entity"}
        }
        
        # Act
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        # The error response format may vary, check for error content
        assert "error" in data or "detail" in data


class TestRelationshipCuration:
    """Test relationship curation endpoints."""
    
    def test_complete_relationship_curation_success(self, client, mock_curation_manager):
        """Test successful relationship curation completion."""
        # Arrange
        journal_id = "test_journal_123"
        mock_curation_manager.complete_relationship_phase.return_value = None
        
        # Act
        response = client.post(f"/api/curation/relationships/{journal_id}/complete")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Relationship curation phase completed"
        assert data["journal_id"] == journal_id
        assert data["data"]["phase"] == "relationship"
        assert data["data"]["status"] == "completed"
    
    def test_handle_relationship_curation_accept_success(self, client, mock_curation_manager):
        """Test successful relationship acceptance."""
        # Arrange
        journal_id = "test_journal_123"
        relationship_id = "test_relationship_456"
        curated_data = {"type": "works_with", "confidence": 0.95}
        updated_uuid = "new_uuid_789"
        
        mock_curation_manager.accept_relationship = AsyncMock(return_value=updated_uuid)
        
        action_data = {
            "action": "accept",
            "curated_data": curated_data
        }
        
        # Act
        response = client.post(
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Relationship accepted and updated"
        assert data["data"]["relationship_id"] == relationship_id
        assert data["data"]["action"] == "accept"
    
    def test_handle_relationship_curation_reject_success(self, client, mock_curation_manager):
        """Test successful relationship rejection."""
        # Arrange
        journal_id = "test_journal_123"
        relationship_id = "test_relationship_456"
        updated_uuid = "new_uuid_789"
        
        mock_curation_manager.reject_relationship = AsyncMock(return_value=True)
        
        action_data = {
            "action": "reject",
            "curated_data": {}
        }
        
        # Act
        response = client.post(
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            json=action_data
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Relationship rejected"
        assert data["data"]["action"] == "reject"


class TestBulkOperations:
    """Test bulk curation operations."""
    
    def test_bulk_accept_all_entities_success(self, client, mock_curation_manager):
        """Test successful bulk accept all entities."""
        # Arrange
        journal_id = "test_journal_123"
        phase = "entity"
        
        # Act
        response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase={phase}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Bulk accepted" in data["message"]
        assert data["data"]["phase"] == phase
        assert data["data"]["accepted_count"] == 0  # Currently returns 0 as placeholder
    
    def test_bulk_accept_all_relationships_success(self, client, mock_curation_manager):
        """Test successful bulk accept all relationships."""
        # Arrange
        journal_id = "test_journal_123"
        phase = "relationship"
        
        # Act
        response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase={phase}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["phase"] == phase
    
    def test_bulk_accept_all_invalid_phase(self, client, mock_curation_manager):
        """Test bulk accept all with invalid phase."""
        # Arrange
        journal_id = "test_journal_123"
        phase = "invalid_phase"
        
        # Act
        response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase={phase}")
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        # The error response format may vary, check for error content
        assert "error" in data or "detail" in data


class TestCurationEndpoints:
    """Test curation endpoint functionality."""
    
    def test_curation_endpoints_exist(self, client):
        """Test that curation endpoints are properly registered."""
        # Test that endpoints exist by checking OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Test that curation endpoints are registered
        expected_endpoints = [
            "/api/curation/pending",
            "/api/curation/stats",
            "/api/curation/entities/{journal_id}/complete",
            "/api/curation/entities/{journal_id}/{entity_id}",
            "/api/curation/relationships/{journal_id}/complete",
            "/api/curation/relationships/{journal_id}/{relationship_id}",
            "/api/curation/bulk/accept-all/{journal_id}"
        ]
        
        for endpoint in expected_endpoints:
            assert endpoint in paths, f"Missing endpoint: {endpoint}"
    
    def test_curation_endpoints_use_correct_methods(self, client):
        """Test that curation endpoints use correct HTTP methods."""
        # Test GET endpoints
        get_endpoints = [
            "/api/curation/pending",
            "/api/curation/stats"
        ]
        
        for endpoint in get_endpoints:
            response = client.get(endpoint)
            # Should not return 405 Method Not Allowed
            assert response.status_code != 405
        
        # Test POST endpoints
        journal_id = "test_journal_123"
        entity_id = "test_entity_456"
        relationship_id = "test_relationship_789"
        
        post_endpoints = [
            f"/api/curation/entities/{journal_id}/complete",
            f"/api/curation/entities/{journal_id}/{entity_id}",
            f"/api/curation/relationships/{journal_id}/complete",
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            f"/api/curation/bulk/accept-all/{journal_id}"
        ]
        
        for endpoint in post_endpoints:
            response = client.post(endpoint, json={"action": "accept", "curated_data": {}})
            # Should not return 405 Method Not Allowed
            assert response.status_code != 405
