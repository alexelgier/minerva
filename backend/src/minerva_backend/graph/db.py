"""
Neo4j Connection Management for Minerva
Simplified database connection layer focused on connection pooling and health checks.
Repository classes handle all CRUD operations.
"""

from neo4j import GraphDatabase, Driver, Session
from typing import Optional, Dict, Any
import logging
from contextlib import contextmanager

from minerva_backend.config import settings
from minerva_backend.graph.models.entities import EmotionType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jConnection:
    """
    Manages Neo4j database connection with pooling and health monitoring.
    Provides sessions to repository classes.
    """

    def __init__(self,
                 uri: str = settings.NEO4J_URI,
                 user: str = settings.NEO4J_USER,
                 password: str = settings.NEO4J_PASSWORD,
                 max_pool_size: int = 50,
                 max_connection_lifetime: int = 3600,
                 database: str = None):
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
        self.driver: Optional[Driver] = None

        try:
            self.driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
                max_connection_pool_size=max_pool_size,
                max_connection_lifetime=max_connection_lifetime,
                database=database
            )

            if not self.health_check():
                raise ConnectionError("Failed to establish healthy connection to Neo4j")

            logger.info(f"Neo4j connection established successfully to {uri}")

        except Exception as e:
            logger.error(f"Failed to initialize Neo4j connection: {e}")
            raise

    def health_check(self) -> bool:
        """
        Verify database connection is healthy.

        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self.driver:
            logger.error("Health check failed: No driver available")
            return False

        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as health_check")
                record = result.single()

                if record and record["health_check"] == 1:
                    logger.debug("Health check passed")
                    return True
                else:
                    logger.error("Health check failed: Unexpected result")
                    return False

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: Neo4j session for database operations

        Raises:
            ConnectionError: If no driver is available
        """
        if not self.driver:
            raise ConnectionError("No database driver available")

        return self.driver.session()

    @contextmanager
    def session(self):
        """
        Context manager for database sessions.
        Automatically handles session cleanup.

        Usage:
            with db_connection.session() as session:
                result = session.run("MATCH (n) RETURN n")
        """
        session = None
        try:
            session = self.get_session()
            yield session
        finally:
            if session:
                session.close()

    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> list:
        """
        Execute a single query and return results.
        Convenience method for simple queries.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            list: Query results as list of records
        """
        parameters = parameters or {}

        with self.session() as session:
            result = session.run(query, parameters)
            return [record for record in result]

    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        Useful for monitoring and debugging.

        Returns:
            Dict containing node counts, relationship counts, etc.
        """
        with self.session() as session:
            # Count nodes by label
            node_query = """
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {}) 
            YIELD value
            RETURN label, value.count as count
            """

            # Fallback if APOC not available
            simple_node_query = """
            MATCH (n)
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY count DESC
            """

            # Count relationships by type
            rel_query = """
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
            """

            try:
                # Try advanced query first
                node_result = session.run(node_query)
                node_counts = {record["label"]: record["count"] for record in node_result}
            except:
                # Fall back to simple query
                node_result = session.run(simple_node_query)
                node_counts = {record["label"]: record["count"] for record in node_result}

            rel_result = session.run(rel_query)
            rel_counts = {record["rel_type"]: record["count"] for record in rel_result}

            # Total counts
            total_nodes = sum(node_counts.values())
            total_rels = sum(rel_counts.values())

            return {
                "total_nodes": total_nodes,
                "total_relationships": total_rels,
                "node_counts": node_counts,
                "relationship_counts": rel_counts,
                "connection_uri": self.uri,
                "connection_healthy": self.health_check()
            }

    def init_emotion_types(self) -> Dict[str, str]:
        """
        Insert all EmotionType values as nodes into the database (idempotent).
        Ensures each node has a uuid. Returns a mapping of EmotionType to uuid.
        Requires APOC plugin for uuid generation.
        """
        query = """
        MERGE (e:Emotion {name: $name})
        ON CREATE SET e.uuid = randomUUID()
        RETURN e.name AS name, e.uuid AS uuid
        """
        result: Dict[str, str] = {}
        with self.session() as session:
            for emotion in EmotionType:
                record = session.run(query, {"name": emotion}).single()
                if record:
                    result[emotion] = str(record["uuid"])
        return result


def close(self):
    """Close the database connection and cleanup resources."""
    if self.driver:
        self.driver.close()
        self.driver = None
        logger.info("Neo4j connection closed")


def __enter__(self):
    """Context manager entry."""
    return self


def __exit__(self, exc_type, exc_val, exc_tb):
    """Context manager exit with cleanup."""
    self.close()
