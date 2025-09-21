"""Dependency injection container for the Minerva application."""

from dependency_injector import containers, providers

from minerva_backend.config import settings
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.extraction_service import ExtractionService
from minerva_backend.processing.llm_service import LLMService
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

    curation_manager = providers.Singleton(
        CurationManager,
        db_path=config.CURATION_DB_PATH,
    )

    pipeline_orchestrator = providers.Singleton(
        PipelineOrchestrator,
        temporal_uri=config.TEMPORAL_URI,
    )

    kg_service = providers.Singleton(
        KnowledgeGraphService,
        connection=db_connection,
    )

    llm_service = providers.Singleton(
        LLMService,
        cache=True
    )

    obsidian_service = providers.Singleton(
        ObsidianService
    )

    extraction_service = providers.Singleton(
        ExtractionService,
        connection=db_connection,
        llm_service=llm_service,
        obsidian_service=obsidian_service
    )
