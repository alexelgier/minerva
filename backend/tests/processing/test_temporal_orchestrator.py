# tests/processing/test_temporal_orchestrator.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from minerva_backend.graph.models.documents import Span
from minerva_backend.graph.models.entities import Person
from minerva_backend.graph.models.relations import Relation
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping
from minerva_backend.processing.temporal_orchestrator import (
    JournalProcessingWorkflow,
    PipelineActivities,
    PipelineStage,
    PipelineOrchestrator
)


@pytest_asyncio.fixture
async def local_workflow_environment():
    env = await WorkflowEnvironment.start_local(
        data_converter=pydantic_data_converter
    )
    yield env


@pytest.fixture
def sample_entity_span_mappings(sample_journal_entry):
    """Create sample EntitySpanMapping objects with proper structure"""
    # Create Person entity
    person = Person(
        uuid=str(uuid4()),
        name="María",
        occupation="unknown",
        summary="summary María",
        summary_short="summary short María"
    )
    person_span = Span(
        uuid=str(uuid4()),
        text="María",
        start=16,
        end=21,
        parent_document_uuid=sample_journal_entry.uuid
    )
    person_mapping = EntitySpanMapping(
        entity=person,
        spans={person_span}
    )
    person2 = Person(
        uuid=str(uuid4()),
        name="Jose",
        occupation="unknown",
        summary="summary Jose",
        summary_short="summary short Jose"
    )
    person_span2 = Span(
        uuid=str(uuid4()),
        text="Jose",
        start=6,
        end=26,
        parent_document_uuid=sample_journal_entry.uuid
    )
    person_mapping2 = EntitySpanMapping(
        entity=person2,
        spans={person_span2}
    )

    return [person_mapping, person_mapping2]


@pytest.fixture
def sample_relation_span_mappings(sample_entity_span_mappings, sample_journal_entry):
    """Create sample RelationSpanContextMapping objects"""
    relation = Relation(
        uuid=str(uuid4()),
        source=sample_entity_span_mappings[0].entity.uuid,  # Person
        target=sample_entity_span_mappings[1].entity.uuid,  # Person2
        proposed_types=["IS_FRIEND", "IS_COWORKER"],
        summary_short="summary short",
        summary="summary is longer than the summary short"
    )

    relation_span = Span(
        uuid=str(uuid4()),
        text="hablé con María",
        start=5,
        end=20,
        parent_document_uuid=sample_journal_entry.uuid
    )

    relation_mapping = RelationSpanContextMapping(
        relation=relation,
        spans={relation_span}
    )

    return [relation_mapping]


