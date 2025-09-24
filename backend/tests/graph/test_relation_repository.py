import pytest
from uuid import uuid4
from datetime import datetime

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.repositories.relation_repository import RelationRepository


@pytest.fixture
def relation_repository(db_connection: Neo4jConnection) -> RelationRepository:
    """Fixture to provide a RelationRepository instance."""
    return RelationRepository(db_connection)


@pytest.fixture
def sample_nodes(db_connection: Neo4jConnection):
    """Fixture to create source and target nodes for relationships."""
    with db_connection.session() as session:
        source_uuid = str(uuid4())
        target_uuid = str(uuid4())
        session.run("CREATE (:TestNode {uuid: $uuid, name: 'Source'})", uuid=source_uuid)
        session.run("CREATE (:TestNode {uuid: $uuid, name: 'Target'})", uuid=target_uuid)

        yield source_uuid, target_uuid

        # Teardown
        session.run("MATCH (n) WHERE n.uuid IN [$source, $target] DETACH DELETE n", source=source_uuid,
                    target=target_uuid)


@pytest.fixture
def sample_relation(sample_nodes) -> Relation:
    """Fixture to provide a sample Relation model instance."""
    source_uuid, target_uuid = sample_nodes
    return Relation(
        uuid=str(uuid4()),
        source=source_uuid,
        target=target_uuid,
        proposed_types=["FRIEND_OF"],
        summary_short="Source is a friend of Target",
        summary="Source and Target have been friends for a long time."
    )


def test_create_edge_only(relation_repository: RelationRepository, sample_nodes, db_connection: Neo4jConnection):
    """Test creating only a direct edge between two nodes."""
    source_uuid, target_uuid = sample_nodes
    proposed_types = ["WORKS_WITH"]

    edge_uuid = relation_repository.create_edge_only(source_uuid, target_uuid, proposed_types)

    assert edge_uuid is not None

    with db_connection.session() as session:
        result = session.run(
            "MATCH (:TestNode {uuid: $source_uuid})-[r:RELATED_TO]->(:TestNode {uuid: $target_uuid}) "
            "RETURN r.uuid as uuid, r.proposed_types as types",
            source_uuid=source_uuid,
            target_uuid=target_uuid
        )
        record = result.single()
        assert record is not None
        assert record["uuid"] == edge_uuid
        assert record["types"] == proposed_types

        # Cleanup
        session.run("MATCH ()-[r:RELATED_TO {uuid: $uuid}]->() DELETE r", uuid=edge_uuid)


def test_create_full_relationship(relation_repository: RelationRepository, sample_relation: Relation,
                                  db_connection: Neo4jConnection):
    """Test creating a full reified relationship with a node and an edge."""
    relation_uuid = relation_repository.create_full_relationship(sample_relation)

    assert relation_uuid == sample_relation.uuid

    # Check if relation node exists
    created_relation = relation_repository.find_by_uuid(relation_uuid)
    assert created_relation is not None
    assert created_relation.summary_short == sample_relation.summary_short

    with db_connection.session() as session:
        # Check direct RELATED_TO edge
        result = session.run(
            "MATCH ({uuid: $source_uuid})-[r:RELATED_TO]->({uuid: $target_uuid}) RETURN r",
            source_uuid=sample_relation.source,
            target_uuid=sample_relation.target
        )
        edge_record = result.single()
        assert edge_record is not None
        edge_properties = dict(edge_record['r'])
        assert edge_properties["summary_short"] == sample_relation.summary_short
        assert "created_at" in edge_properties

        # Check HAS_RELATION edges to reified node
        result = session.run(
            "MATCH (n)-[:HAS_RELATION]->(r:Relation {uuid: $uuid}) RETURN count(n) as count",
            uuid=relation_uuid
        )
        assert result.single()["count"] == 2

    # Cleanup
    relation_repository.delete_full_relationship(relation_uuid)


def test_delete_full_relationship(relation_repository: RelationRepository, sample_relation: Relation,
                                  db_connection: Neo4jConnection):
    """Test deleting a full reified relationship."""
    relation_uuid = relation_repository.create_full_relationship(sample_relation)

    success = relation_repository.delete_full_relationship(relation_uuid)
    assert success is True

    # Verify relation node is deleted
    assert relation_repository.find_by_uuid(relation_uuid) is None

    # Verify RELATED_TO edge is deleted
    with db_connection.session() as session:
        result = session.run(
            "MATCH ({uuid: $source_uuid})-[r:RELATED_TO]->({uuid: $target_uuid}) RETURN r",
            source_uuid=sample_relation.source,
            target_uuid=sample_relation.target
        )
        assert result.single() is None


