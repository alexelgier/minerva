"""Human-in-the-loop curation endpoints."""

import logging

from fastapi import APIRouter, Depends

from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.utils.logging import get_logger

from ..dependencies import (
    get_curation_manager,
    validate_entity_id,
    validate_journal_id,
    validate_relationship_id,
)
from ..exceptions import NotFoundError, ValidationError, handle_errors
from ..models import (
    CurationAction,
    CurationStatsResponse,
    PendingCurationResponse,
    SuccessResponse,
)

logger = get_logger("minerva_backend.api.curation")
router = APIRouter(prefix="/api/curation", tags=["curation"])


@router.get("/pending", response_model=PendingCurationResponse)
@handle_errors(500)
async def get_pending_curation(
    curation_manager: CurationManager = Depends(get_curation_manager),
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
            journal_entries=pending_journals, stats=stats_model
        )

    except Exception as e:
        logger.error(f"Failed to get pending curation tasks: {e}")
        raise


@router.get("/stats", response_model=CurationStatsResponse)
@handle_errors(500)
async def get_curation_stats(
    curation_manager: CurationManager = Depends(get_curation_manager),
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
    curation_manager: CurationManager = Depends(get_curation_manager),
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
            workflow_id=None,
            journal_id=journal_id,
            data={"phase": "entity", "status": "completed"},
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
    curation_manager: CurationManager = Depends(get_curation_manager),
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
                curated_data=action_data.curated_data,
            )
            if not updated_uuid:
                raise NotFoundError("Entity", entity_id)
            message = "Entity accepted and updated"

        else:  # reject
            success = await curation_manager.reject_entity(
                journal_uuid=journal_id, entity_uuid=entity_id
            )
            if not success:
                raise NotFoundError("Entity", entity_id)
            message = "Entity rejected"
            updated_uuid = None  # No UUID for rejected entities

        logger.info(
            f"Entity {entity_id} {action_data.action}ed for journal {journal_id}"
        )

        return SuccessResponse(
            message=message,
            workflow_id=None,
            journal_id=journal_id,
            data={
                "entity_id": entity_id,
                "action": action_data.action,
                "updated_uuid": updated_uuid,
            },
        )

    except Exception as e:
        logger.error(f"Failed to handle entity curation: {e}")
        raise


# ===== RELATIONSHIP CURATION ENDPOINTS =====


@router.post("/relationships/{journal_id}/complete", response_model=SuccessResponse)
@handle_errors(404)
async def complete_relationship_curation(
    journal_id: str = Depends(validate_journal_id),
    curation_manager: CurationManager = Depends(get_curation_manager),
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
            workflow_id=None,
            journal_id=journal_id,
            data={"phase": "relationship", "status": "completed"},
        )

    except Exception as e:
        logger.error(f"Failed to complete relationship curation for {journal_id}: {e}")
        raise


@router.post(
    "/relationships/{journal_id}/{relationship_id}", response_model=SuccessResponse
)
@handle_errors(404)
async def handle_relationship_curation(
    action_data: CurationAction,
    journal_id: str = Depends(validate_journal_id),
    relationship_id: str = Depends(validate_relationship_id),
    curation_manager: CurationManager = Depends(get_curation_manager),
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
                curated_data=action_data.curated_data,
            )
            if not updated_uuid:
                raise NotFoundError("Relationship", relationship_id)
            message = "Relationship accepted and updated"

        else:  # reject
            success = await curation_manager.reject_relationship(
                journal_uuid=journal_id, relationship_uuid=relationship_id
            )
            if not success:
                raise NotFoundError("Relationship", relationship_id)
            message = "Relationship rejected"
            updated_uuid = None  # No UUID for rejected relationships

        logger.info(
            f"Relationship {relationship_id} {action_data.action}ed for journal {journal_id}"
        )

        return SuccessResponse(
            message=message,
            workflow_id=None,
            journal_id=journal_id,
            data={
                "relationship_id": relationship_id,
                "action": action_data.action,
                "updated_uuid": updated_uuid,
            },
        )

    except Exception as e:
        logger.error(f"Failed to handle relationship curation: {e}")
        raise


