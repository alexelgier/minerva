"""Pipeline status and monitoring endpoints."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from minerva_backend.utils.logging import get_logger

from ..dependencies import get_pipeline_orchestrator, validate_workflow_id
from ..exceptions import NotFoundError, handle_errors
from ..models import PendingPipelinesResponse, PipelineStatusResponse

logger = get_logger("minerva_backend.api.pipeline")
router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/status/{workflow_id}", response_model=PipelineStatusResponse)
@handle_errors(404)
async def get_pipeline_status(
    workflow_id: str = Depends(validate_workflow_id),
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> PipelineStatusResponse:
    """
    Get the current status of a specific pipeline workflow.

    Returns detailed information about the workflow's current stage,
    completion status, and any errors encountered.
    """
    try:
        status = await orchestrator.get_pipeline_status(workflow_id)

        if not status:
            raise NotFoundError("Workflow", workflow_id)

        logger.debug(
            f"Retrieved status for workflow {workflow_id}: {status.stage.value if hasattr(status, 'stage') else 'unknown'}"
        )

        # Enhance status with additional metadata
        status_dict = status.model_dump()
        status_dict.update(
            {
                "workflow_id": workflow_id,
                "retrieval_timestamp": "now",  # Could be actual timestamp
            }
        )

        return PipelineStatusResponse(workflow_id=workflow_id, status=status_dict)

    except Exception as e:
        logger.error(f"Failed to get pipeline status for {workflow_id}: {e}")
        raise NotFoundError("Workflow", workflow_id)


@router.get("/all-pending", response_model=PendingPipelinesResponse)
@handle_errors(500)
async def get_all_pending_pipelines(
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> PendingPipelinesResponse:
    """
    Get all pipelines that are currently pending human action.

    This includes workflows waiting for entity curation, relationship curation,
    or other human-in-the-loop steps.
    """
    try:
        # This method might need to be implemented in the orchestrator
        # For now, returning empty list as in original implementation
        pending_workflows: List[Dict[str, Any]] = (
            []
        )  # await orchestrator.get_pending_workflows()

        logger.info(f"Found {len(pending_workflows)} pending pipelines")

        return PendingPipelinesResponse(
            pending_pipelines=pending_workflows, total_count=len(pending_workflows)
        )

    except Exception as e:
        logger.error(f"Failed to get pending pipelines: {e}")
        raise


@router.get("/recent")
@handle_errors(500)
async def get_recent_pipelines(
    limit: int = 10,
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> Dict[str, Any]:
    """
    Get recently completed or active pipeline workflows.

    Useful for monitoring system activity and debugging.
    """
    try:
        # This would need to be implemented in the orchestrator
        # For now, returning placeholder structure
        recent_workflows: List[Dict[str, Any]] = []

        return {
            "success": True,
            "recent_workflows": recent_workflows,
            "limit": limit,
            "message": f"Retrieved {len(recent_workflows)} recent workflows",
        }

    except Exception as e:
        logger.error(f"Failed to get recent pipelines: {e}")
        raise


@router.delete("/{workflow_id}/cancel")
@handle_errors(404)
async def cancel_pipeline(
    workflow_id: str = Depends(validate_workflow_id),
    orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> Dict[str, Any]:
    """
    Cancel a running pipeline workflow.

    This will attempt to gracefully stop the workflow and clean up
    any pending curation tasks.
    """
    try:
        # This method would need to be implemented in the orchestrator
        success = False  # await orchestrator.cancel_workflow(workflow_id)

        if not success:
            raise NotFoundError("Workflow", workflow_id)

        logger.info(f"Cancelled workflow {workflow_id}")

        return {
            "success": True,
            "workflow_id": workflow_id,
            "message": "Workflow cancelled successfully",
        }

    except Exception as e:
        logger.error(f"Failed to cancel workflow {workflow_id}: {e}")
        raise NotFoundError("Workflow", workflow_id)
