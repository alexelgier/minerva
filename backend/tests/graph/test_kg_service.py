import pytest
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.graph.models.relations import Relation, RelationshipType


@pytest.fixture
def kg_service(db_connection):
    return KnowledgeGraphService(db_connection)


def test_database_stats(kg_service):
    """Test database statistics functionality."""
    stats = kg_service.get_database_stats()

    assert "node_counts" in stats
    assert "relationship_counts" in stats
    assert isinstance(stats["node_counts"], dict)
    assert isinstance(stats["relationship_counts"], dict)

# Note: test_complete_journal_workflow will be refactored to test the
# KnowledgeGraphService.add_journal_entry method once its dependencies
# (like EntitySpanMapping) are also testable.
