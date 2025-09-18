import pytest
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.graph.models.relations import Relation, RelationshipType


@pytest.fixture
def kg_service(db_connection):
    return KnowledgeGraphService(db_connection)


def test_relationship_operations(kg_service, person_repo, feeling_repo, sample_person, sample_feeling):
    """Test relationship creation and management via the service."""
    # Create entities first
    person_uuid = person_repo.create(sample_person)
    feeling_uuid = feeling_repo.create(sample_feeling)

    # Create relationship
    relation = Relation(
        source_uuid=person_uuid,
        target_uuid=feeling_uuid,
        type=RelationshipType.FEELS,
        properties={"intensity": 7, "context": "test relationship"}
    )
    assert kg_service.create_relationship(relation)

    # Get relationships (assuming a method exists on the service)
    relationships = kg_service.get_relationships(person_uuid)
    assert len(relationships) > 0

    # Verify relationship properties
    rel = relationships[0]
    assert rel.type == RelationshipType.FEELS
    assert rel.properties["intensity"] == 7

    # Delete relationship
    assert kg_service.delete_relationship(relation)

    # Cleanup
    person_repo.delete(person_uuid)
    feeling_repo.delete(feeling_uuid)


def test_database_stats(kg_service):
    """Test database statistics functionality."""
    stats = kg_service.get_database_stats()

    assert "node_count" in stats
    assert "relationship_count" in stats
    assert isinstance(stats["node_count"], int)
    assert isinstance(stats["relationship_count"], int)


# Note: test_complete_journal_workflow will be refactored to test the
# KnowledgeGraphService.add_journal_entry method once its dependencies
# (like EntitySpanMapping) are also testable.
