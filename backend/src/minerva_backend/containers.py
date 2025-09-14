"""Dependency injection container for the Minerva application."""

from dependency_injector import containers, providers

from minerva_backend.config import settings
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator


class Container(containers.DeclarativeContainer):
    """
    Main dependency injection container.
    """
    config = providers.Configuration()
    config.from_pydantic(settings)

    db_connection = providers.Singleton(
        Neo4jConnection,
        uri=config.NEO4J_URI,
        user=config.NEO4J_USER,
        password=config.NEO4J_PASSWORD,
    )

    # NOTE: The services below likely depend on the database connection.
    # This is a first step; they will need to be refactored to accept
    # the connection as a dependency.

    curation_manager = providers.Singleton(
        CurationManager,
        db_path=config.CURATION_DB_PATH,
    )

    pipeline_orchestrator = providers.Singleton(
        PipelineOrchestrator,
        temporal_uri=config.TEMPORAL_URI,
    )