class TestJournalProcessingWorkflow:
    """Test the main journal processing workflow"""

    @pytest.mark.asyncio
    async def test_successful_workflow_execution(
            self,
            local_workflow_environment,
            sample_journal_entry,
            sample_entity_span_mappings,
            sample_relation_span_mappings
    ):
        """Test complete workflow execution with mocked activities"""
        async with local_workflow_environment as env:
            # Create mock activities that return proper data structures
            mock_activities = MagicMock(spec=PipelineActivities)
            mock_activities.extract_entities = AsyncMock(return_value=sample_entity_span_mappings)
            mock_activities.extract_relationships = AsyncMock(return_value=sample_relation_span_mappings)
            mock_activities.submit_entity_curation = AsyncMock(return_value=None)
            mock_activities.wait_for_entity_curation = AsyncMock(return_value=sample_entity_span_mappings)
            mock_activities.submit_relationship_curation = AsyncMock(return_value=None)
            mock_activities.wait_for_relationship_curation = AsyncMock(return_value=sample_relation_span_mappings)
            mock_activities.write_to_knowledge_graph = AsyncMock(return_value=True)

            # Create worker with mocked activities
            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[JournalProcessingWorkflow],
                activities=[
                    mock_activities.extract_entities,
                    mock_activities.extract_relationships,
                    mock_activities.submit_entity_curation,
                    mock_activities.wait_for_entity_curation,
                    mock_activities.submit_relationship_curation,
                    mock_activities.wait_for_relationship_curation,
                    mock_activities.write_to_knowledge_graph,
                ]
            )

            async with worker:
                # Execute workflow
                result = await env.client.execute_workflow(
                    JournalProcessingWorkflow.run,
                    sample_journal_entry,
                    id=f"test-{uuid4()}",
                    task_queue="test-queue"
                )

                # Verify final state
                assert result.stage == PipelineStage.COMPLETED
                assert len(result.entities_curated) == 2
                assert len(result.relationships_curated) == 1
                assert result.error_count == 0

                # Verify all activities were called
                mock_activities.extract_entities.assert_called_once_with(sample_journal_entry)
                mock_activities.extract_relationships.assert_called_once()
                mock_activities.write_to_knowledge_graph.assert_called_once()

    @pytest.mark.asyncio
    async def test_entity_extraction_failure_with_retry(self, sample_journal_entry):
        """Test that entity extraction retries on failure"""

        async with WorkflowEnvironment(data_converter=pydantic_data_converter) as env:
            mock_activities = MagicMock(spec=PipelineActivities)

            # First two calls fail, third succeeds
            mock_activities.extract_entities = AsyncMock(
                side_effect=[
                    Exception("LLM timeout"),
                    Exception("LLM error"),
                    []  # Success on third try
                ]
            )
            mock_activities.submit_entity_curation = AsyncMock(return_value=None)
            mock_activities.wait_for_entity_curation = AsyncMock(return_value=[])
            mock_activities.extract_relationships = AsyncMock(return_value=[])
            mock_activities.submit_relationship_curation = AsyncMock(return_value=None)
            mock_activities.wait_for_relationship_curation = AsyncMock(return_value=[])
            mock_activities.write_to_knowledge_graph = AsyncMock(return_value=True)

            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[JournalProcessingWorkflow],
                activities=[
                    mock_activities.extract_entities,
                    mock_activities.extract_relationships,
                    mock_activities.submit_entity_curation,
                    mock_activities.wait_for_entity_curation,
                    mock_activities.submit_relationship_curation,
                    mock_activities.wait_for_relationship_curation,
                    mock_activities.write_to_knowledge_graph,
                ]
            )

            async with worker:
                result = await env.client.execute_workflow(
                    JournalProcessingWorkflow.run,
                    sample_journal_entry,
                    id=f"test-retry-{uuid4()}",
                    task_queue="test-queue"
                )

                # Should complete successfully after retries
                assert result.stage == PipelineStage.COMPLETED
                # Verify extract_entities was called 3 times (2 failures + 1 success)
                assert mock_activities.extract_entities.call_count == 3

    @pytest.mark.asyncio
    async def test_workflow_query_state(self, local_workflow_environment, sample_journal_entry):
        """Test querying workflow state during execution"""

        async with local_workflow_environment as env:
            # Create activities that simulate slow human curation
            mock_activities = MagicMock(spec=PipelineActivities)
            mock_activities.extract_entities = AsyncMock(return_value=[])
            mock_activities.submit_entity_curation = AsyncMock(return_value=None)

            # This will block until we signal it
            curation_event = asyncio.Event()

            async def wait_for_curation(*args):
                await curation_event.wait()
                return []

            mock_activities.wait_for_entity_curation = AsyncMock(side_effect=wait_for_curation)
            mock_activities.extract_relationships = AsyncMock(return_value=[])
            mock_activities.submit_relationship_curation = AsyncMock(return_value=None)
            mock_activities.wait_for_relationship_curation = AsyncMock(return_value=[])
            mock_activities.write_to_knowledge_graph = AsyncMock(return_value=True)

            worker = Worker(
                env.client,
                task_queue="test-queue",
                workflows=[JournalProcessingWorkflow],
                activities=[
                    mock_activities.extract_entities,
                    mock_activities.extract_relationships,
                    mock_activities.submit_entity_curation,
                    mock_activities.wait_for_entity_curation,
                    mock_activities.submit_relationship_curation,
                    mock_activities.wait_for_relationship_curation,
                    mock_activities.write_to_knowledge_graph,
                ]
            )

            async with worker:
                # Start workflow
                handle = await env.client.start_workflow(
                    JournalProcessingWorkflow.run,
                    sample_journal_entry,
                    id=f"test-query-{uuid4()}",
                    task_queue="test-queue"
                )

                # Let it get to entity curation
                await asyncio.sleep(0.1)

                # Query state - should be waiting for entity curation
                state = await handle.query("get_state")
                assert state.stage == PipelineStage.WAIT_ENTITY_CURATION
                assert state.entities_extracted == []

                # Complete the curation
                curation_event.set()

                # Wait for workflow completion
                final_result = await handle.result()
                assert final_result.stage == PipelineStage.COMPLETED


