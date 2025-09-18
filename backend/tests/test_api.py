import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from minerva_backend.api.main import backend_app, container
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator, PipelineState, PipelineStage


@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI application."""
    with TestClient(backend_app) as c:
        yield c


@pytest.fixture
def mock_orchestrator():
    """Mock for PipelineOrchestrator."""
    return AsyncMock(spec=PipelineOrchestrator)


@pytest.fixture
def mock_curation_manager():
    """Mock for CurationManager."""
    return AsyncMock(spec=CurationManager)


@pytest.fixture
def mock_db_connection():
    """Mock for Neo4jConnection."""
    return MagicMock(spec=Neo4jConnection)


def test_health_check_healthy(client, mock_db_connection, mock_curation_manager):
    """Test health check endpoint when all services are healthy."""
    mock_db_connection.health_check.return_value = True
    mock_curation_manager.get_curation_stats.return_value = {"pending": 0, "completed": 0}

    with container.db_connection.override(mock_db_connection), \
         container.curation_manager.override(mock_curation_manager):
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["services"]["neo4j_db"] == "healthy"
    mock_db_connection.health_check.assert_called_once()
    mock_curation_manager.get_curation_stats.assert_awaited_once()


def test_health_check_unhealthy(client, mock_db_connection, mock_curation_manager):
    """Test health check endpoint when database is unhealthy."""
    mock_db_connection.health_check.return_value = False
    mock_curation_manager.get_curation_stats.return_value = {"pending": 0, "completed": 0}

    with container.db_connection.override(mock_db_connection), \
         container.curation_manager.override(mock_curation_manager):
        response = client.get("/api/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["services"]["neo4j_db"] == "unhealthy"


def test_submit_journal_success(client, mock_orchestrator):
    """Test successful journal submission."""
    today = date.today().isoformat()
    journal_data = {"date": today, "text": "This is a test entry."}
    workflow_id = str(uuid.uuid4())

    mock_status = MagicMock(spec=PipelineState)
    mock_status.model_dump.return_value = {"stage": "SUBMITTED"}
    mock_status.stage = PipelineStage.SUBMITTED
    mock_orchestrator.submit_journal.return_value = workflow_id
    mock_orchestrator.get_pipeline_status.return_value = mock_status

    with container.pipeline_orchestrator.override(mock_orchestrator):
        response = client.post("/api/journal/submit", json=journal_data)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["workflow_id"] == workflow_id
    assert "journal_id" in data
    mock_orchestrator.submit_journal.assert_awaited_once()
    call_args = mock_orchestrator.submit_journal.call_args[0][0]
    assert isinstance(call_args, JournalEntry)
    assert call_args.text == journal_data["text"]
    mock_orchestrator.get_pipeline_status.assert_awaited_once_with(workflow_id)


def test_get_pipeline_status_success(client, mock_orchestrator):
    """Test getting pipeline status successfully."""
    workflow_id = str(uuid.uuid4())
    status_dict = {"stage": "ENTITY_CURATION", "progress": 50}

    mock_pipeline_status = MagicMock(spec=PipelineState)
    mock_pipeline_status.model_dump.return_value = status_dict
    mock_orchestrator.get_pipeline_status.return_value = mock_pipeline_status

    with container.pipeline_orchestrator.override(mock_orchestrator):
        response = client.get(f"/api/pipeline/status/{workflow_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["workflow_id"] == workflow_id
    assert data["status"] == status_dict
    mock_orchestrator.get_pipeline_status.assert_awaited_once_with(workflow_id)


def test_get_curation_stats_success(client, mock_curation_manager):
    """Test getting curation stats successfully."""
    stats = {"pending_entities": 5, "pending_relationships": 3}
    mock_curation_manager.get_curation_stats.return_value = stats

    with container.curation_manager.override(mock_curation_manager):
        response = client.get("/api/curation/stats")

    assert response.status_code == 200
    assert response.json() == stats
    mock_curation_manager.get_curation_stats.assert_awaited_once()


def test_accept_entity_curation_success(client, mock_curation_manager):
    """Test accepting an entity curation successfully."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())
    curated_data = {"name": "Updated Name"}

    mock_curation_manager.accept_entity.return_value = str(uuid.uuid4())

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/entities/{journal_id}/{entity_id}/accept", json=curated_data)

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Entity accepted"}
    mock_curation_manager.accept_entity.assert_awaited_once_with(
        journal_uuid=journal_id,
        entity_uuid=entity_id,
        curated_data=curated_data
    )


def test_reject_entity_curation_success(client, mock_curation_manager):
    """Test rejecting an entity curation successfully."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())

    mock_curation_manager.reject_entity.return_value = True

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/entities/{journal_id}/{entity_id}/reject")

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Entity rejected"}
    mock_curation_manager.reject_entity.assert_awaited_once_with(
        journal_uuid=journal_id,
        entity_uuid=entity_id
    )


def test_complete_entity_curation_success(client, mock_curation_manager):
    """Test completing entity curation for a journal successfully."""
    journal_id = str(uuid.uuid4())

    mock_curation_manager.complete_entity_phase.return_value = None
    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/entities/{journal_id}/complete")

    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Entity curation completed"}
    mock_curation_manager.complete_entity_phase.assert_awaited_once_with(journal_id)
