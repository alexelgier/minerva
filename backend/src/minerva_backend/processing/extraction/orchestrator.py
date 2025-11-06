import time
from typing import Any, Dict, List

from minerva_models import JournalEntry
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import (
    EntityProcessorStrategy,
)
from minerva_backend.processing.extraction.services.span_processing_service import (
    SpanProcessingService,
)
from minerva_backend.processing.models import EntityMapping
from minerva_backend.utils.logging import get_logger, get_performance_logger


class EntityExtractionOrchestrator:
    """Orchestrates entity extraction but does not contain processing logic."""

    def __init__(
        self,
        obsidian_service: ObsidianService,
        span_processing_service: SpanProcessingService,
        processors: List[EntityProcessorStrategy],
        kg_service,
    ):
        self.obsidian_service = obsidian_service
        self.span_processing_service = span_processing_service
        self.processors = {processor.entity_type: processor for processor in processors}
        self.kg_service = kg_service
        self.logger = get_logger("minerva_backend.processing.extraction.orchestrator")
        self.performance_logger = get_performance_logger()

    async def extract_entities(
        self, journal_entry: JournalEntry
    ) -> List[EntityMapping]:
        """Extract all entities from a journal entry."""
        start_time = time.time()

        self.logger.info(
            "Starting entity extraction orchestration",
            context={
                "journal_id": journal_entry.uuid,
                "entry_length": len(journal_entry.entry_text or ""),
                "stage": "orchestration",
            },
        )

        try:
            # 1. Prepare extraction context
            context = await self._prepare_extraction_context(journal_entry)

            # 2. Execute processors in specific order
            processing_order = [
                "Person",  # People first
                "Concept",  # Concepts
                "Project",  # Projects
                "Consumable",  # Consumables
                "Content",  # Content
                "Event",  # Events
                "Place",  # Places
            ]

            all_entities = []

            for entity_type in processing_order:
                if entity_type in self.processors:
                    entity_start_time = time.time()

                    self.logger.info(
                        f"Processing {entity_type.lower()} entities",
                        context={
                            "journal_id": journal_entry.uuid,
                            "entity_type": entity_type,
                            "stage": "entity_processing",
                        },
                    )

                    entities = await self.processors[entity_type].process(context)
                    entity_duration_ms = (time.time() - entity_start_time) * 1000

                    all_entities.extend(entities)
                    context.add_entities(entities)

                    self.performance_logger.log_entity_extraction(
                        entity_type,
                        len(entities),
                        entity_duration_ms,
                        journal_id=journal_entry.uuid,
                    )

                    self.logger.info(
                        f"Processed {len(entities)} {entity_type.lower()} entities",
                        context={
                            "journal_id": journal_entry.uuid,
                            "entity_type": entity_type,
                            "entity_count": len(entities),
                            "duration_ms": entity_duration_ms,
                            "stage": "entity_processing",
                        },
                    )

            total_duration_ms = (time.time() - start_time) * 1000

            self.performance_logger.log_processing_time(
                "entity_extraction_orchestration",
                total_duration_ms,
                journal_id=journal_entry.uuid,
                total_entities=len(all_entities),
            )

            self.logger.info(
                "Entity extraction orchestration completed",
                context={
                    "journal_id": journal_entry.uuid,
                    "total_entities": len(all_entities),
                    "duration_ms": total_duration_ms,
                    "stage": "orchestration",
                },
            )

            return all_entities

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            # Truncate error message to prevent large payloads in Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            self.logger.error(
                "Entity extraction orchestration failed",
                context={
                    "journal_id": journal_entry.uuid,
                    "error": error_msg,
                    "duration_ms": duration_ms,
                    "stage": "orchestration",
                },
            )
            # Re-raise with truncated error message for Temporal
            raise Exception(f"Entity extraction orchestration failed: {error_msg}")

    async def _prepare_extraction_context(
        self, journal_entry: JournalEntry
    ) -> ExtractionContext:
        """Prepare the initial context for extraction."""

        # Build Obsidian entity lookup
        obsidian_entities = self.obsidian_service.build_entity_lookup(journal_entry)

        return ExtractionContext(
            journal_entry=journal_entry,
            obsidian_entities=obsidian_entities,
            kg_service=self.kg_service,
        )
