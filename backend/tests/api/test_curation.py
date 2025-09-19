import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from minerva_backend.api.main import backend_app, container
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.models import CurationStats, JournalEntryCuration


@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI application."""
    with TestClient(backend_app) as c:
        yield c


@pytest.fixture
def mock_curation_manager():
    """Mock for CurationManager."""
    return AsyncMock(spec=CurationManager)


def test_get_pending_curation_success(client, mock_curation_manager):
    """Test getting pending curation tasks successfully."""
    journal_entry_curation = JournalEntryCuration(journal_id="j1", date="2025-09-19", tasks=[])
    pending_tasks = [journal_entry_curation]
    stats = CurationStats(total_journals=1, pending_entities=1)

    mock_curation_manager.get_all_pending_curation_tasks.return_value = pending_tasks
    mock_curation_manager.get_curation_stats.return_value = stats

    with container.curation_manager.override(mock_curation_manager):
        response = client.get("/api/curation/pending")

    assert response.status_code == 200
    data = response.json()
    assert data["journal_entry"][0]["journal_id"] == "j1"
    assert data["stats"]["total_journals"] == 1
    assert data["stats"]["pending_entities"] == 1
    mock_curation_manager.get_all_pending_curation_tasks.assert_awaited_once()
    mock_curation_manager.get_curation_stats.assert_awaited_once()


def test_get_curation_stats_success(client, mock_curation_manager):
    """Test getting curation stats successfully."""
    stats_model = CurationStats(total_journals=1, pending_entities=1)
    mock_curation_manager.get_curation_stats.return_value = stats_model

    with container.curation_manager.override(mock_curation_manager):
        response = client.get("/api/curation/stats")

    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_journals"] == 1
    assert data["stats"]["pending_entities"] == 1
    mock_curation_manager.get_curation_stats.assert_awaited_once()


def test_handle_entity_curation_accept_success(client, mock_curation_manager):
    """Test accepting an entity curation successfully."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())
    curated_data = {"name": "Updated Name"}
    updated_uuid = str(uuid.uuid4())

    mock_curation_manager.accept_entity.return_value = updated_uuid

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json={"action": "accept", "curated_data": curated_data}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Entity accepted and updated"
    assert data["journal_id"] == journal_id
    assert data["data"]["entity_id"] == entity_id
    assert data["data"]["action"] == "accept"
    assert data["data"]["updated_uuid"] == updated_uuid

    mock_curation_manager.accept_entity.assert_awaited_once_with(
        journal_uuid=journal_id,
        entity_uuid=entity_id,
        curated_data=curated_data
    )


def test_handle_entity_curation_reject_success(client, mock_curation_manager):
    """Test rejecting an entity curation successfully."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())
    updated_uuid = str(uuid.uuid4())

    mock_curation_manager.reject_entity.return_value = updated_uuid

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json={"action": "reject"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Entity rejected"
    assert data["journal_id"] == journal_id
    assert data["data"]["entity_id"] == entity_id
    assert data["data"]["action"] == "reject"
    assert data["data"]["updated_uuid"] == updated_uuid

    mock_curation_manager.reject_entity.assert_awaited_once_with(
        journal_uuid=journal_id,
        entity_uuid=entity_id
    )


def test_handle_entity_curation_not_found(client, mock_curation_manager):
    """Test handling an entity curation when entity not found."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())

    mock_curation_manager.accept_entity.return_value = None  # Falsy for not found

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/entities/{journal_id}/{entity_id}",
            json={"action": "accept", "curated_data": {"name": "Test"}}
        )

    assert response.status_code == 404
    assert "Entity not found" in response.json()["detail"]


def test_handle_entity_curation_accept_validation_error(client):
    """Test accept entity curation with missing curated_data."""
    journal_id = str(uuid.uuid4())
    entity_id = str(uuid.uuid4())

    response = client.post(
        f"/api/curation/entities/{journal_id}/{entity_id}",
        json={"action": "accept"}  # Missing curated_data
    )
    assert response.status_code == 422  # Pydantic validation error


def test_complete_entity_curation_success(client, mock_curation_manager):
    """Test completing entity curation for a journal successfully."""
    journal_id = str(uuid.uuid4())

    mock_curation_manager.complete_entity_phase.return_value = None
    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/entities/{journal_id}/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Entity curation phase completed"
    assert data["journal_id"] == journal_id
    assert data["data"] == {"phase": "entity", "status": "completed"}
    mock_curation_manager.complete_entity_phase.assert_awaited_once_with(journal_id)


