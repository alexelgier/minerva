# pipeline/temporal_orchestrator.py
import asyncio
from datetime import datetime, timedelta, UTC, date
from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass

from temporalio import workflow, activity
from temporalio.common import RetryPolicy
from temporalio.client import Client
from temporalio.worker import Worker

from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.relations import Relation


class PipelineStage(str, Enum):
    SUBMITTED = "SUBMITTED"
    ENTITY_PROCESSING = "ENTITY_PROCESSING"
    ENTITY_CURATION = "ENTITY_CURATION"
    RELATION_PROCESSING = "RELATION_PROCESSING"
    RELATION_CURATION = "RELATION_CURATION"
    DB_WRITE = "DB_WRITE"
    COMPLETED = "COMPLETED"


@dataclass
class PipelineState:
    journal_entry: JournalEntry
    stage: PipelineStage
    created_at: datetime
    entities_extracted: List[Entity] = None
    entities_curated: List[Entity] = None
    relationships_extracted: List[Relation] = None
    relationships_curated: List[Relation] = None
    error_count: int = 0


# ===== ACTIVITIES (The actual work) =====

@activity.defn
async def extract_entities(journal_entry: JournalEntry) -> List[Entity]:
    """Stage 1-2: Extract standalone and relational entities using LLM"""
    # This will call your Ollama extraction pipeline
    from pipeline.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    entities = await extractor.extract_all_entities(journal_text)
    return [entity.dict() for entity in entities]


@activity.defn
async def extract_relationships(journal_entry: JournalEntry, entities: List[Entity]) -> List[Relation]:
    """Stage 3: Extract relationships between entities"""
    from pipeline.llm_extractor import LLMExtractor

    extractor = LLMExtractor()
    relationships = await extractor.extract_relationships(entities)
    return [rel.dict() for rel in relationships]


@activity.defn
async def submit_entity_curation(journal_entry: JournalEntry, entities: List[Entity]) -> List[Dict[str, Any]]:
    """Human-in-the-loop: Wait for user to curate entities"""
    from minerva_backend.processing.curation_manager import CurationManager

    curation_mgr = CurationManager()

    # Add to curation queue
    await curation_mgr.queue_entity_curation(journal_entry, entities)


@activity.defn
async def wait_for_entity_curation(journal_entry: JournalEntry, entities: List[Entity]) -> List[Dict[str, Any]]:
    """Human-in-the-loop: Wait for user to curate entities"""
    from minerva_backend.processing.curation_manager import CurationManager

    curation_mgr = CurationManager()
    # Poll until user completes curation (with heartbeat to keep workflow alive)
    while True:
        result = await curation_mgr.get_entity_curation_result(journal_entry)
        if result:
            return result

        # Temporal heartbeat to prevent timeout
        activity.heartbeat()
        await asyncio.sleep(30)  # Check every 30 seconds


@activity.defn
async def wait_for_relationship_curation(journal_id: str, relationships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Human-in-the-loop: Wait for user to curate relationships"""
    from minerva_backend.processing.curation_manager import CurationManager

    curation_mgr = CurationManager()
    await curation_mgr.queue_relationship_curation(journal_id, relationships)

    while True:
        result = await curation_mgr.get_relationship_curation_result(journal_id)
        if result:
            return result

        activity.heartbeat()
        await asyncio.sleep(30)


@activity.defn
async def write_to_knowledge_graph(journal_id: str, entities: List[Dict[str, Any]],
                                   relationships: List[Dict[str, Any]]) -> bool:
    """Final stage: Write curated data to Neo4j"""
    from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService

    kg_service = KnowledgeGraphService()
    # Convert back to Pydantic models and save
    for entity_data in entities:
        entity = Entity.parse_obj(entity_data)  # You'll need entity factory here
        await db.create_entity(entity)

    for rel_data in relationships:
        # Create relationships in Neo4j
        await db.create_relationship(rel_data)
    kg_service.add_journal_entry()
    return True


# ===== WORKFLOW (The orchestration) =====

@workflow.defn
class JournalProcessingWorkflow:
    """Main workflow that orchestrates the entire 6-stage pipeline"""

    def __init__(self):
        self.state = PipelineState(
            journal_id="",
            stage=PipelineStage.SUBMITTED,
            created_at=datetime.now(UTC)
        )

    @workflow.run
    async def run(self, journal_entry: JournalEntry) -> PipelineState:
        self.state.journal_id = journal_entry.uuid

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
                extract_entities,
                args=[journal_entry],
                schedule_to_close_timeout=timedelta(minutes=60),  # Max 60 min for Entity Extraction
                retry_policy=llm_retry_policy,
            )

            # Stage 3.0: Submit Entities for curation

            # Stage 3: Entity Curation (Human)
            self.state.stage = PipelineStage.ENTITY_CURATION
            self.state.entities_curated = await workflow.execute_activity(
                wait_for_entity_curation,
                args=[journal_entry, self.state.entities_extracted],
                schedule_to_close_timeout=timedelta(days=7),  # User has 7 days
                heartbeat_timeout=timedelta(minutes=2),  # Heartbeat every 2 min
            )

            # Stage 4: Relationship Extraction (LLM)
            self.state.stage = PipelineStage.RELATION_PROCESSING
            self.state.relationships_extracted = await workflow.execute_activity(
                extract_relationships,
                args=[journal_id, self.state.entities_curated],
                schedule_to_close_timeout=timedelta(minutes=10),
                retry_policy=llm_retry_policy,
            )

            # Stage 5: Relationship Curation (Human)
            self.state.stage = PipelineStage.RELATION_CURATION
            self.state.relationships_curated = await workflow.execute_activity(
                wait_for_relationship_curation,
                args=[journal_id, self.state.relationships_extracted],
                schedule_to_close_timeout=timedelta(days=7),
                heartbeat_timeout=timedelta(minutes=2),
            )

            # Stage 6: Database Write
            self.state.stage = PipelineStage.DB_WRITE
            success = await workflow.execute_activity(
                write_to_knowledge_graph,
                args=[journal_id, self.state.entities_curated, self.state.relationships_curated],
                schedule_to_close_timeout=timedelta(minutes=5),
                retry_policy=llm_retry_policy,
            )

            if success:
                self.state.stage = PipelineStage.COMPLETED

        except Exception as e:
            workflow.logger.error(f"Pipeline failed for {journal_id}: {e}")
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

    def __init__(self):
        self.client = None

    async def initialize(self):
        """Connect to Temporal server"""
        self.client = await Client.connect("localhost:7233")

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
        return await handle.query(JournalProcessingWorkflow.get_state)

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
    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="minerva-pipeline",
        workflows=[JournalProcessingWorkflow],
        activities=[
            extract_entities,
            extract_relationships,
            wait_for_entity_curation,
            wait_for_relationship_curation,
            write_to_knowledge_graph
        ]
    )

    print("🚀 Minerva pipeline worker started...")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(run_worker())
