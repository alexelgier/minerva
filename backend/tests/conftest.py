"""
Pytest configuration and shared fixtures for Minerva Backend tests.

This module provides common fixtures, test configuration, and utilities
for both unit and integration tests.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest

from minerva_backend.containers import Container
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.utils.logging import setup_logging

from .fixtures.entity_factory import EntityFactory
from .fixtures.journal_factory import JournalEntryFactory
from .utils.database import TestDatabaseManager, check_neo4j_availability
from .utils.ollama import check_ollama_availability

# Configure logging for tests - DISABLED for unit tests
# setup_logging()  # Commented out to prevent real logging in tests
logger = logging.getLogger(__name__)


# ============================================================================
# Test isolation fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def disable_logging():
    """Disable all logging during tests to prevent log file writes."""
    # Disable all logging
    logging.disable(logging.CRITICAL)
    
    # Also disable specific loggers that might be used
    for logger_name in ['minerva_backend', 'minerva_backend.graph', 'minerva_backend.processing', 'minerva_backend.api']:
        logging.getLogger(logger_name).disabled = True
    
    yield
    
    # Re-enable logging after test
    logging.disable(logging.NOTSET)
    for logger_name in ['minerva_backend', 'minerva_backend.graph', 'minerva_backend.processing', 'minerva_backend.api']:
        logging.getLogger(logger_name).disabled = False


# ============================================================================
# Session-level fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def neo4j_available() -> bool:
    """Check if Neo4j is available for integration tests."""
    return check_neo4j_availability()


@pytest.fixture(scope="session")
async def ollama_available() -> bool:
    """Check if Ollama is available for integration tests."""
    return await check_ollama_availability()


# ============================================================================
# Database fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_manager() -> Generator[TestDatabaseManager, None, None]:
    """Fixture for test database management."""
    manager = TestDatabaseManager()
    try:
        manager.setup_connection()
        yield manager
    finally:
        manager.close()


@pytest.fixture(scope="function")
def clean_test_db(test_db_manager: TestDatabaseManager) -> Generator[TestDatabaseManager, None, None]:
    """Fixture that provides a clean test database for each test."""
    test_db_manager.setup_test_database()
    yield test_db_manager


@pytest.fixture(scope="function")
def neo4j_connection(clean_test_db: TestDatabaseManager) -> Neo4jConnection:
    """Fixture that provides a clean Neo4j connection for testing."""
    return clean_test_db.connection


@pytest.fixture(scope="function")
def emotions_dict(clean_test_db: TestDatabaseManager) -> dict:
    """Fixture that provides initialized emotion types."""
    return clean_test_db.initialize_emotions()


# ============================================================================
# Mock fixtures for unit tests
# ============================================================================

@pytest.fixture
def mock_neo4j_connection():
    """Mock Neo4j connection for unit testing."""
    mock_connection = Mock(spec=Neo4jConnection)
    mock_connection.health_check = AsyncMock(return_value=True)
    
    # Mock async session context manager
    mock_session = AsyncMock()
    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__ = AsyncMock(return_value=mock_session)
    mock_context_manager.__aexit__ = AsyncMock(return_value=None)
    mock_connection.session_async = Mock(return_value=mock_context_manager)
    
    return mock_connection


@pytest.fixture
def mock_curation_manager():
    """Mock curation manager for unit testing."""
    mock_manager = Mock(spec=CurationManager)
    mock_manager.initialize = AsyncMock()
    mock_manager.get_all_pending_curation_tasks = AsyncMock(return_value=[])
    # Import CurationStats for proper mocking
    from minerva_backend.processing.models import CurationStats
    mock_manager.get_curation_stats = AsyncMock(return_value=CurationStats(
        pending_entities=0,
        pending_relationships=0,
        completed=0
    ))
    mock_manager.queue_entities_for_curation = AsyncMock()
    mock_manager.queue_relationships_for_curation = AsyncMock()
    mock_manager.get_journal_status = AsyncMock(return_value="COMPLETED")
    mock_manager.get_accepted_entities_with_spans = AsyncMock(return_value=[])
    mock_manager.get_accepted_relationships_with_spans = AsyncMock(return_value=[])
    # Add curation action methods
    mock_manager.accept_entity = AsyncMock(return_value="new_uuid_123")
    mock_manager.reject_entity = AsyncMock(return_value=True)
    mock_manager.accept_relationship = AsyncMock(return_value="new_uuid_456")
    mock_manager.reject_relationship = AsyncMock(return_value=True)
    mock_manager.complete_entity_phase = AsyncMock()
    mock_manager.complete_relationship_phase = AsyncMock()
    return mock_manager


@pytest.fixture
def mock_pipeline_orchestrator():
    """Mock pipeline orchestrator for unit testing."""
    mock_orchestrator = Mock(spec=PipelineOrchestrator)
    mock_orchestrator.initialize = AsyncMock()
    mock_orchestrator.submit_journal = AsyncMock(return_value="test-workflow-id")
    mock_orchestrator.get_pipeline_status = AsyncMock(return_value={
        "status": "COMPLETED",
        "stage": "DB_WRITE",
        "created_at": "2024-01-15T10:00:00Z"
    })
    return mock_orchestrator


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for unit testing."""
    mock_llm = Mock(spec=LLMService)
    mock_llm.generate = AsyncMock(return_value={
        "entities": [
            {"name": "John", "type": "Person", "summary": "A friend"}
        ]
    })
    return mock_llm


