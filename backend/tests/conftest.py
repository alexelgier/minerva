import pytest
import uuid
from datetime import datetime, date

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import (
    Person, Feeling, Event, Project, Concept, Consumable, Content, Emotion, ProjectStatus, ResourceType, ResourceStatus
)
from minerva_backend.graph.models.enums import EmotionType
from minerva_backend.graph.repositories import (
    PersonRepository, FeelingRepository, EventRepository, ProjectRepository,
    ConceptRepository, ContentRepository, ConsumableRepository,
    EmotionRepository, JournalEntryRepository
)


@pytest.fixture(scope="session")
def db_connection():
    """Database connection fixture for the entire test session."""
    conn = Neo4jConnection()
    yield conn
    conn.close()


@pytest.fixture
def person_repo(db_connection):
    return PersonRepository(db_connection)


@pytest.fixture
def feeling_repo(db_connection):
    return FeelingRepository(db_connection)


@pytest.fixture
def event_repo(db_connection):
    return EventRepository(db_connection)


@pytest.fixture
def project_repo(db_connection):
    return ProjectRepository(db_connection)


@pytest.fixture
def concept_repo(db_connection):
    return ConceptRepository(db_connection)


@pytest.fixture
def content_repo(db_connection):
    return ContentRepository(db_connection)


@pytest.fixture
def consumable_repo(db_connection):
    return ConsumableRepository(db_connection)


@pytest.fixture
def emotion_repo(db_connection):
    return EmotionRepository(db_connection)


@pytest.fixture
def journal_entry_repo(db_connection):
    return JournalEntryRepository(db_connection)


@pytest.fixture
def sample_person():
    """Sample Person entity for testing."""
    return Person(
        name="Test User " + str(uuid.uuid4()),  # Add UUID to ensure uniqueness
        aliases=["Tester", "TestUser"],
        occupation="Software Tester"
    )


@pytest.fixture
def sample_feeling():
    """Sample Feeling entity for testing."""
    return Feeling(
        name="Joy " + str(uuid.uuid4()),
        intensity=7,
        context="Test completion"
    )

@pytest.fixture
def sample_emotion():
    """Sample Emotion entity for testing."""
    return Emotion(
        name="Happiness " + str(uuid.uuid4()),
        emotion_type=EmotionType.JOY
    )


@pytest.fixture
def sample_event():
    """Sample Event entity for testing."""
    return Event(
        name="Test Event " + str(uuid.uuid4()),
        event_type="work",
        start_date=datetime.now(),
        location="Test Location",
        tags=["test", "work"]
    )


@pytest.fixture
def sample_project():
    """Sample Project entity for testing."""
    return Project(
        name="Test Project " + str(uuid.uuid4()),
        description="A project for testing purposes",
        status=ProjectStatus.ACTIVE,
        start_date=date.today()
    )


@pytest.fixture
def sample_concept():
    """Sample Concept entity for testing."""
    return Concept(
        name="Test Concept " + str(uuid.uuid4()),
        definition="A concept used for testing",
        category="testing"
    )


@pytest.fixture
def sample_content():
    """Sample Content entity for testing."""
    return Content(
        name="Test Content " + str(uuid.uuid4()),
        resource_type=ResourceType.DOCUMENTATION,
        author="Test Author",
        status=ResourceStatus.COMPLETED,
        rating=4,
        tags=["testing", "documentation"]
    )


@pytest.fixture
def sample_consumable():
    """Sample Consumable entity for testing."""
    return Consumable(
        name="Test Consumable " + str(uuid.uuid4()),
        type="article",
        source="web"
    )


@pytest.fixture
def sample_journal_entry():
    """Sample JournalEntry document for testing."""
    return JournalEntry(
        text="This is a test journal entry.",
        date=date.today()
    )
