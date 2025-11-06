import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict
from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

from minerva_models import JournalEntry
from minerva_backend.processing.models import CuratableMapping, EntityMapping
from minerva_backend.processing.temporal_converter import create_custom_data_converter


class PipelineStage(str, Enum):
    SUBMITTED = "SUBMITTED"
    ENTITY_PROCESSING = "ENTITY_PROCESSING"
    SUBMIT_ENTITY_CURATION = "SUBMIT_ENTITY_CURATION"
    WAIT_ENTITY_CURATION = "WAIT_ENTITY_CURATION"
    RELATION_PROCESSING = "RELATION_PROCESSING"
    SUBMIT_RELATION_CURATION = "SUBMIT_RELATION_CURATION"
    WAIT_RELATION_CURATION = "WAIT_RELATION_CURATION"
    DB_WRITE = "DB_WRITE"
    COMPLETED = "COMPLETED"


class PipelineState(BaseModel):
    stage: PipelineStage
    created_at: Optional[datetime] = None
    journal_entry: Optional[JournalEntry] = None
    entities_extracted: Optional[List[EntityMapping]] = None
    entities_curated: Optional[List[EntityMapping]] = None
    feelings_extracted: Optional[List[CuratableMapping]] = None
    relationships_extracted: Optional[List[CuratableMapping]] = None
    relationships_curated: Optional[List[CuratableMapping]] = None
    error_count: int = 0

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ===== ACTIVITIES (The actual work) =====


class PipelineActivities:
    @activity.defn
    async def extract_entities(journal_entry: JournalEntry) -> List[EntityMapping]:
        """Extract entities with error handling to prevent large error payloads"""
        from minerva_backend.containers import Container

        try:
            container = Container()
            return await container.extraction_service().extract_entities(journal_entry)
        except Exception as e:
            # Log full error details but raise truncated error for Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            activity.logger.error(f"Entity extraction activity failed: {error_msg}")
            raise Exception(f"Entity extraction failed: {error_msg}")

    @activity.defn
    async def extract_feelings(
        journal_entry: JournalEntry, curated_entities: List[EntityMapping]
    ) -> List[CuratableMapping]:
        """Extract feelings using curated entities with error handling"""
        from minerva_backend.containers import Container

        try:
            container = Container()
            return await container.extraction_service().extract_feelings(
                journal_entry, curated_entities
            )
        except Exception as e:
            # Log full error details but raise truncated error for Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            activity.logger.error(f"Feelings extraction activity failed: {error_msg}")
            raise Exception(f"Feelings extraction failed: {error_msg}")

    @activity.defn
    async def extract_relationships(
        journal_entry: JournalEntry, entities: List[EntityMapping]
    ) -> List[CuratableMapping]:
        """Extract relationships between entities with error handling"""
        from minerva_backend.containers import Container

        try:
            container = Container()
            return await container.extraction_service().extract_relationships(
                journal_entry, entities
            )
        except Exception as e:
            # Log full error details but raise truncated error for Temporal
            error_msg = str(e)[:200] + "..." if len(str(e)) > 200 else str(e)
            activity.logger.error(
                f"Relationship extraction activity failed: {error_msg}"
            )
            raise Exception(f"Relationship extraction failed: {error_msg}")

    @activity.defn
    async def submit_entity_curation(
        journal_entry: JournalEntry, entities_spans: List[EntityMapping]
    ) -> None:
        """Human-in-the-loop: Wait for user to curate entities"""
        from minerva_backend.containers import Container

        # Fail-fast validation: ensure entities_spans is properly typed
        if not isinstance(entities_spans, list):
            raise RuntimeError(
                f"entities_spans must be a list, got {type(entities_spans)}"
            )

        for i, entity_mapping in enumerate(entities_spans):
            if not isinstance(entity_mapping, EntityMapping):
                raise RuntimeError(
                    f"entities_spans[{i}] must be EntityMapping, got {type(entity_mapping)}"
                )

            if not hasattr(entity_mapping, "entity"):
                raise RuntimeError(f"entities_spans[{i}] missing 'entity' attribute")

            entity = entity_mapping.entity
            if not hasattr(entity, "uuid"):
                raise RuntimeError(
                    f"entities_spans[{i}].entity missing 'uuid' attribute, got {type(entity)}"
                )

            if not hasattr(entity, "type"):
                raise RuntimeError(
                    f"entities_spans[{i}].entity missing 'type' attribute"
                )

            # Log for debugging (can be removed once stable)
            print(
                f"DEBUG: entities_spans[{i}] = {type(entity_mapping)}, entity = {type(entity)}, uuid = {getattr(entity, 'uuid', 'MISSING')}"
            )

        container = Container()
        # Add to curation queue
        await container.curation_manager().queue_entities_for_curation(
            journal_entry.uuid, journal_entry.entry_text or "", entities_spans
        )

    @activity.defn
    async def wait_for_entity_curation(
        journal_entry: JournalEntry,
    ) -> List[EntityMapping]:
        """Human-in-the-loop: Wait for user to curate entities"""
        from minerva_backend.containers import Container

        container = Container()
        # Poll until user completes curation (with heartbeat to keep workflow alive)
        while True:
            result = await container.curation_manager().get_journal_status(
                journal_entry.uuid
            )
            if result and result == "ENTITIES_DONE":
                return (
                    await container.curation_manager().get_accepted_entities_with_spans(
                        journal_entry.uuid
                    )
                )
            # Temporal heartbeat to prevent timeout
            activity.heartbeat()
            await asyncio.sleep(30)  # Check every 30 seconds

    @activity.defn
    async def submit_relationship_curation(
        journal_entry: JournalEntry, items: List[CuratableMapping]
    ) -> None:
        """Human-in-the-loop: Wait for user to curate relations and feelings"""
        from minerva_backend.containers import Container

        container = Container()
        # Add to curation queue
        await container.curation_manager().queue_relationships_for_curation(
            journal_entry.uuid, items
        )

    @activity.defn
    async def wait_for_relationship_curation(
        journal_entry: JournalEntry,
    ) -> List[CuratableMapping]:
        """Human-in-the-loop: Wait for user to curate relations and feelings"""
        from minerva_backend.containers import Container

        container = Container()
        # Poll until user completes curation (with heartbeat to keep workflow alive)
        while True:
            result = await container.curation_manager().get_journal_status(
                journal_entry.uuid
            )
            if result and result == "COMPLETED":
                return await container.curation_manager().get_accepted_relationships_with_spans(
                    journal_entry.uuid
                )
            # Temporal heartbeat to prevent timeout
            activity.heartbeat()
            await asyncio.sleep(30)  # Check every 30 seconds

    @activity.defn
    async def write_to_knowledge_graph(
        journal_entry: JournalEntry,
        entities: List[EntityMapping],
        relationships: List[CuratableMapping],
    ) -> bool:
        """Final stage: Write curated data to Neo4j"""
        from minerva_backend.containers import Container

        container = Container()
        await container.kg_service().add_journal_entry(
            journal_entry, entities, relationships
        )
        return True


