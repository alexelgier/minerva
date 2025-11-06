"""
Neo4j Connection Management for Minerva
Simplified database connection layer focused on connection pooling and health checks.
Repository classes handle all CRUD operations.

Async-only implementation for optimal performance.
"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase

from minerva_backend.config import settings
from minerva_models import EmotionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Manages Neo4j database connection with pooling and health monitoring.
    Provides sessions to repository classes.

    Supports both sync and async operations for gradual migration.
    """

    def __init__(
        self,
        uri: str = settings.NEO4J_URI,
        user: str = settings.NEO4J_USER,
        password: str = settings.NEO4J_PASSWORD,
        max_pool_size: int = 50,
        max_connection_lifetime: int = 3600,
        database: str = None,
    ):
        """
        Initialize Neo4j connection.

        Args:
            uri: Neo4j connection URI
            user: Database username
            password: Database password
            max_pool_size: Maximum number of connections in pool
            max_connection_lifetime: Max lifetime of connections in seconds
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.max_pool_size = max_pool_size
        self.max_connection_lifetime = max_connection_lifetime
        self.database = database

        # Async driver
        self.async_driver: Optional[AsyncDriver] = None
        self._initialized = False

    async def initialize(self):
        """Initialize async driver - called during app startup"""
        if self._initialized:
            return

        try:
            self.async_driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_pool_size=self.max_pool_size,
                max_connection_lifetime=self.max_connection_lifetime,
                database=self.database,
            )

            # Health check
            if not await self.health_check():
                raise ConnectionError(
                    "Failed to establish healthy async connection to Neo4j"
                )

            # Set initialized flag BEFORE creating vector indexes to prevent recursion
            self._initialized = True
            
            # Initialize vector indexes
            await self._ensure_vector_indexes()

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j async connection: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Verify database connection is healthy (async).

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.async_driver:
            logger.error("Async health check failed: No async driver available")
            return False

        try:
            async with self.async_driver.session() as session:
                result = await session.run("RETURN 1 as health_check")
                record = await result.single()

                if record and record["health_check"] == 1:
                    logger.debug("Async health check passed")
                    return True
                else:
                    logger.error("Async health check failed: Unexpected result")
                    return False

        except Exception as e:
            logger.error(f"Async health check failed: {e}")
            return False

    @asynccontextmanager
    async def session_async(self):
        """
        Async context manager for database sessions.
        Automatically handles session cleanup.

        Usage:
            async with db_connection.session_async() as session:
                result = await session.run("MATCH (n) RETURN n")
        """
        if not self._initialized:
            await self.initialize()

        async with self.async_driver.session() as session:
            yield session

    async def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> list:
        """
        Execute a single query and return results (async).
        Convenience method for simple queries.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            list: Query results as list of records
        """
        parameters = parameters or {}

        async with self.session_async() as session:
            result = await session.run(query, parameters)
            return [record async for record in result]

    async def init_emotion_types(self) -> Dict[str, str]:
        """
        Insert all EmotionType values as nodes into the database (idempotent - async).
        Ensures each node has a uuid. Returns a mapping of EmotionType to uuid.
        Requires APOC plugin for uuid generation.
        """
        query = """
        MERGE (e:Emotion {name: $name})
        ON CREATE SET e.uuid = randomUUID()
        RETURN e.name AS name, e.uuid AS uuid
        """
        result: Dict[str, str] = {}
        async with self.session_async() as session:
            for emotion in EmotionType:
                result_query = await session.run(query, {"name": emotion})
                record = await result_query.single()
                if record:
                    result[emotion] = str(record["uuid"])
        return result

    async def close_async(self):
        """Close the async database connection and cleanup resources."""
        if self.async_driver:
            await self.async_driver.close()
            self.async_driver = None
            self._initialized = False
            logger.info("Neo4j async connection closed")

    async def close_all(self):
        """Close async connection."""
        await self.close_async()

    async def _ensure_vector_indexes(self):
        """
        Create vector indexes for all entity types and relations (async).
        This method should be called during async initialization.
        """
        vector_indexes = [
            # Entity indexes
            ("Person", "person_embeddings_index"),
            ("Feeling", "feeling_embeddings_index"),
            ("Emotion", "emotion_embeddings_index"),
            ("Event", "event_embeddings_index"),
            ("Project", "project_embeddings_index"),
            ("Concept", "concept_embeddings_index"),
            ("Content", "content_embeddings_index"),
            ("Consumable", "consumable_embeddings_index"),
            ("Place", "place_embeddings_index"),
            # Document indexes
            ("Quote", "quote_embeddings_index"),
            # Relation indexes
            ("Relation", "relation_embeddings_index"),
        ]

        for label, index_name in vector_indexes:
            try:
                await self._create_vector_index(label, index_name)
            except Exception as e:
                logger.warning(f"Failed to create vector index {index_name}: {e}")

    async def _create_vector_index(self, label: str, index_name: str):
        """
        Create a vector index for a specific label (async).

        Args:
            label: Neo4j node label
            index_name: Name of the vector index
        """
        query = f"""
        CREATE VECTOR INDEX {index_name} IF NOT EXISTS
        FOR (n:{label}) ON (n.embedding)
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: 1024,
                `vector.similarity_function`: 'cosine'
            }}
        }}
        """

        async with self.session_async() as session:
            await session.run(query)

    async def vector_search(
        self,
        label: str,
        query_embedding: list[float],
        limit: int = 10,
        threshold: float = 0.7,
    ) -> list:
        """
        Perform vector similarity search on a specific label (async).

        Args:
            label: Neo4j node label to search
            query_embedding: Query vector for similarity search
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of matching nodes with similarity scores
        """
        query = f"""
        CALL db.index.vector.queryNodes('{label.lower()}_embeddings_index', $limit, $query_embedding)
        YIELD node, score
        WHERE score >= $threshold
        RETURN node, score
        ORDER BY score DESC
        """

        async with self.session_async() as session:
            result = await session.run(
                query,
                {
                    "query_embedding": query_embedding,
                    "limit": limit,
                    "threshold": threshold,
                },
            )
            return [record async for record in result]
