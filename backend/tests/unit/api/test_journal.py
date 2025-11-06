"""
Unit tests for journal API endpoints.

Tests the journal submission and validation endpoints with mocked dependencies.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

from minerva_backend.api.main import backend_app
from minerva_backend.api.models import JournalSubmission


@pytest.fixture
def client(test_container):
    """Create test client with mocked dependencies."""
    # Set the container in the app state
    backend_app.state.container = test_container
    
    # Wire the dependencies for the API module
    test_container.wire(modules=["minerva_backend.api.dependencies"])
    
    # Create TestClient - this will trigger startup event with test container
    return TestClient(backend_app)


class TestJournalSubmission:
    """Test journal submission endpoint."""
    
    def test_submit_journal_success(self, client, sample_journal_entry, mock_pipeline_orchestrator, test_container):
        """Test successful journal submission."""
        # Arrange
        submission_data = {
            "text": sample_journal_entry.text,
            "date": "2025-09-15"
        }
        
        # Act
        response = client.post("/api/journal/submit", json=submission_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_id" in data
        assert "journal_id" in data
        assert data["message"] == "Journal submitted for processing"
        
        # Verify orchestrator was called
        mock_pipeline_orchestrator.submit_journal.assert_called_once()
    
    def test_submit_journal_validation_error(self, client):
        """Test journal submission with validation error."""
        # Arrange
        invalid_data = {
            "text": "",  # Empty text should fail validation
            "date": "invalid-date"
        }
        
        # Act
        response = client.post("/api/journal/submit", json=invalid_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
    
    def test_submit_journal_processing_error(self, client, sample_journal_entry, mock_pipeline_orchestrator):
        """Test journal submission with processing error."""
        # Arrange
        mock_pipeline_orchestrator.submit_journal.side_effect = Exception("Processing failed")
        submission_data = {
            "text": sample_journal_entry.text,
            "date": "2025-09-15"
        }
        
        # Act
        response = client.post("/api/journal/submit", json=submission_data)
        
        # Assert
        assert response.status_code == 422  # ProcessingError is handled as 422
        data = response.json()
        # Check that we get an error response (structure may vary)
        assert "detail" in data or "error" in data
    
    def test_validate_journal_format_success(self, client, sample_journal_entry):
        """Test journal format validation success."""
        # Arrange
        text = "Today I worked on Minerva all day."
        date = "2025-09-15"
        
        # Act
        response = client.get(f"/api/journal/validate?text={text}&date={date}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "word_count" in data["data"]
        assert "character_count" in data["data"]
    
    def test_validate_journal_format_invalid(self, client):
        """Test journal format validation with invalid data."""
        # Arrange
        text = "Invalid format"
        date = "invalid-date"
        
        # Act
        response = client.get(f"/api/journal/validate?text={text}&date={date}")
        
        # Assert
        assert response.status_code == 422  # Validation error (Pydantic validation)


class TestJournalEndpoints:
    """Test journal endpoint functionality."""
    
    def test_journal_endpoints_exist(self, client):
        """Test that journal endpoints are properly registered."""
        # Test that endpoints exist by checking OpenAPI JSON
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        paths = openapi_data.get("paths", {})
        
        # Test that journal endpoints are registered
        assert "/api/journal/submit" in paths
        assert "/api/journal/validate" in paths