@pytest.fixture
def mock_obsidian_service():
    """Mock Obsidian service for unit testing."""
    mock_obsidian = Mock(spec=ObsidianService)
    mock_obsidian.get_entity_by_name = Mock(return_value=None)
    mock_obsidian.get_entities_by_type = Mock(return_value=[])
    mock_obsidian.resolve_link = Mock(return_value=Mock(
        file_path=None,
        entity_name="Test Entity",
        entity_long_name="Test Entity",
        entity_id=None,
        entity_type=None,
        aliases=None,
        display_text="Test Entity",
        short_summary=None
    ))
    mock_obsidian.update_link = Mock(return_value=True)
    
    # Add methods that tests are calling - these will be configured per test
    mock_obsidian.parse_conexiones_section = Mock(return_value={})
    mock_obsidian.validate_relation_consistency = Mock(return_value=[])
    mock_obsidian.update_conexiones_section = Mock(return_value=True)
    mock_obsidian.get_zettel_directory = Mock(return_value="/test/vault/08 - Ideas")
    mock_obsidian.find_zettel_files = Mock(return_value=[])
    mock_obsidian.parse_zettel_content = Mock(return_value={})
    mock_obsidian.parse_zettel_sections = Mock(return_value={})
    mock_obsidian.sync_zettels_to_db = AsyncMock(return_value=Mock(
        parsed=0, created=0, updated=0, unchanged=0, errors=0, 
        errors_list=[], missing_concepts=[], relations_created=0,
        relations_updated=0, self_connections_removed=0,
        inconsistent_relations=[], relations_deleted=0
    ))
    mock_obsidian.find_orphaned_relations = Mock(return_value=[])
    mock_obsidian._get_reverse_relation_type = Mock(return_value="SPECIFIC_OF")
    mock_obsidian.cleanup_orphaned_relations = AsyncMock(return_value=Mock(
        relations_deleted=0
    ))
    
    # Add attributes that tests expect
    mock_obsidian.vault_path = "/test/vault"
    mock_obsidian.llm_service = Mock()
    mock_obsidian.concept_repository = Mock()
    
    return mock_obsidian


# ============================================================================
# Additional mock fixtures for complete isolation
# ============================================================================

@pytest.fixture
def mock_kg_service():
    """Mock Knowledge Graph service for unit testing."""
    mock_kg = Mock()
    mock_kg.add_journal_entry = AsyncMock(return_value="test-journal-uuid")
    mock_kg.get_entity_by_name = AsyncMock(return_value=None)
    mock_kg.create_entity = AsyncMock(return_value="test-entity-uuid")
    mock_kg.update_entity = AsyncMock(return_value="test-entity-uuid")
    mock_kg.delete_entity = AsyncMock(return_value=True)
    mock_kg.create_relationship = AsyncMock(return_value="test-relation-uuid")
    mock_kg.update_relationship = AsyncMock(return_value="test-relation-uuid")
    mock_kg.delete_relationship = AsyncMock(return_value=True)
    return mock_kg