def test_handle_relationship_curation_accept_success(client, mock_curation_manager):
    """Test accepting a relationship curation successfully."""
    journal_id = str(uuid.uuid4())
    relationship_id = str(uuid.uuid4())
    curated_data = {"type": "UPDATED_RELATION"}
    updated_uuid = str(uuid.uuid4())

    mock_curation_manager.accept_relationship.return_value = updated_uuid

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            json={"action": "accept", "curated_data": curated_data}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Relationship accepted and updated"
    assert data["journal_id"] == journal_id
    assert data["data"]["relationship_id"] == relationship_id
    assert data["data"]["action"] == "accept"
    assert data["data"]["updated_uuid"] == updated_uuid

    mock_curation_manager.accept_relationship.assert_awaited_once_with(
        journal_uuid=journal_id,
        relationship_uuid=relationship_id,
        curated_data=curated_data
    )


def test_handle_relationship_curation_reject_success(client, mock_curation_manager):
    """Test rejecting a relationship curation successfully."""
    journal_id = str(uuid.uuid4())
    relationship_id = str(uuid.uuid4())
    updated_uuid = str(uuid.uuid4())

    mock_curation_manager.reject_relationship.return_value = updated_uuid

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            json={"action": "reject"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Relationship rejected"
    assert data["journal_id"] == journal_id
    assert data["data"]["relationship_id"] == relationship_id
    assert data["data"]["action"] == "reject"
    assert data["data"]["updated_uuid"] == updated_uuid

    mock_curation_manager.reject_relationship.assert_awaited_once_with(
        journal_uuid=journal_id,
        relationship_uuid=relationship_id
    )


def test_handle_relationship_curation_not_found(client, mock_curation_manager):
    """Test handling a relationship curation when relationship not found."""
    journal_id = str(uuid.uuid4())
    relationship_id = str(uuid.uuid4())

    mock_curation_manager.accept_relationship.return_value = None  # Falsy for not found

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(
            f"/api/curation/relationships/{journal_id}/{relationship_id}",
            json={"action": "accept", "curated_data": {"type": "Test"}}
        )

    assert response.status_code == 404
    assert "Relationship not found" in response.json()["detail"]


def test_complete_relationship_curation_success(client, mock_curation_manager):
    """Test completing relationship curation for a journal successfully."""
    journal_id = str(uuid.uuid4())

    mock_curation_manager.complete_relationship_phase.return_value = None
    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/relationships/{journal_id}/complete")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Relationship curation phase completed"
    assert data["journal_id"] == journal_id
    assert data["data"] == {"phase": "relationship", "status": "completed"}
    mock_curation_manager.complete_relationship_phase.assert_awaited_once_with(journal_id)


def test_bulk_accept_all_entity_success(client, mock_curation_manager):
    """Test bulk accepting all entity tasks for a journal."""
    journal_id = str(uuid.uuid4())
    # This endpoint currently has count = 0 hardcoded as the manager method is not implemented.
    # mock_curation_manager.bulk_accept_all.return_value = 5

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase=entity")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Bulk accepted 0 entity items"
    assert data["journal_id"] == journal_id
    assert data["data"]["phase"] == "entity"
    assert data["data"]["accepted_count"] == 0
    # mock_curation_manager.bulk_accept_all.assert_awaited_once_with(journal_id, "entity")


def test_bulk_accept_all_relationship_success(client, mock_curation_manager):
    """Test bulk accepting all relationship tasks for a journal."""
    journal_id = str(uuid.uuid4())

    with container.curation_manager.override(mock_curation_manager):
        response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase=relationship")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Bulk accepted 0 relationship items"
    assert data["data"]["phase"] == "relationship"


def test_bulk_accept_all_invalid_phase(client):
    """Test bulk accept with an invalid phase."""
    journal_id = str(uuid.uuid4())
    response = client.post(f"/api/curation/bulk/accept-all/{journal_id}?phase=invalid")
    assert response.status_code == 400
    assert "Phase must be 'entity' or 'relationship'" in response.json()["detail"]
