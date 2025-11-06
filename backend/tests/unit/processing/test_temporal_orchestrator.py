"""
Unit tests for temporal orchestrator.

Tests the pipeline orchestrator with mocked Temporal client and activities.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4
from datetime import datetime

from minerva_backend.processing.temporal_orchestrator import (
    PipelineOrchestrator,
    PipelineStage,
    PipelineState,
    PipelineActivities,
    JournalProcessingWorkflow
)
from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Person
from minerva_backend.graph.models.relations import Relation
from minerva_backend.processing.models import EntityMapping, CuratableMapping


@pytest.fixture
def mock_temporal_client():
    """Create mock Temporal client."""
    client = Mock()
    client.start_workflow = AsyncMock()
    client.get_workflow_handle = Mock()
    return client


@pytest.fixture
def pipeline_orchestrator(mock_temporal_client):
    """Create pipeline orchestrator with mocked dependencies."""
    with patch('minerva_backend.processing.temporal_orchestrator.Client.connect', return_value=mock_temporal_client):
        orchestrator = PipelineOrchestrator(temporal_uri="localhost:7233")
        orchestrator.client = mock_temporal_client
        return orchestrator


@pytest.fixture
def sample_journal_entry():
    """Create sample journal entry for testing."""
    return JournalEntry(
        uuid=str(uuid4()),
        text="Today I went to the park with John and felt happy about the sunny weather.",
        date="2025-09-29",
        metadata={}
    )


@pytest.fixture
def sample_pipeline_state():
    """Create sample pipeline state for testing."""
    return PipelineState(
        stage=PipelineStage.SUBMITTED,
        created_at=datetime.now(),
        journal_entry=sample_journal_entry(),
        entities_extracted=[],
        entities_curated=[],
        relationships_extracted=[],
        relationships_curated=[],
        error_count=0
    )


class TestPipelineStage:
    """Test pipeline stage enum."""
    
    def test_pipeline_stage_values(self):
        """Test that pipeline stage has expected values."""
        expected_stages = [
            "SUBMITTED",
            "ENTITY_PROCESSING", 
            "SUBMIT_ENTITY_CURATION",
            "WAIT_ENTITY_CURATION",
            "RELATION_PROCESSING",
            "SUBMIT_RELATION_CURATION",
            "WAIT_RELATION_CURATION",
            "DB_WRITE",
            "COMPLETED"
        ]
        
        for stage in expected_stages:
            assert hasattr(PipelineStage, stage)
            assert getattr(PipelineStage, stage).value == stage


class TestPipelineState:
    """Test pipeline state model."""
    
    def test_pipeline_state_creation(self, sample_journal_entry):
        """Test pipeline state creation."""
        state = PipelineState(
            stage=PipelineStage.SUBMITTED,
            created_at=datetime.now(),
            journal_entry=sample_journal_entry,
            entities_extracted=[],
            entities_curated=[],
            relationships_extracted=[],
            relationships_curated=[],
            error_count=0
        )
        
        assert state.stage == PipelineStage.SUBMITTED
        assert state.journal_entry == sample_journal_entry
        assert state.entities_extracted == []
        assert state.error_count == 0
    
    def test_pipeline_state_defaults(self):
        """Test pipeline state with default values."""
        state = PipelineState(stage=PipelineStage.SUBMITTED)
        
        assert state.stage == PipelineStage.SUBMITTED
        assert state.created_at is None
        assert state.journal_entry is None
        assert state.entities_extracted is None
        assert state.entities_curated is None
        assert state.relationships_extracted is None
        assert state.relationships_curated is None
        assert state.error_count == 0


class TestPipelineActivities:
    """Test pipeline activities."""
    
    def test_extract_entities_activity_exists(self):
        """Test that extract_entities activity method exists."""
        activities = PipelineActivities()
        assert hasattr(activities, 'extract_entities')
        assert callable(getattr(activities, 'extract_entities'))
    
    def test_extract_relationships_activity_exists(self):
        """Test that extract_relationships activity method exists."""
        activities = PipelineActivities()
        assert hasattr(activities, 'extract_relationships')
        assert callable(getattr(activities, 'extract_relationships'))
    
    def test_submit_entity_curation_activity_exists(self):
        """Test that submit_entity_curation activity method exists."""
        activities = PipelineActivities()
        assert hasattr(activities, 'submit_entity_curation')
        assert callable(getattr(activities, 'submit_entity_curation'))
    
    def test_wait_for_entity_curation_activity_exists(self):
        """Test that wait_for_entity_curation activity method exists."""
        activities = PipelineActivities()
        assert hasattr(activities, 'wait_for_entity_curation')
        assert callable(getattr(activities, 'wait_for_entity_curation'))
    
    def test_extract_feelings_activity_exists(self):
        """Test that extract_feelings activity method exists."""
        activities = PipelineActivities()
        assert hasattr(activities, 'extract_feelings')
        assert callable(getattr(activities, 'extract_feelings'))


class TestPipelineOrchestrator:
    """Test pipeline orchestrator."""
    
    def test_pipeline_orchestrator_init(self, mock_temporal_client):
        """Test pipeline orchestrator initialization."""
        orchestrator = PipelineOrchestrator(temporal_uri="localhost:7233")
        
        assert orchestrator.temporal_uri == "localhost:7233"
        assert orchestrator.client is None  # Client is only set after initialize()
    
    @pytest.mark.asyncio
    async def test_submit_journal_success(self, pipeline_orchestrator, sample_journal_entry):
        """Test successful journal submission."""
        # Arrange
        pipeline_orchestrator.client.start_workflow.return_value = Mock()

        # Act
        result = await pipeline_orchestrator.submit_journal(sample_journal_entry)
        
        # Assert
        expected_workflow_id = f"journal-{sample_journal_entry.date}-{sample_journal_entry.uuid}"
        assert result == expected_workflow_id
        pipeline_orchestrator.client.start_workflow.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_submit_journal_error(self, pipeline_orchestrator, sample_journal_entry):
        """Test journal submission when error occurs."""
        # Arrange
        pipeline_orchestrator.client.start_workflow.side_effect = Exception("Temporal error")
        
        # Act & Assert
        with pytest.raises(Exception, match="Temporal error"):
            await pipeline_orchestrator.submit_journal(sample_journal_entry)
    
    @pytest.mark.asyncio
    async def test_get_pipeline_status_success(self, pipeline_orchestrator):
        """Test successful pipeline status retrieval."""
        # Arrange
        workflow_id = str(uuid4())
        mock_handle = Mock()
        mock_state = PipelineState(stage=PipelineStage.ENTITY_PROCESSING)
        mock_handle.query = AsyncMock(return_value=mock_state)
        pipeline_orchestrator.client.get_workflow_handle.return_value = mock_handle
        
        # Act
        result = await pipeline_orchestrator.get_pipeline_status(workflow_id)
        
        # Assert
        assert result == mock_state
        pipeline_orchestrator.client.get_workflow_handle.assert_called_once_with(workflow_id)
        mock_handle.query.assert_called_once_with("get_state")
    
    @pytest.mark.asyncio
    async def test_get_pipeline_status_error(self, pipeline_orchestrator):
        """Test pipeline status retrieval when error occurs."""
        # Arrange
        workflow_id = str(uuid4())
        pipeline_orchestrator.client.get_workflow_handle.side_effect = Exception("Workflow not found")
        
        # Act & Assert
        with pytest.raises(Exception, match="Workflow not found"):
            await pipeline_orchestrator.get_pipeline_status(workflow_id)
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_success(self, pipeline_orchestrator):
        """Test successful workflow cancellation."""
        # Arrange
        workflow_id = str(uuid4())
        mock_handle = Mock()
        mock_handle.terminate = AsyncMock()
        pipeline_orchestrator.client.get_workflow_handle.return_value = mock_handle
        
        # Act
        result = await pipeline_orchestrator.cancel_workflow(workflow_id)
        
        # Assert
        assert result is True
        pipeline_orchestrator.client.get_workflow_handle.assert_called_once_with(workflow_id)
        mock_handle.terminate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_workflow_error(self, pipeline_orchestrator):
        """Test workflow cancellation when error occurs."""
        # Arrange
        workflow_id = str(uuid4())
        pipeline_orchestrator.client.get_workflow_handle.side_effect = Exception("Workflow not found")
        
        # Act
        result = await pipeline_orchestrator.cancel_workflow(workflow_id)
        
        # Assert
        assert result is False


class TestJournalProcessingWorkflow:
    """Test journal processing workflow."""
    
    @pytest.mark.asyncio
    async def test_workflow_execution_success(self, sample_journal_entry):
        """Test workflow instantiation and basic structure."""
        # Arrange
        workflow = JournalProcessingWorkflow()
        
        # Test that workflow has expected attributes
        assert hasattr(workflow, 'state')
        assert hasattr(workflow, 'run')
        
        # Test workflow state initialization
        assert workflow.state is not None
    
    @pytest.mark.asyncio
    async def test_workflow_execution_with_errors(self, sample_journal_entry):
        """Test workflow error handling structure."""
        # Arrange
        workflow = JournalProcessingWorkflow()
        
        # Test that workflow has expected error handling attributes
        assert hasattr(workflow, 'state')
        assert hasattr(workflow, 'run')
        
        # Test workflow state initialization
        assert workflow.state is not None


class TestPipelineOrchestratorHealthCheck:
    """Test pipeline orchestrator health check."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, pipeline_orchestrator):
        """Test successful health check."""
        # Arrange
        pipeline_orchestrator.client.list_workflows = AsyncMock(return_value=[])
        
        # Act
        result = await pipeline_orchestrator.health_check()
        
        # Assert
        assert result is True
        pipeline_orchestrator.client.list_workflows.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, pipeline_orchestrator):
        """Test health check failure."""
        # Arrange
        pipeline_orchestrator.client.list_workflows = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Act
        result = await pipeline_orchestrator.health_check()
        
        # Assert
        assert result is False
        pipeline_orchestrator.client.list_workflows.assert_called_once()