@pytest.fixture
def mock_extraction_service():
    """Mock Extraction service for unit testing."""
    mock_extraction = Mock()
    mock_extraction.extract_entities = AsyncMock(return_value=[])
    mock_extraction.extract_relationships = AsyncMock(return_value=[])
    return mock_extraction


@pytest.fixture
def mock_emotions_dict():
    """Mock emotions dictionary for unit testing."""
    return {
        "happy": "positive",
        "sad": "negative",
        "angry": "negative",
        "excited": "positive",
        "calm": "neutral"
    }


# Repository mock fixtures
@pytest.fixture
def mock_journal_entry_repository():
    """Mock Journal Entry repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-journal-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-journal-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_temporal_repository():
    """Mock Temporal repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create_workflow = AsyncMock(return_value="test-workflow-uuid")
    mock_repo.get_workflow_status = AsyncMock(return_value=None)
    mock_repo.update_workflow_status = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_relation_repository():
    """Mock Relation repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-relation-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-relation-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_person_repository():
    """Mock Person repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-person-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-person-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    mock_repo.find_by_name = AsyncMock(return_value=None)
    return mock_repo


@pytest.fixture
def mock_feeling_repository():
    """Mock Feeling repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-feeling-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-feeling-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_emotion_repository():
    """Mock Emotion repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-emotion-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-emotion-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_event_repository():
    """Mock Event repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-event-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-event-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_project_repository():
    """Mock Project repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-project-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-project-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_concept_repository():
    """Mock Concept repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-concept-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-concept-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    mock_repo.find_by_name = AsyncMock(return_value=None)
    mock_repo.find_concept_by_name_or_title = AsyncMock(return_value=None)
    mock_repo.get_concept_relations = AsyncMock(return_value=[])
    mock_repo.delete_concept_relation = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture
def mock_content_repository():
    """Mock Content repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-content-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-content-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_consumable_repository():
    """Mock Consumable repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-consumable-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-consumable-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_place_repository():
    """Mock Place repository for unit testing."""
    mock_repo = Mock()
    mock_repo.create = AsyncMock(return_value="test-place-uuid")
    mock_repo.get_by_id = AsyncMock(return_value=None)
    mock_repo.update = AsyncMock(return_value="test-place-uuid")
    mock_repo.delete = AsyncMock(return_value=True)
    mock_repo.vector_search = AsyncMock(return_value=[])
    return mock_repo


@pytest.fixture
def mock_entity_repositories():
    """Mock entity repositories dictionary for unit testing."""
    return {
        "Person": Mock(),
        "Feeling": Mock(),
        "Emotion": Mock(),
        "Event": Mock(),
        "Project": Mock(),
        "Concept": Mock(),
        "Content": Mock(),
        "Consumable": Mock(),
        "Place": Mock(),
    }


@pytest.fixture
def test_container(
    # Core service mocks
    mock_neo4j_connection,
    mock_curation_manager,
    mock_pipeline_orchestrator,
    mock_llm_service,
    mock_obsidian_service,
    mock_kg_service,
    mock_extraction_service,
    # Repository mocks
    mock_journal_entry_repository,
    mock_temporal_repository,
    mock_relation_repository,
    mock_person_repository,
    mock_feeling_repository,
    mock_emotion_repository,
    mock_event_repository,
    mock_project_repository,
    mock_concept_repository,
    mock_content_repository,
    mock_consumable_repository,
    mock_place_repository,
    # Dictionary mocks
    mock_entity_repositories,
    mock_emotions_dict,
):
    """Test container with complete isolation - ALL providers mocked."""
    container = Container()
    
    # Override Singleton providers (core services)
    container.db_connection.override(mock_neo4j_connection)
    container.curation_manager.override(mock_curation_manager)
    container.pipeline_orchestrator.override(mock_pipeline_orchestrator)
    container.llm_service.override(mock_llm_service)
    container.obsidian_service.override(mock_obsidian_service)
    container.kg_service.override(mock_kg_service)
    container.extraction_service.override(mock_extraction_service)
    
    # Override Factory providers (repositories)
    container.journal_entry_repository.override(mock_journal_entry_repository)
    container.temporal_repository.override(mock_temporal_repository)
    container.relation_repository.override(mock_relation_repository)
    container.person_repository.override(mock_person_repository)
    container.feeling_emotion_repository.override(mock_feeling_repository)
    container.feeling_concept_repository.override(mock_feeling_repository)
    container.emotion_repository.override(mock_emotion_repository)
    container.event_repository.override(mock_event_repository)
    container.project_repository.override(mock_project_repository)
    container.concept_repository.override(mock_concept_repository)
    container.content_repository.override(mock_content_repository)
    container.consumable_repository.override(mock_consumable_repository)
    container.place_repository.override(mock_place_repository)
    
    # Override Dict providers
    container.entity_repositories.override(mock_entity_repositories)
    
    # Override computed values
    container.emotions_dict.override(mock_emotions_dict)
    
    return container


# ============================================================================
# Data factory fixtures
# ============================================================================

@pytest.fixture
def journal_factory():
    """Factory for creating journal entries."""
    return JournalEntryFactory


@pytest.fixture
def entity_factory():
    """Factory for creating entities."""
    return EntityFactory


@pytest.fixture
def sample_journal_entry(journal_factory):
    """Sample journal entry for testing."""
    return journal_factory.create_minimal_journal_entry()


@pytest.fixture
def sample_entities(entity_factory):
    """Sample entities for testing."""
    return entity_factory.create_entity_set()


@pytest.fixture
def sample_person(entity_factory):
    """Sample person entity."""
    return entity_factory.create_person()


@pytest.fixture
def sample_place(entity_factory):
    """Sample place entity."""
    return entity_factory.create_place()


@pytest.fixture
def sample_project(entity_factory):
    """Sample project entity."""
    return entity_factory.create_project()


# ============================================================================
# Temporary file fixtures
# ============================================================================

@pytest.fixture
def temp_curation_db():
    """Create a temporary curation database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        db_path = tmp_file.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