class TestPipelineActivitiesUnit:
    """Unit tests for individual activities with proper mocking of your container"""

    @pytest.fixture
    def activities(self):
        return PipelineActivities()

    @pytest.mark.asyncio
    async def test_extract_entities_activity(self, activities, sample_journal_entry, sample_entity_span_mappings):
        """Test entity extraction activity in isolation"""

        # Mock the container and its services
        with patch('minerva_backend.containers.Container') as mock_container_class:
            mock_container = MagicMock()
            mock_extraction_service = AsyncMock()
            mock_extraction_service.extract_entities.return_value = sample_entity_span_mappings
            mock_container.extraction_service.return_value = mock_extraction_service
            mock_container_class.return_value = mock_container

            # Execute activity
            result = await activities.extract_entities(sample_journal_entry)

            # Verify
            assert len(result) == 2
            assert result[0].entity.name == "María"
            assert result[1].entity.name == "Jose"
            mock_extraction_service.extract_entities.assert_called_once_with(sample_journal_entry)

    @pytest.mark.asyncio
    async def test_submit_entity_curation_activity(
            self,
            activities,
            sample_journal_entry,
            sample_entity_span_mappings
    ):
        """Test entity curation submission"""

        with patch('minerva_backend.containers.Container') as mock_container_class:
            mock_container = MagicMock()
            mock_curation_manager = AsyncMock()
            mock_container.curation_manager.return_value = mock_curation_manager
            mock_container_class.return_value = mock_container

            # Execute activity
            await activities.submit_entity_curation(sample_journal_entry, sample_entity_span_mappings)

            # Verify curation manager was called
            mock_curation_manager.queue_entities_for_curation.assert_called_once_with(
                sample_journal_entry.uuid,
                sample_journal_entry.entry_text,
                sample_entity_span_mappings
            )

    @pytest.mark.asyncio
    async def test_wait_for_entity_curation_activity(
            self,
            activities,
            sample_journal_entry,
            sample_entity_span_mappings
    ):
        """Test waiting for entity curation completion"""

        with patch('minerva_backend.containers.Container') as mock_container_class:
            mock_container = MagicMock()
            mock_curation_manager = AsyncMock()

            # Simulate: first check returns None, second returns ENTITIES_DONE
            mock_curation_manager.get_journal_status.side_effect = [None, "ENTITIES_DONE"]
            mock_curation_manager.get_accepted_entities_with_spans.return_value = sample_entity_span_mappings

            mock_container.curation_manager.return_value = mock_curation_manager
            mock_container_class.return_value = mock_container

            # Execute activity (this will loop twice due to our side_effect)
            with patch('asyncio.sleep', new_callable=AsyncMock):  # Speed up the test
                result = await activities.wait_for_entity_curation(sample_journal_entry)

            # Verify
            assert len(result) == 2
            assert mock_curation_manager.get_journal_status.call_count == 2
            mock_curation_manager.get_accepted_entities_with_spans.assert_called_once_with(
                sample_journal_entry.uuid
            )

    @pytest.mark.asyncio
    async def test_write_to_knowledge_graph_activity(
            self,
            activities,
            sample_journal_entry,
            sample_entity_span_mappings,
            sample_relation_span_mappings
    ):
        """Test final knowledge graph write activity"""

        with patch('minerva_backend.containers.Container') as mock_container_class:
            mock_container = MagicMock()
            mock_kg_service = MagicMock()
            mock_container.kg_service.return_value = mock_kg_service
            mock_container_class.return_value = mock_container

            # Execute activity
            result = await activities.write_to_knowledge_graph(
                sample_journal_entry,
                sample_entity_span_mappings,
                sample_relation_span_mappings
            )

            # Verify
            assert result is True
            mock_kg_service.add_journal_entry.assert_called_once_with(
                sample_journal_entry,
                sample_entity_span_mappings,
                sample_relation_span_mappings
            )


class TestPipelineOrchestratorIntegration:
    """Integration tests for the orchestrator"""

    @pytest.mark.asyncio
    async def test_orchestrator_submit_and_status(self, local_workflow_environment, sample_journal_entry):
        """Test submitting journal and checking status through orchestrator"""

        async with local_workflow_environment as env:
            # Create orchestrator
            orchestrator = PipelineOrchestrator(env.client.service_client.target)
            orchestrator.client = env.client

            # Create fast-completing mock activities
            mock_activities = self._create_fast_mock_activities()

            worker = Worker(
                env.client,
                task_queue="minerva-pipeline",
                workflows=[JournalProcessingWorkflow],
                activities=list(mock_activities.values())
            )

            async with worker:
                # Submit journal
                workflow_id = await orchestrator.submit_journal(sample_journal_entry)

                assert workflow_id.startswith(f"journal-{sample_journal_entry.date}")

                # Wait a moment for workflow to start
                await asyncio.sleep(0.1)

                # Check initial status
                status = await orchestrator.get_pipeline_status(workflow_id)
                assert status.stage in [PipelineStage.SUBMITTED, PipelineStage.ENTITY_PROCESSING]

                # Wait for completion
                handle = env.client.get_workflow_handle(workflow_id)
                final_result = await handle.result()

                assert final_result.stage == PipelineStage.COMPLETED

    def _create_fast_mock_activities(self):
        """Create mock activities that complete quickly for integration tests"""
        activities = {}

        activities["extract_entities"] = AsyncMock(return_value=[])
        activities["extract_relationships"] = AsyncMock(return_value=[])
        activities["submit_entity_curation"] = AsyncMock(return_value=None)
        activities["wait_for_entity_curation"] = AsyncMock(return_value=[])
        activities["submit_relationship_curation"] = AsyncMock(return_value=None)
        activities["wait_for_relationship_curation"] = AsyncMock(return_value=[])
        activities["write_to_knowledge_graph"] = AsyncMock(return_value=True)

        return activities
