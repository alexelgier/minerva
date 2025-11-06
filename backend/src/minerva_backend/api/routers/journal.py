"""Journal submission and processing endpoints."""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends

from minerva_models import JournalEntry
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from minerva_backend.utils.logging import get_logger

from ..dependencies import get_pipeline_orchestrator, poll_for_initial_status
from ..exceptions import ProcessingError, handle_errors
from ..models import JournalSubmission, SuccessResponse

logger = get_logger("minerva_backend.api.journal")
router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.post(
    "/submit",
    response_model=SuccessResponse,
    summary="Submit Journal Entry",
    description="Submit a journal entry for processing through the complete Minerva pipeline",
    responses={
        200: {
            "description": "Journal entry successfully submitted for processing",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Journal submitted for processing",
                        "workflow_id": "workflow-uuid-123",
                        "journal_id": "journal-uuid-456",
                        "data": {
                            "workflow_id": "workflow-uuid-123",
                            "journal_id": "journal-uuid-456",
                            "initial_status": "SUBMITTED",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Validation error - invalid journal data",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid date format. Expected YYYY-MM-DD",
                            "status_code": 400,
                        },
                    }
                }
            },
        },
        422: {
            "description": "Processing error - unable to process journal entry",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "PROCESSING_ERROR",
                            "message": "Failed to submit journal entry: LLM service unavailable",
                            "status_code": 422,
                        },
                    }
                }
            },
        },
    },
)
@handle_errors(500)
async def submit_journal(
    submission: JournalSubmission,
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> SuccessResponse:
    """
    Submit a journal entry for processing through the complete Minerva pipeline.

    This endpoint accepts a journal entry and queues it for processing through the
    following stages:

    1. **Entity Extraction**: Uses local LLM to extract entities (people, places, events, etc.)
    2. **Entity Curation**: Human validation and refinement of extracted entities
    3. **Relationship Extraction**: LLM analysis of relationships between entities
    4. **Relationship Curation**: Human validation of extracted relationships
    5. **Knowledge Graph Update**: Integration of validated entities and relationships into Neo4j

    The processing is handled asynchronously using Temporal workflows, allowing for
    long-running operations and human-in-the-loop curation.

    Args:
        submission (JournalSubmission): The journal entry data including text and date

    Returns:
        SuccessResponse: Confirmation of submission with workflow and journal IDs

    Raises:
        ValidationError: If the journal data is invalid (400)
        ProcessingError: If the journal cannot be processed (422)
        InternalError: If an unexpected error occurs (500)

    Example:
        ```python
        submission = JournalSubmission(
            text="Today I went to the park with John. It was a beautiful day.",
            date="2024-01-15"
        )
        response = await submit_journal(submission)
        # Returns workflow_id and journal_id for tracking
        ```

    Note:
        Processing typically takes 2-10 minutes depending on content length and complexity.
        Use the returned workflow_id to check processing status via the pipeline endpoints.
    """
    try:
        # Create journal entry from submission
        journal_entry = JournalEntry.from_text(submission.text, submission.date)
        logger.info(
            "Processing journal entry",
            context={
                "journal_id": journal_entry.uuid,
                "entry_date": submission.date,
                "entry_length": len(submission.text),
                "stage": "journal_submission",
            },
        )

        # Submit to processing pipeline
        workflow_id = await orchestrator.submit_journal(journal_entry)
        logger.info(
            "Journal submitted to processing pipeline",
            context={
                "journal_id": journal_entry.uuid,
                "workflow_id": workflow_id,
                "stage": "journal_submission",
            },
        )

        # Poll for initial status instead of arbitrary sleep
        initial_status = await poll_for_initial_status(orchestrator, workflow_id)

        response_data: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "journal_id": journal_entry.uuid,
        }

        if initial_status:
            response_data["initial_status"] = initial_status

        logger.info(
            "Journal submission completed successfully",
            context={
                "journal_id": journal_entry.uuid,
                "workflow_id": workflow_id,
                "initial_status": initial_status,
                "stage": "journal_submission",
            },
        )

        return SuccessResponse(
            message="Journal submitted for processing",
            workflow_id=workflow_id,
            journal_id=journal_entry.uuid,
            data=response_data,
        )

    except Exception as e:
        logger.error(
            "Failed to submit journal",
            context={
                "journal_id": getattr(journal_entry, "uuid", None),
                "entry_date": submission.date,
                "error": str(e),
                "stage": "journal_submission",
            },
        )
        raise ProcessingError(f"Failed to submit journal entry: {str(e)}")


@router.get(
    "/validate",
    response_model=SuccessResponse,
    summary="Validate Journal Format",
    description="Validate journal entry format without submitting for processing",
    responses={
        200: {
            "description": "Journal format is valid",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Journal format is valid",
                        "data": {
                            "word_count": 15,
                            "character_count": 89,
                            "estimated_processing_time_minutes": 2,
                        },
                    }
                }
            },
        },
        400: {
            "description": "Validation error - invalid journal format",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "Invalid date format. Expected YYYY-MM-DD",
                            "status_code": 400,
                        },
                    }
                }
            },
        },
    },
)
@handle_errors(400)
async def validate_journal_format(text: str, date: str) -> SuccessResponse:
    """
    Validate journal entry format without submitting for processing.

    This endpoint performs client-side validation of journal entry data to ensure
    it meets the required format and constraints before submission. It's useful
    for providing immediate feedback to users about data quality and estimated
    processing time.

    Validation checks include:
    - Date format validation (YYYY-MM-DD)
    - Text content validation (non-empty, reasonable length)
    - Character and word count analysis
    - Estimated processing time calculation

    Args:
        text (str): The journal entry text content
        date (str): The journal entry date in YYYY-MM-DD format

    Returns:
        SuccessResponse: Validation result with metadata about the journal entry

    Raises:
        ValidationError: If the journal format is invalid (400)

    Example:
        ```python
        response = await validate_journal_format(
            text="Today I went to the park with John.",
            date="2024-01-15"
        )
        # Returns validation result with word count and processing time estimate
        ```

    Note:
        This endpoint does not submit the journal for processing. Use the /submit
        endpoint after validation passes.
    """
    try:
        # This will raise validation errors if format is invalid
        submission = JournalSubmission(text=text, date=date)

        # Additional validation checks can go here
        word_count = len(submission.text.split())
        char_count = len(submission.text)

        return SuccessResponse(
            message="Journal format is valid",
            workflow_id=None,
            journal_id=None,
            data={
                "word_count": word_count,
                "character_count": char_count,
                "estimated_processing_time_minutes": max(
                    2, word_count // 100
                ),  # Rough estimate
            },
        )

    except Exception as e:
        logger.warning(f"Journal validation failed: {e}")
        raise ProcessingError(f"Journal validation failed: {str(e)}")