# ============================================================================
# Test markers and configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: Unit tests that use mocks"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real dependencies"
    )
    config.addinivalue_line(
        "markers", "database: Tests that require database"
    )
    config.addinivalue_line(
        "markers", "ollama: Tests that require Ollama"
    )
    config.addinivalue_line(
        "markers", "temporal: Tests that require Temporal"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items based on external service availability."""
    # Check Neo4j availability
    neo4j_available = check_neo4j_availability()
    
    # Check Ollama availability (synchronously)
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ollama_available = loop.run_until_complete(check_ollama_availability())
        loop.close()
    except Exception:
        ollama_available = False
    
    # Mark tests that require external services
    for item in items:
        if "database" in item.keywords and not neo4j_available:
            item.add_marker(pytest.mark.skip(reason="Neo4j not available"))
        
        if "ollama" in item.keywords and not ollama_available:
            item.add_marker(pytest.mark.skip(reason="Ollama not available"))
        
        if "integration" in item.keywords and not (neo4j_available and ollama_available):
            item.add_marker(pytest.mark.skip(reason="Required services not available"))


# ============================================================================
# Async test utilities
# ============================================================================

@pytest.fixture
async def async_test_database():
    """Async context manager for test database operations."""
    from .utils.database import async_test_database
    async with async_test_database() as manager:
        yield manager


@pytest.fixture
def real_obsidian_service(test_container):
    """Real ObsidianService for testing with mocked dependencies."""
    from minerva_backend.obsidian.obsidian_service import ObsidianService
    return ObsidianService(
        vault_path="/tmp/minerva_test_vault",  # Test-specific vault path
        llm_service=test_container.llm_service(),
        concept_repository=test_container.concept_repository()
    )