import time
from typing import Dict, List

from minerva_backend.graph.db import Neo4jConnection
from minerva_models import JournalEntry
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.extraction.orchestrator import (
    EntityExtractionOrchestrator,
)
from minerva_backend.processing.extraction.processors.factory import ProcessorFactory
from minerva_backend.processing.extraction.services.span_processing_service import (
    SpanProcessingService,
)
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.processing.models import CuratableMapping, EntityMapping
from minerva_backend.utils.logging import get_logger, get_performance_logger


class ExtractionService:
    """Refactored entity extraction service with clear architecture."""

    def __init__(
        self,
        connection: Neo4jConnection,
        llm_service: LLMService,
        obsidian_service: ObsidianService,
        kg_service: KnowledgeGraphService,
        entity_repositories: Dict[str, BaseRepository],
    ):
        self.llm_service = llm_service
        self.connection = connection
        self.obsidian_service = obsidian_service
        self.kg_service = kg_service
        self.logger = get_logger("minerva_backend.processing.extraction_service")
        self.performance_logger = get_performance_logger()

        # Use injected entity repositories
        self.entity_repositories = entity_repositories

        # Configure specialized services
        self.span_processing_service = SpanProcessingService()

        # Create entity processors
        processors = ProcessorFactory.create_all_processors(
            llm_service=llm_service,
            entity_repositories=self.entity_repositories,
            span_service=self.span_processing_service,
            obsidian_service=obsidian_service,
        )

        # Configure orchestrator
        self.orchestrator = EntityExtractionOrchestrator(
            obsidian_service=obsidian_service,
            span_processing_service=self.span_processing_service,
            processors=processors,
            kg_service=self.kg_service,
        )

    async def extract_entities(
        self, journal_entry: JournalEntry
    ) -> List[EntityMapping]:
        """Extract entities from a journal entry using the new architecture."""
        start_time = time.time()

        self.logger.info(
            "Starting entity extraction",
            context={
                "journal_id": journal_entry.uuid,
                "entry_length": (
                    len(journal_entry.entry_text) if journal_entry.entry_text else 0
                ),
                "stage": "entity_extraction",
            },
        )

        try:
            entities = await self.orchestrator.extract_entities(journal_entry)
            duration_ms = (time.time() - start_time) * 1000

            self.performance_logger.log_entity_extraction(
                "all_entities",
                len(entities),
                duration_ms,
                journal_id=journal_entry.uuid,
                entry_length=(
                    len(journal_entry.entry_text) if journal_entry.entry_text else 0
                ),
            )

            self.logger.info(
                "Entity extraction completed",
                context={
                    "journal_id": journal_entry.uuid,
                    "entity_count": len(entities),
                    "duration_ms": duration_ms,
                    "stage": "entity_extraction",
                },
            )

            return entities

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # Truncate error message to prevent large payloads in Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            self.logger.error(
                "Entity extraction failed",
                context={
                    "journal_id": journal_entry.uuid,
                    "error": error_msg,
                    "duration_ms": duration_ms,
                    "stage": "entity_extraction",
                },
            )
            # Re-raise with truncated error message for Temporal
            raise Exception(f"Entity extraction failed: {error_msg}")

    async def extract_feelings(
        self, journal_entry: JournalEntry, curated_entities: List[EntityMapping]
    ) -> List[CuratableMapping]:
        """Extract feelings using curated entities as context."""
        start_time = time.time()

        self.performance_logger.log_processing_time(
            {
                "operation": "extract_feelings",
                "journal_uuid": journal_entry.uuid,
                "stage": "feelings_extraction",
            },
        )

        try:
            from minerva_backend.processing.extraction.context import ExtractionContext
            from minerva_backend.processing.extraction.processors.concept_feeling_processor import (
                ConceptFeelingProcessor,
            )
            from minerva_backend.processing.extraction.processors.emotion_feeling_processor import (
                EmotionFeelingProcessor,
            )

            # Create context with curated entities
            obsidian_entities = self.obsidian_service.build_entity_lookup(journal_entry)
            context = ExtractionContext(
                journal_entry=journal_entry,
                obsidian_entities=obsidian_entities,
                kg_service=self.kg_service,
            )
            context.add_entities(curated_entities)

            all_feelings = []

            # 1. Extract emotion feelings
            emotion_processor = EmotionFeelingProcessor(
                llm_service=self.llm_service,
                entity_repositories=self.entity_repositories,
                span_service=self.span_processing_service,
                obsidian_service=self.obsidian_service,
            )
            emotion_feelings = await emotion_processor.process(context)
            for feeling_mapping in emotion_feelings:
                all_feelings.append(
                    CuratableMapping(
                        kind="feeling_emotion",
                        data=feeling_mapping.entity,
                        spans=feeling_mapping.spans,
                        context=None,
                    )
                )

            # 2. Extract concept feelings
            concept_feeling_processor = ConceptFeelingProcessor(
                llm_service=self.llm_service,
                entity_repositories=self.entity_repositories,
                span_service=self.span_processing_service,
                obsidian_service=self.obsidian_service,
            )
            concept_feelings = await concept_feeling_processor.process(context)
            for feeling_mapping in concept_feelings:
                all_feelings.append(
                    CuratableMapping(
                        kind="feeling_concept",
                        data=feeling_mapping.entity,
                        spans=feeling_mapping.spans,
                        context=None,
                    )
                )

            duration_ms = (time.time() - start_time) * 1000
            self.performance_logger.log_processing_time(
                {
                    "operation": "extract_feelings",
                    "journal_uuid": journal_entry.uuid,
                    "stage": "feelings_extraction",
                    "duration_ms": duration_ms,
                    "feelings_count": len(all_feelings),
                },
            )

            return all_feelings

        except Exception as e:
            self.logger.error(f"Error in feelings extraction: {e}")
            raise

    async def extract_relationships(
        self, journal_entry: JournalEntry, entities: List[EntityMapping]
    ) -> List[CuratableMapping]:
        """Extract relationships between entities (compatibility method)."""
        start_time = time.time()

        self.logger.info(
            "Starting relationship extraction",
            context={
                "journal_id": journal_entry.uuid,
                "entity_count": len(entities),
                "stage": "relationship_extraction",
            },
        )

        try:
            from minerva_backend.processing.extraction.context import ExtractionContext
            from minerva_backend.processing.extraction.relationship_processor import (
                RelationshipProcessor,
            )

            # Create context with extracted entities
            obsidian_entities = self.obsidian_service.build_entity_lookup(journal_entry)
            context = ExtractionContext(
                journal_entry=journal_entry,
                obsidian_entities=obsidian_entities,
                kg_service=self.kg_service,
            )
            context.add_entities(entities)

            all_relationships = []

            # 1. Extract general relationships (existing logic)
            relationship_processor = RelationshipProcessor(
                llm_service=self.llm_service,
                entity_repositories=self.entity_repositories,
                span_service=self.span_processing_service,
                obsidian_service=self.obsidian_service,
            )
            general_relationships = await relationship_processor.process(context)
            for rel_mapping in general_relationships:
                # rel_mapping is already a CuratableMapping, just add it directly
                all_relationships.append(rel_mapping)

            # 2. Extract concept relations (new logic)
            from minerva_backend.processing.extraction.processors.concept_relation_processor import (
                ConceptRelationProcessor,
            )

            concept_relation_processor = ConceptRelationProcessor(
                llm_service=self.llm_service,
                entity_repositories=self.entity_repositories,
                span_service=self.span_processing_service,
                obsidian_service=self.obsidian_service,
            )
            concept_relationships = await concept_relation_processor.process(context)
            for rel_mapping in concept_relationships:
                # rel_mapping is already a CuratableMapping, just add it directly
                all_relationships.append(rel_mapping)
            duration_ms = (time.time() - start_time) * 1000

            self.performance_logger.log_processing_time(
                "relationship_extraction",
                duration_ms,
                journal_id=journal_entry.uuid,
                entity_count=len(entities),
                relationship_count=len(all_relationships),
            )

            self.logger.info(
                "Relationship extraction completed",
                context={
                    "journal_id": journal_entry.uuid,
                    "relationship_count": len(all_relationships),
                    "concept_relations": len(concept_relationships),
                    "duration_ms": duration_ms,
                    "stage": "relationship_extraction",
                },
            )

            return all_relationships

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # Truncate error message to prevent large payloads in Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            self.logger.error(
                "Relationship extraction failed",
                context={
                    "journal_id": journal_entry.uuid,
                    "error": error_msg,
                    "duration_ms": duration_ms,
                    "stage": "relationship_extraction",
                },
            )
            # Re-raise with truncated error message for Temporal
            raise Exception(f"Relationship extraction failed: {error_msg}")