# ===== WORKFLOW (The orchestration) =====


@workflow.defn(name="JournalProcessing")
class JournalProcessingWorkflow:
    """Main workflow that orchestrates the entire 6-stage pipeline"""

    def __init__(self):
        self.state = PipelineState(stage=PipelineStage.SUBMITTED)

    @workflow.run
    async def run(self, journal_entry: JournalEntry) -> PipelineState:
        self.state.journal_entry = journal_entry
        self.state.created_at = workflow.now()
        # Configure retry policy for LLM activities with exponential backoff
        llm_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_attempts=3,  # Reduced from 5 to prevent excessive retries
            backoff_coefficient=2.0,  # Exponential backoff: 2s, 4s, 8s
            maximum_interval=timedelta(minutes=5),  # Cap maximum retry interval
        )

        try:
            # Stage 1-2: Entity Extraction (LLM)
            self.state.stage = PipelineStage.ENTITY_PROCESSING
            self.state.entities_extracted = await workflow.execute_activity(
                PipelineActivities.extract_entities,
                args=[journal_entry],
                start_to_close_timeout=timedelta(
                    minutes=60
                ),  # Max 60 min for Entity Extraction
                retry_policy=llm_retry_policy,
            )

            # Stage 3.0: Submit Entities for curation
            self.state.stage = PipelineStage.SUBMIT_ENTITY_CURATION
            await workflow.execute_activity(
                PipelineActivities.submit_entity_curation,
                args=[journal_entry, self.state.entities_extracted],
                start_to_close_timeout=timedelta(minutes=1),
                schedule_to_close_timeout=timedelta(minutes=5),
            )

            # Stage 3: Entity Curation (Human)
            self.state.stage = PipelineStage.WAIT_ENTITY_CURATION
            self.state.entities_curated = await workflow.execute_activity(
                PipelineActivities.wait_for_entity_curation,
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),  # User has 7 days
                heartbeat_timeout=timedelta(minutes=2),  # Heartbeat every 2 min
            )

            # Stage 4: Feelings Extraction (LLM)
            self.state.stage = PipelineStage.RELATION_PROCESSING
            self.state.feelings_extracted = await workflow.execute_activity(
                PipelineActivities.extract_feelings,
                args=[journal_entry, self.state.entities_curated],
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=llm_retry_policy,
            )

            # Stage 5: Relationship Extraction (LLM)
            self.state.relationships_extracted = await workflow.execute_activity(
                PipelineActivities.extract_relationships,
                args=[journal_entry, self.state.entities_curated],
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=llm_retry_policy,
            )

            # Stage 6.0: Submit Relations and Feelings for curation
            self.state.stage = PipelineStage.SUBMIT_RELATION_CURATION
            combined_items = (
                self.state.feelings_extracted + self.state.relationships_extracted
            )
            await workflow.execute_activity(
                PipelineActivities.submit_relationship_curation,
                args=[journal_entry, combined_items],
                start_to_close_timeout=timedelta(minutes=1),
                schedule_to_close_timeout=timedelta(minutes=5),
            )

            # Stage 7: Relationship and Feelings Curation (Human)
            self.state.stage = PipelineStage.WAIT_RELATION_CURATION
            self.state.relationships_curated = await workflow.execute_activity(
                PipelineActivities.wait_for_relationship_curation,
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),
                heartbeat_timeout=timedelta(minutes=2),
            )

            # Stage 8: Database Write
            self.state.stage = PipelineStage.DB_WRITE
            success = await workflow.execute_activity(
                PipelineActivities.write_to_knowledge_graph,
                args=[
                    journal_entry,
                    self.state.entities_curated,
                    self.state.relationships_curated,
                ],
                schedule_to_close_timeout=timedelta(minutes=5),
                retry_policy=llm_retry_policy,
            )

            if success:
                self.state.stage = PipelineStage.COMPLETED

        except Exception as e:
            workflow.logger.error(
                f"Pipeline failed for {journal_entry.date}({journal_entry.uuid}): {e}"
            )
            self.state.error_count += 1
            raise

        return self.state

    @workflow.query
    def get_state(self) -> PipelineState:
        """Query current pipeline state without affecting workflow"""
        # Return a lightweight state object to prevent large payloads
        return PipelineState(
            stage=self.state.stage,
            created_at=self.state.created_at,
            journal_entry=None,  # Exclude large journal entry from query response
            entities_extracted=None,  # Exclude large entity lists from query response
            entities_curated=None,
            relationships_extracted=None,
            relationships_curated=None,
            error_count=self.state.error_count,
        )


