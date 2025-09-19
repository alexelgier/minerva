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


def test_get_all_pending_pipelines_success(client, mock_orchestrator):
    """Test getting all pending pipelines successfully (expecting empty list)."""
    mock_orchestrator.get_all_pending_curation.return_value = []  # This is actually for curation manager in code

    with container.pipeline_orchestrator.override(mock_orchestrator):
        response = client.get("/api/pipeline/all-pending")

    assert response.status_code == 200
    assert response.json() == {"pending_pipelines": []}


def test_start_processing_success(client):
    """Test starting processing manually."""
    response = client.post("/api/processing/start")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Processing started manually"}


def test_pause_processing_success(client):
    """Test pausing processing."""
    response = client.post("/api/processing/pause")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Processing paused"}


def test_get_processing_windows_success(client):
    """Test getting processing window configuration."""
    response = client.get("/api/processing/windows")
    assert response.status_code == 200
    data = response.json()
    assert "default_window" in data
    assert "currently_active" in data
    assert "next_window" in data
    assert data["default_window"]["start_time"] == "06:00"


def test_process_obsidian_note_success(client):
    """Test processing an Obsidian note."""
    note_path = "2023-01-01.md"
    response = client.post(f"/api/obsidian/process-note?note_path={note_path}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == f"Note {note_path} queued for processing"
    assert "workflow_id" in data
