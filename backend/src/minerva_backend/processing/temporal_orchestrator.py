import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation


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


@dataclass
class PipelineState:
    stage: PipelineStage
    created_at: datetime = None
    journal_entry: JournalEntry = None
    entities_extracted: Dict[Entity, List[Span]] = None
    entities_curated: Dict[Entity, List[Span]] = None
    relationships_extracted: Dict[Relation, List[Span]] = None
    relationships_curated: Dict[Relation, List[Span]] = None
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a JSON-serializable dictionary"""
        return {
            "stage": self.stage.value,
            "created_at": self.created_at.isoformat(),
            "journal_entry": self.journal_entry.model_dump() if self.journal_entry else None,
            "entities_extracted": [{"entity": e.model_dump(), "spans": [s.model_dump() for s in spans]} for e, spans
                                   in self.entities_extracted.items()] if self.entities_extracted else None,
            "entities_curated": [{"entity": e.model_dump(), "spans": [s.model_dump() for s in spans]} for e, spans in
                                 self.entities_curated.items()] if self.entities_curated else None,
            "relationships_extracted": [
                {"relationship": r.model_dump(), "spans": [s.model_dump() for s in spans]} for r, spans in
                self.relationships_extracted.items()] if self.relationships_extracted else None,
            "relationships_curated": [
                {"relationship": r.model_dump(), "spans": [s.model_dump() for s in spans]} for r, spans in
                self.relationships_curated.items()] if self.relationships_curated else None,
            "error_count": self.error_count
        }


# ===== ACTIVITIES (The actual work) =====

class PipelineActivities:

    @activity.defn
    async def extract_entities(self, journal_entry: JournalEntry) -> Dict[Entity, List[Span]]:
        """Extract entities"""
        from minerva_backend.containers import Container
        container = Container()

        return await container.extraction_service().extract_entities(journal_entry)

    @activity.defn
    async def extract_relationships(self, journal_entry: JournalEntry,
                                    entities: List[Entity]) -> Dict[Relation, List[Span]]:
        """Extract relationships between entities"""
        from minerva_backend.containers import Container
        container = Container()

        return await container.extraction_service().extract_relationships(journal_entry, entities)

    @activity.defn
    async def submit_entity_curation(self, journal_entry: JournalEntry,
                                     entities_spans: Dict[Entity, List[Span]]) -> None:
        """Human-in-the-loop: Wait for user to curate entities"""
        from minerva_backend.containers import Container
        container = Container()

        # Add to curation queue
        await container.curation_manager().queue_entities_for_curation(journal_entry.uuid, journal_entry.entry_text,
                                                                       entities_spans)

    @activity.defn
    async def wait_for_entity_curation(self, journal_entry: JournalEntry) -> Dict[Entity, List[Span]]:
        """Human-in-the-loop: Wait for user to curate entities"""
        from minerva_backend.containers import Container
        container = Container()
        # Poll until user completes curation (with heartbeat to keep workflow alive)
        while True:
            result = await container.curation_manager().get_journal_status(journal_entry.uuid)
            if result and result == "ENTITIES_DONE":
                return await container.curation_manager().get_accepted_entities_with_spans(journal_entry.uuid)
            # Temporal heartbeat to prevent timeout
            activity.heartbeat()
            await asyncio.sleep(30)  # Check every 30 seconds

    @activity.defn
    async def submit_relationship_curation(self, journal_entry: JournalEntry,
                                           relations_spans: Dict[Relation, List[Span]]) -> None:
        """Human-in-the-loop: Wait for user to curate relations"""
        from minerva_backend.containers import Container
        container = Container()
        # Add to curation queue
        await container.curation_manager().queue_relationships_for_curation(journal_entry.uuid, relations_spans)

    @activity.defn
    async def wait_for_relationship_curation(self, journal_entry: JournalEntry) -> Dict[Relation, List[Span]]:
        """Human-in-the-loop: Wait for user to curate relations"""
        from minerva_backend.containers import Container
        container = Container()
        # Poll until user completes curation (with heartbeat to keep workflow alive)
        while True:
            result = await container.curation_manager().get_journal_status(journal_entry.uuid)
            if result and result == "COMPLETED":
                return await container.curation_manager().get_accepted_relationships_with_spans(journal_entry.uuid)
            # Temporal heartbeat to prevent timeout
            activity.heartbeat()
            await asyncio.sleep(30)  # Check every 30 seconds

    @activity.defn
    async def write_to_knowledge_graph(self, journal_entry: JournalEntry, entities_spans: Dict[Entity, List[Span]],
                                       relationships_spans: Dict[Relation, List[Span]]) -> bool:
        """Final stage: Write curated data to Neo4j"""
        from minerva_backend.containers import Container
        container = Container()
        container.kg_service().add_journal_entry(journal_entry, entities_spans, relationships_spans)
        return True


# ===== WORKFLOW (The orchestration) =====

@workflow.defn(name="JournalProcessing")
class JournalProcessingWorkflow:
    """Main workflow that orchestrates the entire 6-stage pipeline"""

    def __init__(self):
        self.state = PipelineState(
            stage=PipelineStage.SUBMITTED
        )

    @workflow.run
    async def run(self, journal_entry: JournalEntry) -> PipelineState:
        self.state.journal_entry = journal_entry
        self.state.created_at = workflow.now()
        # Configure retry policy for LLM activities
        llm_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            maximum_attempts=5,
            backoff_coefficient=1.0,  # No backoff, immediate retry
        )

        try:
            # Stage 1-2: Entity Extraction (LLM)
            self.state.stage = PipelineStage.ENTITY_PROCESSING
            self.state.entities_and_spans_extracted = await workflow.execute_activity(
                PipelineActivities.extract_entities,
                args=[journal_entry],
                start_to_close_timeout=timedelta(minutes=60),  # Max 60 min for Entity Extraction
                retry_policy=llm_retry_policy,
            )

            # Stage 3.0: Submit Entities for curation
            self.state.stage = PipelineStage.SUBMIT_ENTITY_CURATION
            await workflow.execute_activity(
                PipelineActivities.submit_entity_curation,
                args=[journal_entry, self.state.entities_and_spans_extracted],
                start_to_close_timeout=timedelta(minutes=1),
                schedule_to_close_timeout=timedelta(minutes=5),
            )

            # Stage 3: Entity Curation (Human)
            self.state.stage = PipelineStage.WAIT_ENTITY_CURATION
            self.state.entities_and_spans_curated = await workflow.execute_activity(
                PipelineActivities.wait_for_entity_curation,
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),  # User has 7 days
                heartbeat_timeout=timedelta(minutes=2),  # Heartbeat every 2 min
            )

            # Stage 4: Relationship Extraction (LLM)
            self.state.stage = PipelineStage.RELATION_PROCESSING
            self.state.relationships_and_spans_extracted = await workflow.execute_activity(
                PipelineActivities.extract_relationships,
                args=[journal_entry, list(self.state.entities_and_spans_curated.keys())],
                start_to_close_timeout=timedelta(minutes=60),
                retry_policy=llm_retry_policy,
            )

            # Stage 5.0: Submit Relations for curation
            self.state.stage = PipelineStage.SUBMIT_RELATION_CURATION
            await workflow.execute_activity(
                PipelineActivities.submit_relationship_curation,
                args=[journal_entry, self.state.relationships_and_spans_extracted],
                start_to_close_timeout=timedelta(minutes=1),
                schedule_to_close_timeout=timedelta(minutes=5),
            )

            # Stage 5: Relationship Curation (Human)
            self.state.stage = PipelineStage.WAIT_RELATION_CURATION
            self.state.relationships_and_spans_curated = await workflow.execute_activity(
                PipelineActivities.wait_for_relationship_curation,
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),
                heartbeat_timeout=timedelta(minutes=2),
            )

            # Stage 6: Database Write
            self.state.stage = PipelineStage.DB_WRITE
            success = await workflow.execute_activity(
                PipelineActivities.write_to_knowledge_graph,
                args=[journal_entry, self.state.entities_and_spans_curated, self.state.relationships_and_spans_curated],
                schedule_to_close_timeout=timedelta(minutes=5),
                retry_policy=llm_retry_policy,
            )

            if success:
                self.state.stage = PipelineStage.COMPLETED

        except Exception as e:
            workflow.logger.error(f"Pipeline failed for {journal_entry.date}({journal_entry.uuid}): {e}")
            self.state.error_count += 1
            raise

        return self.state

    @workflow.query
    def get_state(self) -> PipelineState:
        """Query current pipeline state without affecting workflow"""
        return self.state


# ===== CLIENT INTERFACE =====

class PipelineOrchestrator:
    """Main interface for starting and monitoring journal processing pipelines"""

    def __init__(self, temporal_uri: str):
        self.temporal_uri = temporal_uri
        self.client: Client | None = None

    async def initialize(self):
        """Connect to Temporal server"""
        self.client = await Client.connect(self.temporal_uri, data_converter=pydantic_data_converter)

    async def submit_journal(self, journal_entry: JournalEntry) -> str:
        """Submit a journal entry for processing"""
        workflow_id = f"journal-{journal_entry.date}-{journal_entry.uuid}"

        await self.client.start_workflow(
            JournalProcessingWorkflow.run,
            args=[journal_entry],
            id=workflow_id,
            task_queue="minerva-pipeline"
        )

        return workflow_id

    async def get_pipeline_status(self, workflow_id: str) -> PipelineState:
        """Get current status of a journal processing pipeline"""
        handle = self.client.get_workflow_handle(workflow_id)
        return await handle.query("get_state")

    async def get_all_pending_curation(self) -> List[Dict[str, Any]]:
        """Get all journal entries waiting for curation (across all workflows)"""
        # You'd implement this by querying Temporal for workflows in curation stages
        # This is a simplified version
        pending = []

        # In real implementation, you'd list workflows and query their states
        # For now, returning empty list
        return pending


# ===== WORKER SETUP =====

async def run_worker():
    """Start the Temporal worker that executes activities"""
    from minerva_backend.containers import Container
    container = Container()
    # Create activity instance with dependencies
    activities = PipelineActivities()

    client = await Client.connect(container.config.TEMPORAL_URI(), data_converter=pydantic_data_converter)

    worker = Worker(
        client,
        task_queue="minerva-pipeline",
        workflows=[JournalProcessingWorkflow],
        activities=[
            activities.extract_entities,
            activities.extract_relationships,
            activities.submit_entity_curation,
            activities.wait_for_entity_curation,
            activities.submit_relationship_curation,
            activities.wait_for_relationship_curation,
            activities.write_to_knowledge_graph,
        ],
        debug_mode=True
    )

    print("🚀 Minerva pipeline worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
