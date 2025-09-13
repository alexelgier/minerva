"""
Comprehensive test suite for Minerva Neo4j CRUD operations.
Tests all entity types and relationship operations.
"""

import pytest
import uuid
from datetime import datetime, date
from minerva_backend.graph.db import (
    MinervaDatabase, Person, Feeling, Event, Project, Concept, Resource,
    JournalEntry, EntityType, RelationshipType
)


class TestMinervaDatabase:
    """Test suite for Minerva database operations."""

    @pytest.fixture(scope="class")
    def db(self):
        """Database connection fixture."""
        database = MinervaDatabase()
        yield database
        database.close()

    @pytest.fixture
    def sample_person(self):
        """Sample Person entity for testing."""
        return Person(
            id=str(uuid.uuid4()),
            full_name="Test User",
            aliases=["Tester", "TestUser"],
            occupation="Software Tester",
            relationship_type="colleague",
            mention_count=1,
            emotional_valence=0.5
        )

    @pytest.fixture
    def sample_feeling(self):
        """Sample Feeling entity for testing."""
        return Feeling(
            id=str(uuid.uuid4()),
            emotion_type="joy",
            intensity=7,
            timestamp=datetime.now(),
            duration_minutes=30,
            context="Test completion"
        )

    @pytest.fixture
    def sample_event(self):
        """Sample Event entity for testing."""
        return Event(
            id=str(uuid.uuid4()),
            title="Test Event",
            event_type="work",
            start_date=datetime.now(),
            location="Test Location",
            significance_level=5,
            emotional_impact=0.3,
            tags=["test", "work"]
        )

    @pytest.fixture
    def sample_project(self):
        """Sample Project entity for testing."""
        return Project(
            id=str(uuid.uuid4()),
            name="Test Project",
            description="A project for testing purposes",
            status="active",
            priority="medium",
            start_date=date.today(),
            progress_percentage=25.0
        )

    @pytest.fixture
    def sample_concept(self):
        """Sample Concept entity for testing."""
        return Concept(
            id=str(uuid.uuid4()),
            title="Test Concept",
            definition="A concept used for testing",
            category="testing",
            complexity_level=2,
            understanding_level=4,
            source_type="documentation"
        )

    @pytest.fixture
    def sample_resource(self):
        """Sample Resource entity for testing."""
        return Resource(
            id=str(uuid.uuid4()),
            title="Test Resource",
            type="documentation",
            author="Test Author",
            status="completed",
            rating=4,
            tags=["testing", "documentation"]
        )

    @pytest.fixture
    def sample_journal_entry(self):
        """Sample JournalEntry entity for testing."""
        return JournalEntry(
            id=str(uuid.uuid4()),
            date=date.today(),
            word_count=150,
            processing_status="completed",
            psychological_metrics={
                "panas_positive": 3.5,
                "panas_negative": 2.1
            },
            extraction_confidence=0.85
        )

    # =============================================================================
    # PERSON TESTS
    # =============================================================================

    def test_person_crud_operations(self, db, sample_person):
        """Test complete CRUD operations for Person entity."""
        # Create
        person_id = db.create_person(sample_person)
        assert person_id == sample_person.id

        # Read
        retrieved_person = db.get_person(person_id)
        assert retrieved_person is not None
        assert retrieved_person.full_name == sample_person.full_name
        assert retrieved_person.occupation == sample_person.occupation

        # Update
        updates = {"mention_count": 10, "emotional_valence": 0.8}
        success = db.update_person(person_id, updates)
        assert success is True

        # Verify update
        updated_person = db.get_person(person_id)
        assert updated_person.mention_count == 10
        assert updated_person.emotional_valence == 0.8

        # List
        persons = db.list_persons(limit=10)
        assert len(persons) > 0
        assert any(p.id == person_id for p in persons)

        # Delete
        success = db.delete_person(person_id)
        assert success is True

        # Verify deletion
        deleted_person = db.get_person(person_id)
        assert deleted_person is None

    # =============================================================================
    # FEELING TESTS
    # =============================================================================

    def test_feeling_crud_operations(self, db, sample_feeling):
        """Test complete CRUD operations for Feeling entity."""
        # Create
        feeling_id = db.create_feeling(sample_feeling)
        assert feeling_id == sample_feeling.id

        # Read
        retrieved_feeling = db.get_feeling(feeling_id)
        assert retrieved_feeling is not None
        assert retrieved_feeling.emotion_type == sample_feeling.emotion_type
        assert retrieved_feeling.intensity == sample_feeling.intensity

        # Update
        updates = {"intensity": 9, "duration_minutes": 45}
        success = db.update_feeling(feeling_id, updates)
        assert success is True

        # List
        feelings = db.list_feelings(limit=10)
        assert len(feelings) > 0

        # Delete
        success = db.delete_feeling(feeling_id)
        assert success is True

    # =============================================================================
    # EVENT TESTS
    # =============================================================================

    def test_event_crud_operations(self, db, sample_event):
        """Test complete CRUD operations for Event entity."""
        # Create
        event_id = db.create_event(sample_event)
        assert event_id == sample_event.id

        # Read
        retrieved_event = db.get_event(event_id)
        assert retrieved_event is not None
        assert retrieved_event.title == sample_event.title
        assert retrieved_event.event_type == sample_event.event_type

        # Update
        updates = {"significance_level": 8, "emotional_impact": 0.7}
        success = db.update_event(event_id, updates)
        assert success is True

        # List
        events = db.list_events(limit=10)
        assert len(events) > 0

        # Delete
        success = db.delete_event(event_id)
        assert success is True

    # =============================================================================
    # PROJECT TESTS
    # =============================================================================

    def test_project_crud_operations(self, db, sample_project):
        """Test complete CRUD operations for Project entity."""
        # Create
        project_id = db.create_project(sample_project)
        assert project_id == sample_project.id

        # Read
        retrieved_project = db.get_project(project_id)
        assert retrieved_project is not None
        assert retrieved_project.name == sample_project.name
        assert retrieved_project.status == sample_project.status

        # Update
        updates = {"progress_percentage": 75.0, "status": "completed"}
        success = db.update_project(project_id, updates)
        assert success is True

        # List
        projects = db.list_projects(limit=10)
        assert len(projects) > 0

        # Delete
        success = db.delete_project(project_id)
        assert success is True

    # =============================================================================
    # CONCEPT TESTS
    # =============================================================================

    def test_concept_crud_operations(self, db, sample_concept):
        """Test complete CRUD operations for Concept entity."""
        # Create
        concept_id = db.create_concept(sample_concept)
        assert concept_id == sample_concept.id

        # Read
        retrieved_concept = db.get_concept(concept_id)
        assert retrieved_concept is not None
        assert retrieved_concept.title == sample_concept.title
        assert retrieved_concept.category == sample_concept.category

        # Update
        updates = {"understanding_level": 5, "complexity_level": 3}
        success = db.update_concept(concept_id, updates)
        assert success is True

        # List
        concepts = db.list_concepts(limit=10)
        assert len(concepts) > 0

        # Delete
        success = db.delete_concept(concept_id)
        assert success is True

    # =============================================================================
    # RESOURCE TESTS
    # =============================================================================

    def test_resource_crud_operations(self, db, sample_resource):
        """Test complete CRUD operations for Resource entity."""
        # Create
        resource_id = db.create_resource(sample_resource)
        assert resource_id == sample_resource.id

        # Read
        retrieved_resource = db.get_resource(resource_id)
        assert retrieved_resource is not None
        assert retrieved_resource.title == sample_resource.title
        assert retrieved_resource.type == sample_resource.type

        # Update
        updates = {"rating": 5, "status": "recommended"}
        success = db.update_resource(resource_id, updates)
        assert success is True

        # List
        resources = db.list_resources(limit=10)
        assert len(resources) > 0

        # Delete
        success = db.delete_resource(resource_id)
        assert success is True

    # =============================================================================
    # JOURNAL ENTRY TESTS
    # =============================================================================

    def test_journal_entry_crud_operations(self, db, sample_journal_entry):
        """Test complete CRUD operations for JournalEntry entity."""
        # Create
        entry_id = db.create_journal_entry(sample_journal_entry)
        assert entry_id == sample_journal_entry.id

        # Read
        retrieved_entry = db.get_journal_entry(entry_id)
        assert retrieved_entry is not None
        assert retrieved_entry.date == sample_journal_entry.date
        assert retrieved_entry.word_count == sample_journal_entry.word_count

        # Update
        updates = {"processing_status": "reviewed", "word_count": 200}
        success = db.update_journal_entry(entry_id, updates)
        assert success is True

        # List
        entries = db.list_journal_entries(limit=10)
        assert len(entries) > 0

        # Delete
        success = db.delete_journal_entry(entry_id)
        assert success is True

    # =============================================================================
    # RELATIONSHIP TESTS
    # =============================================================================

    def test_relationship_operations(self, db, sample_person, sample_feeling):
        """Test relationship creation and management."""
        # Create entities first
        person_id = db.create_person(sample_person)
        feeling_id = db.create_feeling(sample_feeling)

        # Create relationship
        success = db.create_relationship(
            person_id, feeling_id,
            RelationshipType.FEELS,
            {"intensity": 7, "context": "test relationship"}
        )
        assert success is True

        # Get relationships
        relationships = db.get_entity_relationships(person_id)
        assert len(relationships) > 0

        # Verify relationship properties
        rel = relationships[0]
        assert rel["relationship_type"] == RelationshipType.FEELS.value
        assert rel["properties"]["intensity"] == 7

        # Delete relationship
        success = db.delete_relationship(person_id, feeling_id, RelationshipType.FEELS)
        assert success is True

        # Cleanup
        db.delete_person(person_id)
        db.delete_feeling(feeling_id)

    # =============================================================================
    # UTILITY TESTS
    # =============================================================================

    def test_database_stats(self, db):
        """Test database statistics functionality."""
        stats = db.get_database_stats()

        assert "total_nodes" in stats
        assert "total_relationships" in stats
        assert "entity_counts" in stats
        assert "relationship_counts" in stats
        assert isinstance(stats["total_nodes"], int)
        assert isinstance(stats["total_relationships"], int)

    def test_search_functionality(self, db, sample_person):
        """Test entity search functionality."""
        # Create a person to search for
        person_id = db.create_person(sample_person)

        # Search for the person
        results = db.search_entities("Test User", [EntityType.PERSON])
        assert len(results) > 0

        # Verify search result
        found = any(result["id"] == person_id for result in results)
        assert found is True

        # Cleanup
        db.delete_person(person_id)

    def test_connection_and_cleanup(self, db):
        """Test database connection and proper cleanup."""
        # Test that we can get stats (verifies connection)
        stats = db.get_database_stats()
        assert stats is not None

        # Test connection close
        db.close()

        # Reconnect for other tests
        db.__init__()


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for complex scenarios."""

    @pytest.fixture(scope="class")
    def db(self):
        """Database connection fixture."""
        database = MinervaDatabase()
        yield database
        database.close()

    def test_complete_journal_workflow(self, db):
        """Test a complete journal processing workflow."""
        # Create a journal entry
        journal_entry = JournalEntry(
            id=str(uuid.uuid4()),
            date=date.today(),
            word_count=300,
            processing_status="processing"
        )
        entry_id = db.create_journal_entry(journal_entry)

        # Create related entities
        person = Person(
            id=str(uuid.uuid4()),
            full_name="Journal Test Person",
            relationship_type="friend"
        )
        person_id = db.create_person(person)

        feeling = Feeling(
            id=str(uuid.uuid4()),
            emotion_type="gratitude",
            intensity=8,
            timestamp=datetime.now(),
            journal_entry_id=entry_id
        )
        feeling_id = db.create_feeling(feeling)

        event = Event(
            id=str(uuid.uuid4()),
            title="Coffee with friend",
            event_type="social",
            start_date=datetime.now()
        )
        event_id = db.create_event(event)

        # Create relationships
        db.create_relationship(entry_id, person_id, RelationshipType.MENTIONS)
        db.create_relationship(entry_id, feeling_id, RelationshipType.CONTAINS)
        db.create_relationship(entry_id, event_id, RelationshipType.MENTIONS)
        db.create_relationship(person_id, feeling_id, RelationshipType.FEELS)
        db.create_relationship(person_id, event_id, RelationshipType.PARTICIPATES_IN)

        # Verify the complete network
        entry_relationships = db.get_entity_relationships(entry_id)
        assert len(entry_relationships) >= 3

        person_relationships = db.get_entity_relationships(person_id)
        assert len(person_relationships) >= 3

        # Update journal entry status
        db.update_journal_entry(entry_id, {"processing_status": "completed"})
        updated_entry = db.get_journal_entry(entry_id)
        assert updated_entry.processing_status == "completed"

        # Cleanup
        db.delete_journal_entry(entry_id)
        db.delete_person(person_id)
        db.delete_feeling(feeling_id)
        db.delete_event(event_id)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])