# ===== CLIENT INTERFACE =====


class PipelineOrchestrator:
    """Main interface for starting and monitoring journal processing pipelines"""

    def __init__(self, temporal_uri: str):
        self.temporal_uri = temporal_uri
        self.client: Client | None = None

    async def initialize(self):
        """Connect to Temporal server"""
        self.client = await Client.connect(
            self.temporal_uri, data_converter=create_custom_data_converter()
        )

    async def submit_journal(self, journal_entry: JournalEntry) -> str:
        """Submit a journal entry for processing"""
        workflow_id = f"journal-{journal_entry.date}-{journal_entry.uuid}"

        if self.client:
            await self.client.start_workflow(
                JournalProcessingWorkflow.run,
                args=[journal_entry],
                id=workflow_id,
                task_queue="minerva-pipeline",
            )
        return workflow_id

    async def get_pipeline_status(self, workflow_id: str) -> PipelineState:
        """Get current status of a journal processing pipeline"""
        if not self.client:
            raise RuntimeError("Temporal client not initialized")
        handle = self.client.get_workflow_handle(workflow_id)
        return await handle.query("get_state")

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if not self.client:
            raise RuntimeError("Temporal client not initialized")
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.terminate()
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        """Check if Temporal service is healthy"""
        if not self.client:
            return False
        try:
            await self.client.list_workflows()
            return True
        except Exception:
            return False


# ===== WORKER SETUP =====


async def run_worker():
    """Start the Temporal worker that executes activities"""
    from minerva_backend.config import settings

    client = await Client.connect(
        settings.TEMPORAL_URI, data_converter=create_custom_data_converter()
    )

    worker = Worker(
        client,
        task_queue="minerva-pipeline",
        workflows=[JournalProcessingWorkflow],
        activities=[
            PipelineActivities.extract_entities,
            PipelineActivities.extract_feelings,
            PipelineActivities.extract_relationships,
            PipelineActivities.submit_entity_curation,
            PipelineActivities.wait_for_entity_curation,
            PipelineActivities.submit_relationship_curation,
            PipelineActivities.wait_for_relationship_curation,
            PipelineActivities.write_to_knowledge_graph,
        ],
        debug_mode=True,
    )

    print("[START] Minerva pipeline worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