# ===== QUOTE CURATION ENDPOINTS =====


@router.get("/quotes/pending")
@handle_errors(500)
async def get_pending_quote_workflows(
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get all pending quote parsing workflows."""
    workflows = await curation_manager.get_pending_quote_workflows()
    return {"workflows": workflows}


@router.get("/quotes/{workflow_id}/items")
@handle_errors(404)
async def get_quote_curation_items(
    workflow_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get all quote curation items for a workflow."""
    items = await curation_manager.get_quote_curation_items_for_workflow(workflow_id)
    return {"workflow_id": workflow_id, "items": items}


@router.post("/quotes/{workflow_id}/complete", response_model=SuccessResponse)
@handle_errors(404)
async def complete_quote_workflow(
    workflow_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Mark quote workflow as completed (signals Temporal to proceed)."""
    await curation_manager.complete_quote_workflow(workflow_id)
    return SuccessResponse(
        message="Quote workflow completed",
        workflow_id=workflow_id,
        journal_id=None,
        data={"status": "completed"},
    )


@router.post("/quotes/{workflow_id}/{quote_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_quote_curation(
    action_data: CurationAction,
    workflow_id: str,
    quote_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Accept or reject a quote item."""
    if action_data.action == "accept":
        success = await curation_manager.accept_quote_item(
            workflow_id, quote_id, action_data.curated_data
        )
        message = "Quote accepted"
    else:
        success = await curation_manager.reject_quote_item(workflow_id, quote_id)
        message = "Quote rejected"
    if not success:
        raise NotFoundError("Quote", quote_id)
    return SuccessResponse(
        message=message,
        workflow_id=workflow_id,
        journal_id=None,
        data={"quote_id": quote_id, "action": action_data.action},
    )


# ===== CONCEPT CURATION ENDPOINTS =====


@router.get("/concepts/pending")
@handle_errors(500)
async def get_pending_concept_workflows(
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get all pending concept extraction workflows."""
    workflows = await curation_manager.get_pending_concept_workflows()
    return {"workflows": workflows}


@router.get("/concepts/{workflow_id}/items")
@handle_errors(404)
async def get_concept_curation_items(
    workflow_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get concept and relation items for a workflow."""
    concepts = await curation_manager.get_concept_curation_items_for_workflow(workflow_id)
    relations = await curation_manager.get_concept_relation_items_for_workflow(workflow_id)
    return {"workflow_id": workflow_id, "concepts": concepts, "relations": relations}


@router.post("/concepts/{workflow_id}/complete", response_model=SuccessResponse)
@handle_errors(404)
async def complete_concept_workflow(
    workflow_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Mark concept workflow as completed."""
    await curation_manager.complete_concept_workflow(workflow_id)
    return SuccessResponse(
        message="Concept workflow completed",
        workflow_id=workflow_id,
        journal_id=None,
        data={"status": "completed"},
    )


@router.post("/concepts/{workflow_id}/{concept_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_concept_curation(
    action_data: CurationAction,
    workflow_id: str,
    concept_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Accept or reject a concept item."""
    if action_data.action == "accept":
        success = await curation_manager.accept_concept_item(
            workflow_id, concept_id, action_data.curated_data
        )
        message = "Concept accepted"
    else:
        success = await curation_manager.reject_concept_item(workflow_id, concept_id)
        message = "Concept rejected"
    if not success:
        raise NotFoundError("Concept", concept_id)
    return SuccessResponse(
        message=message,
        workflow_id=workflow_id,
        journal_id=None,
        data={"concept_id": concept_id, "action": action_data.action},
    )


@router.post("/concepts/{workflow_id}/relations/{relation_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_concept_relation_curation(
    action_data: CurationAction,
    workflow_id: str,
    relation_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Accept or reject a concept relation item."""
    if action_data.action == "accept":
        success = await curation_manager.accept_concept_relation_item(
            workflow_id, relation_id, action_data.curated_data
        )
        message = "Concept relation accepted"
    else:
        success = await curation_manager.reject_concept_relation_item(
            workflow_id, relation_id
        )
        message = "Concept relation rejected"
    if not success:
        raise NotFoundError("Concept relation", relation_id)
    return SuccessResponse(
        message=message,
        workflow_id=workflow_id,
        journal_id=None,
        data={"relation_id": relation_id, "action": action_data.action},
    )


# ===== INBOX CLASSIFICATION ENDPOINTS =====


@router.get("/inbox/pending")
@handle_errors(500)
async def get_pending_inbox_workflows(
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get workflow IDs with pending inbox classification items."""
    workflow_ids = await curation_manager.get_pending_inbox_workflow_ids()
    return {"workflow_ids": workflow_ids}


@router.get("/inbox/{workflow_id}/items")
@handle_errors(404)
async def get_inbox_classification_items(
    workflow_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get all inbox classification items for a workflow."""
    items = await curation_manager.get_inbox_classification_items_for_workflow(workflow_id)
    return {"workflow_id": workflow_id, "items": items}


@router.post("/inbox/{workflow_id}/{item_id}", response_model=SuccessResponse)
@handle_errors(404)
async def handle_inbox_classification_curation(
    action_data: CurationAction,
    workflow_id: str,
    item_id: str,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Accept or reject an inbox classification item."""
    if action_data.action == "accept":
        success = await curation_manager.accept_inbox_classification_item(
            workflow_id, item_id, action_data.curated_data
        )
        message = "Classification accepted"
    else:
        success = await curation_manager.reject_inbox_classification_item(
            workflow_id, item_id
        )
        message = "Classification rejected"
    if not success:
        raise NotFoundError("Inbox classification item", item_id)
    return SuccessResponse(
        message=message,
        workflow_id=workflow_id,
        journal_id=None,
        data={"item_id": item_id, "action": action_data.action},
    )


# ===== NOTIFICATIONS =====


@router.get("/notifications")
@handle_errors(500)
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    curation_manager: CurationManager = Depends(get_curation_manager),
):
    """Get notifications. Use unread_only=true and limit=0 to get only total count."""
    notifications, total = await curation_manager.list_notifications(
        unread_only=unread_only, limit=limit, offset=offset
    )
    return {"notifications": notifications, "total": total}


@router.post("/notifications/{notification_id}/read", response_model=SuccessResponse)
@handle_errors(404)
async def mark_notification_read(
    notification_id: int,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Mark a notification as read."""
    success = await curation_manager.mark_notification_read(notification_id)
    if not success:
        raise NotFoundError("Notification", str(notification_id))
    return SuccessResponse(
        message="Notification marked as read",
        workflow_id=None,
        journal_id=None,
        data={"notification_id": notification_id},
    )


@router.post("/notifications/{notification_id}/dismiss", response_model=SuccessResponse)
@handle_errors(404)
async def mark_notification_dismissed(
    notification_id: int,
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> SuccessResponse:
    """Mark a notification as dismissed."""
    success = await curation_manager.mark_notification_dismissed(notification_id)
    if not success:
        raise NotFoundError("Notification", str(notification_id))
    return SuccessResponse(
        message="Notification dismissed",
        workflow_id=None,
        journal_id=None,
        data={"notification_id": notification_id},
    )


# ===== BULK OPERATIONS =====


@router.post("/bulk/accept-all/{journal_id}", response_model=SuccessResponse)
@handle_errors(404)
async def bulk_accept_all(
    journal_id: str = Depends(validate_journal_id),
    phase: str = "entity",  # or "relationship"
    curation_manager: CurationManager = Depends(get_curation_manager),
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
            workflow_id=None,
            journal_id=journal_id,
            data={"phase": phase, "accepted_count": count},
        )

    except Exception as e:
        logger.error(f"Failed to bulk accept for {journal_id}: {e}")
        raise