def test_update_relationship(relation_repository: RelationRepository, sample_relation: Relation,
                             db_connection: Neo4jConnection):
    """Test updating a reified relationship and syncing to the direct edge."""
    relation_uuid = relation_repository.create_full_relationship(sample_relation)

    updates = {
        "summary_short": "Updated summary",
        "summary": "Updated full summary"
    }

    success = relation_repository.update_relationship(relation_uuid, updates)
    assert success is True

    updated_relation = relation_repository.find_by_uuid(relation_uuid)
    assert updated_relation is not None
    assert updated_relation.summary_short == "Updated summary"

    # get edge_uuid first, then find the edge
    with db_connection.session() as session:
        result = session.run(
            "MATCH (r:Relation {uuid: $relation_uuid}) "
            "WITH r.edge_uuid as edge_uuid "
            "MATCH ()-[edge:RELATED_TO {uuid: edge_uuid}]->() "
            "RETURN edge.summary_short as summary, edge.updated_at as updated_at",
            relation_uuid=relation_uuid
        )
        record = result.single()
        assert record["summary"] == "Updated summary"
        assert record["updated_at"] is not None

    # Cleanup
    relation_repository.delete_full_relationship(relation_uuid)


@pytest.fixture
def sample_chunk_and_node(db_connection: Neo4jConnection):
    """Fixture to create a chunk node and a generic node for MENTIONS tests."""
    with db_connection.session() as session:
        chunk_uuid = str(uuid4())
        node_uuid = str(uuid4())
        session.run("CREATE (:Chunk {uuid: $uuid})", uuid=chunk_uuid)
        session.run("CREATE (:TestNode {uuid: $uuid})", uuid=node_uuid)

        yield chunk_uuid, node_uuid

        # Teardown
        session.run("MATCH (n) WHERE n.uuid IN [$chunk_uuid, $node_uuid] DETACH DELETE n",
                    chunk_uuid=chunk_uuid, node_uuid=node_uuid)


def test_create_mention(relation_repository: RelationRepository, sample_chunk_and_node, db_connection: Neo4jConnection):
    """Test creating a MENTIONS relationship between a chunk and a node."""
    chunk_uuid, node_uuid = sample_chunk_and_node

    success = relation_repository.create_mention(chunk_uuid, node_uuid)
    assert success is True

    with db_connection.session() as session:
        result = session.run(
            "MATCH (:Chunk {uuid: $chunk_uuid})-[:MENTIONS]->(:TestNode {uuid: $node_uuid}) RETURN count(*) as count",
            chunk_uuid=chunk_uuid,
            node_uuid=node_uuid
        )
        assert result.single()["count"] == 1


def test_create_mentions_batch(relation_repository: RelationRepository, db_connection: Neo4jConnection):
    """Test creating multiple MENTIONS relationships in a batch."""
    # Setup
    with db_connection.session() as session:
        c1, c2 = str(uuid4()), str(uuid4())
        n1, n2 = str(uuid4()), str(uuid4())
        session.run("CREATE (:Chunk {uuid: $uuid})", uuid=c1)
        session.run("CREATE (:Chunk {uuid: $uuid})", uuid=c2)
        session.run("CREATE (:TestNode {uuid: $uuid})", uuid=n1)
        session.run("CREATE (:TestNode {uuid: $uuid})", uuid=n2)
        mentions = [(c1, n1), (c2, n2)]

    # Test
    created_count = relation_repository.create_mentions_batch(mentions)
    assert created_count == 2

    # Verify
    with db_connection.session() as session:
        result1 = session.run(
            "MATCH (:Chunk {uuid: $c_uuid})-[:MENTIONS]->(:TestNode {uuid: $n_uuid}) RETURN count(*) as count",
            c_uuid=c1, n_uuid=n1
        )
        assert result1.single()["count"] == 1

        result2 = session.run(
            "MATCH (:Chunk {uuid: $c_uuid})-[:MENTIONS]->(:TestNode {uuid: $n_uuid}) RETURN count(*) as count",
            c_uuid=c2, n_uuid=n2
        )
        assert result2.single()["count"] == 1

    # Teardown
    with db_connection.session() as session:
        session.run("MATCH (n) WHERE n.uuid IN [$c1, $c2, $n1, $n2] DETACH DELETE n", c1=c1, c2=c2, n1=n1, n2=n2)


def test_base_repository_methods_on_relation(relation_repository: RelationRepository, sample_relation: Relation):
    """
    Test that standard base repository methods work on Relation nodes.
    Note: These do not handle the associated edge logic; create_full_relationship is preferred.
    """
    # Test create
    relation_uuid = relation_repository.create(sample_relation)
    assert relation_uuid == sample_relation.uuid

    # Test find_by_uuid
    found = relation_repository.find_by_uuid(relation_uuid)
    assert found is not None
    assert found.uuid == relation_uuid

    # Test exists
    assert relation_repository.exists(relation_uuid) is True
    assert relation_repository.exists(str(uuid4())) is False

    # Test list_all & count
    initial_count = relation_repository.count()
    assert initial_count >= 1
    all_relations = relation_repository.list_all()
    assert any(r.uuid == relation_uuid for r in all_relations)

    # Test update (base version)
    updates = {"summary_short": "Base update"}
    uuid = relation_repository.update(relation_uuid, updates)
    assert uuid is not None
    updated = relation_repository.find_by_uuid(relation_uuid)
    assert updated.summary_short == "Base update"

    # Test delete (base version)
    success = relation_repository.delete(relation_uuid)
    assert success is True
    assert relation_repository.find_by_uuid(relation_uuid) is None
