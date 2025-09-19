"""Journal submission and processing endpoints."""
import logging
from fastapi import APIRouter, Depends

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from ..models import JournalSubmission, SuccessResponse
from ..dependencies import get_pipeline_orchestrator, poll_for_initial_status
from ..exceptions import handle_errors, ProcessingError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.post("/submit", response_model=SuccessResponse)
@handle_errors(500)
async def submit_journal(
        submission: JournalSubmission,
        orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator)
) -> SuccessResponse:
    """
    Submit a journal entry for processing.

    The journal entry will be processed through the complete pipeline:
    1. Entity extraction using local LLM
    2. Human curation of extracted entities
    3. Relationship extraction
    4. Human curation of relationships
    5. Integration into knowledge graph
    """
    try:
        # Create journal entry from submission
        journal_entry = JournalEntry.from_text(submission.text, submission.date)
        logger.info(f"Processing journal entry for date {submission.date}")

        # Submit to processing pipeline
        workflow_id = await orchestrator.submit_journal(journal_entry)
        logger.info(f"Journal submitted with workflow ID: {workflow_id}")

        # Poll for initial status instead of arbitrary sleep
        initial_status = await poll_for_initial_status(orchestrator, workflow_id)

        response_data = {
            "workflow_id": workflow_id,
            "journal_id": journal_entry.uuid
        }

        if initial_status:
            response_data["initial_status"] = initial_status

        return SuccessResponse(
            message="Journal submitted for processing",
            workflow_id=workflow_id,
            journal_id=journal_entry.uuid,
            data=response_data
        )

    except Exception as e:
        logger.error(f"Failed to submit journal: {e}")
        raise ProcessingError(f"Failed to submit journal entry: {str(e)}")


@router.get("/validate")
@handle_errors(400)
async def validate_journal_format(text: str, date: str) -> SuccessResponse:
    """
    Validate journal entry format without submitting for processing.

    Useful for client-side validation before submission.
    """
    try:
        # This will raise validation errors if format is invalid
        submission = JournalSubmission(text=text, date=date)

        # Additional validation checks can go here
        word_count = len(submission.text.split())
        char_count = len(submission.text)

        return SuccessResponse(
            message="Journal format is valid",
            data={
                "word_count": word_count,
                "character_count": char_count,
                "estimated_processing_time_minutes": max(2, word_count // 100)  # Rough estimate
            }
        )

    except Exception as e:
        logger.warning(f"Journal validation failed: {e}")
        raise ProcessingError(f"Journal validation failed: {str(e)}")
