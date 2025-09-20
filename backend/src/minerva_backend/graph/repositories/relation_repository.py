"""
Repository for Relation nodes with dual edge/node management.
Handles both the direct RELATED_TO edges and the rich reified Relation nodes.
Edge UUID pattern: Node stores the edge UUID, not vice versa.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple

from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class RelationRepository(BaseRepository[Relation]):
    """
    Repository for managing reified relationships.
    Creates both direct edges for graph traversal and reified nodes for rich context.
    Uses edge UUID pattern: the reified node stores the edge's UUID.
    """

    @property
    def entity_label(self) -> str:
        return "Relation"

    @property
    def entity_class(self) -> type[Relation]:
        return Relation

    def create_edge_only(self, source_uuid: str, target_uuid: str, proposed_types: List[str]) -> str:
        """
        Create only the direct RELATED_TO edge without a reified node.
        Useful for simple relationships that don't need rich context.

        Args:
            source_uuid: UUID of source entity
            target_uuid: UUID of target entity
            proposed_types:

        Returns:
            str: UUID of the created edge

        Raises:
            Exception: If creation fails
        """
        edge_uuid = str(uuid.uuid4())

        query = """
        MATCH (source {uuid: $source_uuid})
        MATCH (target {uuid: $target_uuid})
        CREATE (source)-[edge:RELATED_TO {
            uuid: $edge_uuid,
            summary_short: $summary_short,
            created_at: $created_at,
            proposed_types: $proposed_types
        }]->(target)
        RETURN edge.uuid as edge_uuid
        """

        with self.connection.session() as session:
            try:
                result = session.run(
                    query,
                    source_uuid=source_uuid,
                    target_uuid=target_uuid,
                    edge_uuid=edge_uuid,
                    proposed_types=proposed_types,
                    created_at=datetime.now().isoformat()
                )
                record = result.single()

                if not record:
                    raise Exception("Failed to create edge relationship")

                logger.info(f"Created edge relationship: {proposed_types} (Edge UUID: {edge_uuid})")
                return edge_uuid

            except Exception as e:
                logger.error(f"Error creating edge relationship: {e}")
                raise

    def create_full_relationship(self, relation: Relation) -> str:
        """
        Create both the direct edge and the reified relation node.
        The reified node will store the edge's UUID for linking.

        Args:
            relation: Relation instance to create

        Returns:
            str: UUID of the created reified relation node

        Raises:
            Exception: If creation fails
        """
        # Generate UUID for the edge
        edge_uuid = str(uuid.uuid4())

        # Add edge UUID to relation properties
        properties = self._node_to_properties(relation)
        properties['edge_uuid'] = edge_uuid

        query = """
        // Find source and target entities first
        MATCH (source {uuid: $source_uuid})
        MATCH (target {uuid: $target_uuid})

        // Create direct edge with its own UUID for fast traversal
        CREATE (source)-[edge:RELATED_TO {
            uuid: $edge_uuid,
            type: $type,
            created_at: $created_at,
            summary_short: $summary_short
        }]->(target)

        // Create the reified relation node that references the edge
        CREATE (r:Relation $properties)

        // Create bidirectional connections to reified relation
        CREATE (source)-[:HAS_RELATION]->(r)
        CREATE (target)-[:HAS_RELATION]->(r)

        RETURN r.uuid as relation_uuid, edge.uuid as edge_uuid
        """

        with self.connection.session() as session:
            try:
                result = session.run(
                    query,
                    properties=properties,
                    source_uuid=relation.source,
                    target_uuid=relation.target,
                    edge_uuid=edge_uuid,
                    type=relation.type,
                    created_at=properties.get('created_at'),
                    summary_short=relation.summary_short
                )
                record = result.single()

                if not record:
                    raise Exception("Failed to create reified relationship")

                relation_uuid = record["relation_uuid"]
                logger.info(
                    f"Created reified relationship: {relation.summary_short} (Node: {relation_uuid}, Edge: {edge_uuid})")
                return relation_uuid

            except Exception as e:
                logger.error(f"Error creating reified relationship: {e}")
                raise

    def delete_full_relationship(self, relation_uuid: str) -> bool:
        """
        Delete both the reified relation node and its associated direct edge.

        Args:
            relation_uuid: UUID of the reified relationship to delete

        Returns:
            bool: True if deletion succeeded
        """
        query = """
        MATCH (r:Relation {uuid: $relation_uuid})

        // Delete the direct RELATED_TO edge using the stored edge UUID
        OPTIONAL MATCH ()-[edge:RELATED_TO {uuid: r.edge_uuid}]->()
        DELETE edge

        // Delete the reified relation and its connections
        DETACH DELETE r

        RETURN count(r) as deleted
        """

        with self.connection.session() as session:
            try:
                result = session.run(query, relation_uuid=relation_uuid)
                record = result.single()
                success = record["deleted"] > 0

                if success:
                    logger.info(f"Deleted reified relationship: {relation_uuid}")

                return success

            except Exception as e:
                logger.error(f"Error deleting reified relationship {relation_uuid}: {e}")
                return False

    def update_relationship(self, relation_uuid: str, updates: Dict[str, Any]) -> bool:
        """
        Update reified relationship and sync relevant changes to the direct edge.

        Args:
            relation_uuid: UUID of the relationship to update
            updates: Dictionary of properties to update

        Returns:
            bool: True if update succeeded
        """
        # Add updated timestamp
        updates['updated_at'] = datetime.now().isoformat()

        # Prepare edge updates (only sync specific fields that should be on both)
        edge_updates = {}
        if 'type' in updates:
            edge_updates['type'] = updates['type']
        if 'summary_short' in updates:
            edge_updates['summary_short'] = updates['summary_short']
        if 'updated_at' in updates:
            edge_updates['updated_at'] = updates['updated_at']

        query = """
        MATCH (r:Relation {uuid: $relation_uuid})
        SET r += $updates

        // Update the corresponding direct edge if it exists
        WITH r
        OPTIONAL MATCH ()-[edge:RELATED_TO {uuid: r.edge_uuid}]->()
        SET edge += $edge_updates

        RETURN r.uuid as uuid
        """

        with self.connection.session() as session:
            try:
                result = session.run(
                    query,
                    relation_uuid=relation_uuid,
                    updates=updates,
                    edge_updates=edge_updates
                )
                record = result.single()
                success = record is not None

                if success:
                    logger.info(f"Updated reified relationship: {relation_uuid}")

                return success

            except Exception as e:
                logger.error(f"Error updating reified relationship {relation_uuid}: {e}")
                return False

    def create_mention(self, chunk_uuid: str, node_uuid: str) -> bool:
        """
        Connect a chunk to a node with a MENTIONS relation

        Args:
            chunk_uuid: UUID of the chunk
            node_uuid: UUID of the node

        Returns:
            bool: True if connection succeeded
        """
        query = """
