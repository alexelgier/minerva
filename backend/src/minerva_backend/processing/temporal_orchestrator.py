# pipeline/temporal_orchestrator.py
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, UTC
from enum import Enum
from typing import Dict, Any, List

from temporalio import workflow, activity
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.processing.curation_manager import CurationManager


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
    created_at: datetime = datetime.now()
    journal_entry: JournalEntry = None
    entities_extracted: List[Entity] = None
    entities_curated: List[Entity] = None
    relationships_extracted: List[Relation] = None
    relationships_curated: List[Relation] = None
    error_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to a JSON-serializable dictionary"""
        return {
            "stage": self.stage.value,
            "created_at": self.created_at.isoformat(),
            "journal_entry": self.journal_entry.model_dump() if self.journal_entry else None,
            "entities_extracted": [e.model_dump() for e in
                                   self.entities_extracted] if self.entities_extracted else None,
            "entities_curated": [e.model_dump() for e in self.entities_curated] if self.entities_curated else None,
            "relationships_extracted": [r.model_dump() for r in
                                        self.relationships_extracted] if self.relationships_extracted else None,
            "relationships_curated": [r.model_dump() for r in
                                      self.relationships_curated] if self.relationships_curated else None,
            "error_count": self.error_count
        }


# ===== ACTIVITIES (The actual work) =====

class PipelineActivities:
    def __init__(self, curation_manager: CurationManager, kg_service: KnowledgeGraphService):
        self.curation_manager = curation_manager
        self.kg_service = kg_service

    @activity.defn
    async def extract_entities(self, journal_entry: JournalEntry) -> List[Entity]:
        """Stage 1-2: Extract standalone and relational entities using LLM"""

        # This will call your Ollama extraction pipeline
        return []

    @activity.defn
    async def extract_relationships(self, journal_entry: JournalEntry, entities: List[Entity]) -> List[Relation]:
        """Stage 3: Extract relationships between entities"""

        # This will call your Ollama extraction pipeline
        return []

    @activity.defn
    async def submit_entity_curation(self, journal_entry: JournalEntry, entities: List[Entity]) -> None:
        """Human-in-the-loop: Wait for user to curate entities"""
        # Add to curation queue
        await self.curation_manager.queue_entity_curation(journal_entry.uuid, journal_entry.entry_text, entities)

    @activity.defn
    async def wait_for_entity_curation(self, journal_entry: JournalEntry) -> List[Entity]:
        """Human-in-the-loop: Wait for user to curate entities"""
        # Poll until user completes curation (with heartbeat to keep workflow alive)
        while True:
            result = await self.curation_manager.get_entity_curation_result(journal_entry.uuid)
            if result:
                return result
            # Temporal heartbeat to prevent timeout
            activity.heartbeat()
            await asyncio.sleep(30)  # Check every 30 seconds

    @activity.defn
    async def submit_relationship_curation(self, journal_entry: JournalEntry, entities: List[Entity],
                                           relations: List[Relation]) -> None:
        """Human-in-the-loop: Wait for user to curate entities"""
        # Add to curation queue
        await self.curation_manager.queue_relationship_curation(journal_entry.uuid, journal_entry.entry_text, entities,
                                                                relations)

    @activity.defn
    async def wait_for_relationship_curation(self, journal_entry: JournalEntry) -> List[Relation]:
        """Human-in-the-loop: Wait for user to curate relationships"""
        while True:
            result = await self.curation_manager.get_relationship_curation_result(journal_entry.uuid)
            if result:
                return result
            activity.heartbeat()
            await asyncio.sleep(30)

    @activity.defn
    async def write_to_knowledge_graph(self, journal_entry: JournalEntry, entities: List[Entity],
                                       relationships: List[Relation]) -> bool:
        """Final stage: Write curated data to Neo4j"""
        # In a real implementation, you would also pass the entities and relationships
        # to the knowledge graph service to be persisted.
        self.kg_service.add_journal_entry(journal_entry)
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
            self.state.entities_extracted = await workflow.execute_activity(
                "extract_entities",
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(minutes=60),  # Max 60 min for Entity Extraction
                retry_policy=llm_retry_policy,
            )

            # Stage 3.0: Submit Entities for curation
            self.state.stage = PipelineStage.SUBMIT_ENTITY_CURATION
            await workflow.execute_activity(
                "submit_entity_curation",
                args=[journal_entry, self.state.entities_extracted],
            )

            # Stage 3: Entity Curation (Human)
            self.state.stage = PipelineStage.WAIT_ENTITY_CURATION
            self.state.entities_curated = await workflow.execute_activity(
                "wait_for_entity_curation",
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),  # User has 7 days
                heartbeat_timeout=timedelta(minutes=2),  # Heartbeat every 2 min
            )

            # Stage 4: Relationship Extraction (LLM)
            self.state.stage = PipelineStage.RELATION_PROCESSING
            self.state.relationships_extracted = await workflow.execute_activity(
                "extract_relationships",
                args=[journal_entry, self.state.entities_curated],
                schedule_to_close_timeout=timedelta(minutes=10),
                retry_policy=llm_retry_policy,
            )

            # Stage 5.0: Submit Relations for curation
            self.state.stage = PipelineStage.SUBMIT_RELATION_CURATION
            await workflow.execute_activity(
                "submit_relationship_curation",
                args=[journal_entry, self.state.entities_curated, self.state.relationships_extracted],
            )

            # Stage 5: Relationship Curation (Human)
            self.state.stage = PipelineStage.WAIT_RELATION_CURATION
            self.state.relationships_curated = await workflow.execute_activity(
                "wait_for_relationship_curation",
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(days=7),
                heartbeat_timeout=timedelta(minutes=2),
            )

            # Stage 6: Database Write
            self.state.stage = PipelineStage.DB_WRITE
            success = await workflow.execute_activity(
                "write_to_knowledge_graph",
                args=[journal_entry, self.state.entities_curated, self.state.relationships_curated],
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
    # Create a container instance for the worker
    from minerva_backend.containers import Container
    container = Container()
    container.wire(modules=[__name__])

    # Instantiate services
    curation_manager = container.curation_manager()
    await curation_manager.initialize()
    kg_service = container.kg_service()

    # Create activity instance with dependencies
    activities = PipelineActivities(curation_manager, kg_service)

    client = await Client.connect(container.config.TEMPORAL_URI())

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
    )

    print("🚀 Minerva pipeline worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
