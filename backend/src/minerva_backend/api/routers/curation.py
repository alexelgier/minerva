"""Human-in-the-loop curation endpoints."""
import logging

from fastapi import APIRouter, Depends

from minerva_backend.processing.curation_manager import CurationManager
from ..dependencies import (
    get_curation_manager, validate_journal_id,
    validate_entity_id, validate_relationship_id
)
from ..exceptions import handle_errors, NotFoundError, ValidationError
from ..models import (
    CurationAction, SuccessResponse, PendingCurationResponse,
    CurationStatsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/curation", tags=["curation"])


@router.get("/pending", response_model=PendingCurationResponse)
@handle_errors(500)
async def get_pending_curation(
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> PendingCurationResponse:
    """
    Get all pending curation tasks across all journal entries.

    Returns both entity and relationship curation tasks that require
    human review and approval.
    """
    try:
        pending_journals = await curation_manager.get_all_pending_curation_tasks()
        stats_model = await curation_manager.get_curation_stats()

        return PendingCurationResponse(
            journal_entry=pending_journals,
            stats=stats_model
        )

    except Exception as e:
        logger.error(f"Failed to get pending curation tasks: {e}")
        raise


@router.get("/stats", response_model=CurationStatsResponse)
@handle_errors(500)
async def get_curation_stats(
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> CurationStatsResponse:
    """
    Get comprehensive curation statistics.

    Provides insights into curation workload, processing times,
    and system efficiency metrics.
    """
    try:
        stats_dict = await curation_manager.get_curation_stats()
        return CurationStatsResponse(stats=stats_dict)

    except Exception as e:
        logger.error(f"Failed to get curation stats: {e}")
        raise


# ===== ENTITY CURATION ENDPOINTS =====

@router.post("/entities/{journal_id}/complete", response_model=SuccessResponse)
@handle_errors(404)
async def complete_entity_curation(
        journal_id: str = Depends(validate_journal_id),
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> SuccessResponse:
    """
    Mark entity curation phase as complete for a journal entry.

    This signals the workflow to proceed to relationship extraction
    once all entities have been reviewed.
    """
    try:
        await curation_manager.complete_entity_phase(journal_id)

        logger.info(f"Entity curation completed for journal {journal_id}")

        return SuccessResponse(
            message="Entity curation phase completed",
            journal_id=journal_id,
            data={"phase": "entity", "status": "completed"}
        )

    except Exception as e:
        logger.error(f"Failed to complete entity curation for {journal_id}: {e}")
        raise


@router.post("/entities/{journal_id}/{entity_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_entity_curation(
        action_data: CurationAction,
        journal_id: str = Depends(validate_journal_id),
        entity_id: str = Depends(validate_entity_id),
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> SuccessResponse:
    """
    Handle entity curation actions (accept/reject).

    Unified endpoint for both accepting and rejecting entity extractions,
    replacing the previous separate accept/reject endpoints.
    """
    try:
        if action_data.action == "accept":
            if not action_data.curated_data:
                raise ValidationError("Curated data is required for accept action")

            updated_uuid = await curation_manager.accept_entity(
                journal_uuid=journal_id,
                entity_uuid=entity_id,
                curated_data=action_data.curated_data
            )
            message = "Entity accepted and updated"

        else:  # reject
            updated_uuid = await curation_manager.reject_entity(
                journal_uuid=journal_id,
                entity_uuid=entity_id
            )
            message = "Entity rejected"

        if not updated_uuid:
            raise NotFoundError("Entity", entity_id)

        logger.info(f"Entity {entity_id} {action_data.action}ed for journal {journal_id}")

        return SuccessResponse(
            message=message,
            journal_id=journal_id,
            data={
                "entity_id": entity_id,
                "action": action_data.action,
                "updated_uuid": updated_uuid
            }
        )

    except Exception as e:
        logger.error(f"Failed to handle entity curation: {e}")
        raise


# ===== RELATIONSHIP CURATION ENDPOINTS =====


@router.post("/relationships/{journal_id}/complete", response_model=SuccessResponse)
@handle_errors(404)
async def complete_relationship_curation(
        journal_id: str = Depends(validate_journal_id),
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> SuccessResponse:
    """
    Mark relationship curation phase as complete for a journal entry.

    This signals the workflow to proceed to knowledge graph integration
    once all relationships have been reviewed.
    """
    try:
        await curation_manager.complete_relationship_phase(journal_id)

        logger.info(f"Relationship curation completed for journal {journal_id}")

        return SuccessResponse(
            message="Relationship curation phase completed",
            journal_id=journal_id,
            data={"phase": "relationship", "status": "completed"}
        )

    except Exception as e:
        logger.error(f"Failed to complete relationship curation for {journal_id}: {e}")
        raise


@router.post("/relationships/{journal_id}/{relationship_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_relationship_curation(
        action_data: CurationAction,
        journal_id: str = Depends(validate_journal_id),
        relationship_id: str = Depends(validate_relationship_id),
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> SuccessResponse:
    """
    Handle relationship curation actions (accept/reject).

    Unified endpoint for both accepting and rejecting relationship extractions.
    """
    try:
        if action_data.action == "accept":
            if not action_data.curated_data:
                raise ValidationError("Curated data is required for accept action")

            updated_uuid = await curation_manager.accept_relationship(
                journal_uuid=journal_id,
                relationship_uuid=relationship_id,
                curated_data=action_data.curated_data
            )
            message = "Relationship accepted and updated"

        else:  # reject
            updated_uuid = await curation_manager.reject_relationship(
                journal_uuid=journal_id,
                relationship_uuid=relationship_id
            )
            message = "Relationship rejected"

        if not updated_uuid:
            raise NotFoundError("Relationship", relationship_id)

        logger.info(f"Relationship {relationship_id} {action_data.action}ed for journal {journal_id}")

        return SuccessResponse(
            message=message,
            journal_id=journal_id,
            data={
                "relationship_id": relationship_id,
                "action": action_data.action,
                "updated_uuid": updated_uuid
            }
        )

    except Exception as e:
        logger.error(f"Failed to handle relationship curation: {e}")
        raise


# ===== BULK OPERATIONS =====

@router.post("/bulk/accept-all/{journal_id}", response_model=SuccessResponse)
@handle_errors(404)
async def bulk_accept_all(
        journal_id: str = Depends(validate_journal_id),
        phase: str = "entity",  # or "relationship"
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> SuccessResponse:
    """
    Accept all pending curation tasks for a journal entry.

    Useful when the AI extraction quality is high and manual review
    of each item is not necessary.
    """
    try:
        if phase not in ["entity", "relationship"]:
            raise ValidationError("Phase must be 'entity' or 'relationship'")

        # This method would need to be implemented in CurationManager
        count = 0  # await curation_manager.bulk_accept_all(journal_id, phase)

        return SuccessResponse(
            message=f"Bulk accepted {count} {phase} items",
            journal_id=journal_id,
            data={
                "phase": phase,
                "accepted_count": count
            }
        )

    except Exception as e:
        logger.error(f"Failed to bulk accept for {journal_id}: {e}")
        raise
