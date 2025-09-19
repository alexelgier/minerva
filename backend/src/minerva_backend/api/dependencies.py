"""Shared dependencies for FastAPI dependency injection."""
import asyncio
import logging
from typing import Optional
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, HTTPException

from minerva_backend.containers import Container
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from .exceptions import ServiceUnavailableError, ProcessingError
from ..config import settings

logger = logging.getLogger(__name__)


@inject
async def get_db_connection(
        db: Neo4jConnection = Depends(Provide[Container.db_connection])
) -> Neo4jConnection:
    """Get Neo4j database connection with health check."""
    if not db.health_check():
        raise ServiceUnavailableError("Neo4j Database", "Database connection failed")
    return db


@inject
async def get_curation_manager(
        manager: CurationManager = Depends(Provide[Container.curation_manager])
) -> CurationManager:
    """Get curation manager with initialization check."""
    try:
        # Verify the curation manager is properly initialized
        await manager.get_curation_stats()
        return manager
    except Exception as e:
        logger.error(f"Curation manager error: {e}")
        raise ServiceUnavailableError("Curation Manager", str(e))


@inject
async def get_pipeline_orchestrator(
        orchestrator: PipelineOrchestrator = Depends(Provide[Container.pipeline_orchestrator])
) -> PipelineOrchestrator:
    """Get pipeline orchestrator with connectivity check."""
    try:
        # This could include a simple connectivity test to Temporal
        return orchestrator
    except Exception as e:
        logger.error(f"Pipeline orchestrator error: {e}")
        raise ServiceUnavailableError("Pipeline Orchestrator", str(e))


async def poll_for_initial_status(
        orchestrator: PipelineOrchestrator,
        workflow_id: str
) -> Optional[dict]:
    """
    Poll for initial workflow status with timeout.

    Replaces the arbitrary asyncio.sleep(2) with proper polling.
    """
    for attempt in range(settings.max_status_poll_attempts):
        try:
            status = await orchestrator.get_pipeline_status(workflow_id)
            if status and hasattr(status, 'stage') and status.stage:
                logger.info(f"Workflow {workflow_id} status: {status.stage.value}")
                return status.model_dump()
        except Exception as e:
            logger.warning(f"Status poll attempt {attempt + 1} failed: {e}")

        if attempt < settings.max_status_poll_attempts - 1:
            await asyncio.sleep(settings.status_poll_interval)

    logger.warning(
        f"Failed to get initial status for workflow {workflow_id} after {settings.max_status_poll_attempts} attempts")
    return None


def validate_journal_id(journal_id: str) -> str:
    """Validate journal ID format."""
    if not journal_id or len(journal_id) < 10:
        raise HTTPException(status_code=400, detail="Invalid journal ID format")
    return journal_id


def validate_entity_id(entity_id: str) -> str:
    """Validate entity ID format."""
    if not entity_id or len(entity_id) < 10:
        raise HTTPException(status_code=400, detail="Invalid entity ID format")
    return entity_id


def validate_relationship_id(relationship_id: str) -> str:
    """Validate relationship ID format."""
    if not relationship_id or len(relationship_id) < 10:
        raise HTTPException(status_code=400, detail="Invalid relationship ID format")
    return relationship_id


def validate_workflow_id(workflow_id: str) -> str:
    """Validate workflow ID format."""
    if not workflow_id:
        raise HTTPException(status_code=400, detail="Invalid workflow ID format")
    return workflow_id