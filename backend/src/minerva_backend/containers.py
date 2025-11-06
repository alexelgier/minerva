"""Dependency injection container for the Minerva application.

This module defines the main dependency injection container using dependency-injector.
All services and their dependencies are configured here.

For testing patterns and usage, see:
- backend/docs/architecture/dependency-injection.md
- backend/docs/development/testing.md

Key patterns:
- Singleton providers for core services (db_connection, llm_service, etc.)
- Factory providers for repositories (created per request)
- Lambda providers for complex initialization (emotions_dict)
"""

from dependency_injector import containers, providers 

from minerva_backend.config import settings
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.repositories.concept_repository import ConceptRepository
from minerva_backend.graph.repositories.consumable_repository import (
    ConsumableRepository,
)
from minerva_backend.graph.repositories.content_repository import ContentRepository
from minerva_backend.graph.repositories.emotion_repository import EmotionRepository
from minerva_backend.graph.repositories.event_repository import EventRepository
from minerva_backend.graph.repositories.feeling_concept_repository import (
    FeelingConceptRepository,
)
from minerva_backend.graph.repositories.feeling_emotion_repository import (
    FeelingEmotionRepository,
)
from minerva_backend.graph.repositories.journal_entry_repository import (
    JournalEntryRepository,
)
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.repositories.place_repository import PlaceRepository
from minerva_backend.graph.repositories.project_repository import ProjectRepository
from minerva_backend.graph.repositories.quote_repository import QuoteRepository
from minerva_backend.graph.repositories.relation_repository import RelationRepository
from minerva_backend.graph.repositories.temporal_repository import TemporalRepository
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.extraction_service import ExtractionService
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator


async def initialize_async_services(container):
    """Initialize services that need async setup."""
    # Initialize Neo4j async connection
    await container.db_connection().initialize()

    # Initialize other async services
    await container.curation_manager().initialize()
    await container.pipeline_orchestrator().initialize()

    # Initialize emotions dict with async connection and update the provider
    emotions_dict = await container.db_connection().init_emotion_types()
    # Override the emotions_dict_async provider with the actual data
    container.emotions_dict_async.override(emotions_dict)


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

    def _create_emotions_dict(db_connection):
        return db_connection.init_emotion_types()

    async def _create_emotions_dict_async(db_connection):
        return await db_connection.init_emotion_types()

    emotions_dict = providers.Singleton(
        _create_emotions_dict, db_connection=db_connection
    )

    # Use a simple provider that will be set during async initialization
    emotions_dict_async = providers.Singleton(lambda: {})

    llm_service = providers.Singleton(LLMService, cache=True)

    # Repository providers (need to be defined before services that use them)
    journal_entry_repository = providers.Factory(
        JournalEntryRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    temporal_repository = providers.Factory(
        TemporalRepository,
        connection=db_connection,
    )

    relation_repository = providers.Factory(
        RelationRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    # Entity repository providers
    person_repository = providers.Factory(
        PersonRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    feeling_emotion_repository = providers.Factory(
        FeelingEmotionRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    feeling_concept_repository = providers.Factory(
        FeelingConceptRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    emotion_repository = providers.Factory(
        EmotionRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    event_repository = providers.Factory(
        EventRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    project_repository = providers.Factory(
        ProjectRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    concept_repository = providers.Factory(
        ConceptRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    content_repository = providers.Factory(
        ContentRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    consumable_repository = providers.Factory(
        ConsumableRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    place_repository = providers.Factory(
        PlaceRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    quote_repository = providers.Factory(
        QuoteRepository,
        connection=db_connection,
        llm_service=llm_service,
    )

    # Entity repositories collection
    entity_repositories = providers.Dict(
        {
            "Person": person_repository,
            "FeelingEmotion": feeling_emotion_repository,
            "FeelingConcept": feeling_concept_repository,
            "Emotion": emotion_repository,
            "Event": event_repository,
            "Project": project_repository,
            "Concept": concept_repository,
            "Content": content_repository,
            "Consumable": consumable_repository,
            "Place": place_repository,
            "Quote": quote_repository,
        }
    )

    obsidian_service = providers.Singleton(
        ObsidianService,
        vault_path=config.OBSIDIAN_VAULT_PATH,
        llm_service=llm_service,
        concept_repository=concept_repository,
    )

    kg_service = providers.Singleton(
        KnowledgeGraphService,
        connection=db_connection,
        llm_service=llm_service,
        emotions_dict=emotions_dict_async,  # Use async version
        obsidian_service=obsidian_service,
        journal_entry_repository=journal_entry_repository,
        temporal_repository=temporal_repository,
        relation_repository=relation_repository,
        entity_repositories=entity_repositories,
    )

    extraction_service = providers.Singleton(
        ExtractionService,
        connection=db_connection,
        llm_service=llm_service,
        obsidian_service=obsidian_service,
        kg_service=kg_service,
        entity_repositories=entity_repositories,
    )
