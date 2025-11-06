"""
Database utilities for testing.

Provides fixtures and utilities for managing test databases,
including Neo4j test database setup and cleanup.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Generator

import pytest
from neo4j import GraphDatabase

from minerva_backend.config import settings
from minerva_backend.graph.db import Neo4jConnection

logger = logging.getLogger(__name__)


class TestDatabaseManager:
    """Manages test database operations."""
    
    def __init__(self, database: str = "testdb"):
        self.database = database
        self.connection = None
    
    def setup_connection(self) -> Neo4jConnection:
        """Set up connection to test database."""
        self.connection = Neo4jConnection(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            database=self.database
        )
        return self.connection
    
    def clear_database(self):
        """Clear all data from test database."""
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        with self.connection.session() as session:
            # Clear all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            logger.info(f"Cleared test database: {self.database}")
    
    def initialize_emotions(self):
        """Initialize emotion types in test database."""
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        emotions_dict = self.connection.init_emotion_types()
        logger.info(f"Initialized {len(emotions_dict)} emotion types")
        return emotions_dict
    
    def setup_test_database(self):
        """Complete setup: clear and initialize test database."""
        self.clear_database()
        emotions_dict = self.initialize_emotions()
        return emotions_dict
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None


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


@asynccontextmanager
async def async_test_database(database: str = "testdb") -> AsyncGenerator[TestDatabaseManager, None]:
    """Async context manager for test database operations."""
    manager = TestDatabaseManager(database)
    try:
        manager.setup_connection()
        manager.setup_test_database()
        yield manager
    finally:
        manager.close()


def check_neo4j_availability() -> bool:
    """Check if Neo4j is available for testing."""
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            return record and record["test"] == 1
    except Exception as e:
        logger.warning(f"Neo4j not available: {e}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()


@pytest.fixture(scope="session")
def neo4j_available() -> bool:
    """Check if Neo4j is available for integration tests."""
    return check_neo4j_availability()