MATCH (c:Chunk {uuid: $chunk_uuid})
MATCH (n {uuid: $node_uuid})
MERGE (c)-[:MENTIONS]->(n)
RETURN count(*) as created
        """
        with self.connection.session() as session:
            try:
                result = session.run(query, chunk_uuid=chunk_uuid, node_uuid=node_uuid)
                record = result.single()
                success = record["created"] > 0
                if success:
                    logger.info(f"Connected chunk {chunk_uuid} to node {node_uuid}")
                return success
            except Exception as e:
                logger.error(f"Error connecting chunk to node: {e}")
                return False

    def create_mentions_batch(self, mentions: List[Tuple[str, str]]) -> int:
        """
        Connect multiple chunks to nodes with MENTIONS relations in batch.

        Args:
            mentions: List of (chunk_uuid, node_uuid) tuples

        Returns:
            int: Number of relationships created
        """
        if not mentions:
            return 0

        query = """
        UNWIND $mentions as mention
        MATCH (c:Chunk {uuid: mention.chunk_uuid})
        MATCH (n {uuid: mention.node_uuid})
        MERGE (c)-[:MENTIONS]->(n)
        RETURN count(*) as created
        """

        # Convert list of tuples to list of dicts for Cypher
        mention_dicts = [
            {"chunk_uuid": chunk_uuid, "node_uuid": node_uuid}
            for chunk_uuid, node_uuid in mentions
        ]

        with self.connection.session() as session:
            try:
                result = session.run(query, mentions=mention_dicts)
                record = result.single()
                created_count = record["created"]
                if created_count > 0:
                    logger.info(f"Created {created_count} MENTIONS relationships in batch")
                return created_count
            except Exception as e:
                logger.error(f"Error creating batch mentions: {e}")
                return 0
