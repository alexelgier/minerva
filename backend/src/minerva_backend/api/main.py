# api/main.py
import asyncio
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Callable, TypeVar
from functools import wraps

from dependency_injector.wiring import inject, Provide
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from minerva_backend.containers import Container
from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator

# Create a type variable for the decorator
T = TypeVar('T')


# --- Decorators for error handling ---
class MinervaHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code, detail)
        self.error_code = error_code


def handle_errors(default_status_code: int = 500):
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as e:
                raise MinervaHTTPException(400, str(e), "VALIDATION_ERROR")
            except ConnectionError as e:
                raise MinervaHTTPException(503, "Service unavailable", "SERVICE_DOWN")
            except Exception as e:
                # TODO Logging
                # logger.error(f"Unhandled error in {func.__name__}: {e}")
                raise MinervaHTTPException(default_status_code, "Internal server error", "INTERNAL_ERROR")

        return wrapper

    return decorator


# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    container: Container = app.state.container
    container.wire(modules=[__name__])
    await container.curation_manager().initialize()
    await container.pipeline_orchestrator().initialize()
    yield
    container.db_connection().close()


container = Container()
backend_app = FastAPI(title="Minerva Backend", version="0.1.0", lifespan=lifespan)
backend_app.state.container = container

backend_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request/Response Models ---
class JournalSubmission(BaseModel):
    date: str
    text: str


class SuccessResponse(BaseModel):
    success: bool
    message: str
    workflow_id: str = None
    journal_id: str = None


class PipelineStatusResponse(BaseModel):
    workflow_id: str
    status: Dict[str, Any]


class PendingPipelinesResponse(BaseModel):
    pending_pipelines: List[Dict[str, Any]]


class ProcessingWindowsResponse(BaseModel):
    default_window: Dict[str, Any]
    currently_active: bool
    next_window: str


# --- Base Endpoint Classes ---
class BaseEndpoint:
    @staticmethod
    @handle_errors(500)
    @inject
    async def submit_journal(
            submission: JournalSubmission,
            orchestrator: PipelineOrchestrator = Depends(Provide[Container.pipeline_orchestrator])
    ) -> SuccessResponse:
        journal_entry = JournalEntry.from_text(submission.text, submission.date)
        workflow_id = await orchestrator.submit_journal(journal_entry)

        await asyncio.sleep(2)
        status = await orchestrator.get_pipeline_status(workflow_id)
        if status:
            print(f"Current pipeline stage: {status.stage.value}")

        return SuccessResponse(
            success=True,
            workflow_id=workflow_id,
            journal_id=journal_entry.uuid,
            message="Journal submitted for processing"
        )


class CurationEndpoint:
    @staticmethod
    @handle_errors(500)
    @inject
    async def handle_entity_action(
            journal_id: str,
            entity_id: str,
            curated_data: Dict[str, Any],
            action: str,
            curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
    ) -> SuccessResponse:
        if action == "accept":
            updated_uuid = await curation_manager.accept_entity(
                journal_uuid=journal_id,
                entity_uuid=entity_id,
                curated_data=curated_data
            )
            message = "Entity accepted"
        else:  # reject
            updated_uuid = await curation_manager.reject_entity(
                journal_uuid=journal_id,
                entity_uuid=entity_id
            )
            message = "Entity rejected"

        if not updated_uuid:
            raise HTTPException(status_code=404, detail="Entity not found or not in PENDING state")

        return SuccessResponse(success=True, message=message, journal_id=journal_id)

    @staticmethod
    @handle_errors(500)
    @inject
    async def handle_relationship_action(
            journal_id: str,
            relationship_id: str,
            curated_data: Dict[str, Any],
            action: str,
            curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
    ) -> SuccessResponse:
        if action == "accept":
            updated_uuid = await curation_manager.accept_relationship(
                journal_uuid=journal_id,
                relationship_uuid=relationship_id,
                curated_data=curated_data
            )
            message = "Relationship accepted"
        else:  # reject
            updated_uuid = await curation_manager.reject_relationship(
                journal_uuid=journal_id,
                relationship_uuid=relationship_id
            )
            message = "Relationship rejected"

        if not updated_uuid:
            raise HTTPException(status_code=404, detail="Relationship not found or not in PENDING state")

        return SuccessResponse(success=True, message=message)

    @staticmethod
    @handle_errors(500)
    @inject
    async def complete_phase(
            journal_id: str,
            phase_type: str,
            curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
    ) -> SuccessResponse:
        if phase_type == "entity":
            await curation_manager.complete_entity_phase(journal_id)
            message = "Entity curation completed"
        else:  # relationship
            await curation_manager.complete_relationship_phase(journal_id)
            message = "Relationship curation completed"

        return SuccessResponse(success=True, message=message)


class ProcessingEndpoint:
    @staticmethod
    @handle_errors(500)
    async def control_processing(action: str) -> SuccessResponse:
        if action == "start":
            message = "Processing started manually"
        else:  # pause
            message = "Processing paused"

        return SuccessResponse(success=True, message=message)


# ===== JOURNAL SUBMISSION ENDPOINTS =====
@backend_app.post("/api/journal/submit", response_model=SuccessResponse)
async def submit_journal(submission: JournalSubmission):
    return await BaseEndpoint.submit_journal(submission)


# ===== PIPELINE STATUS ENDPOINTS =====
@backend_app.get("/api/pipeline/status/{workflow_id}", response_model=PipelineStatusResponse)
@handle_errors(404)
@inject
async def get_pipeline_status(
        workflow_id: str,
        orchestrator: PipelineOrchestrator = Depends(Provide[Container.pipeline_orchestrator])
):
    status = await orchestrator.get_pipeline_status(workflow_id)
    return PipelineStatusResponse(
        workflow_id=workflow_id,
        status=status.model_dump()
    )


@backend_app.get("/api/pipeline/all-pending", response_model=PendingPipelinesResponse)
@handle_errors(500)
@inject
async def get_all_pending_pipelines(
        orchestrator: PipelineOrchestrator = Depends(Provide[Container.pipeline_orchestrator])
):
    return PendingPipelinesResponse(pending_pipelines=[])


# ===== CURATION ENDPOINTS =====
@backend_app.get("/api/curation/pending")
@handle_errors(500)
@inject
async def get_pending_curation(
        curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
):
    return await curation_manager.get_all_pending_curation_tasks()


@backend_app.get("/api/curation/stats")
@handle_errors(500)
@inject
async def get_curation_stats(
        curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
):
    return await curation_manager.get_curation_stats()


# ===== ENTITY CURATION ENDPOINTS =====
@backend_app.post("/api/curation/entities/{journal_id}/{entity_id}/accept", response_model=SuccessResponse)
async def accept_entity_curation(
        journal_id: str,
        entity_id: str,
        curated_data: Dict[str, Any]
):
    return await CurationEndpoint.handle_entity_action(journal_id, entity_id, curated_data, "accept")


@backend_app.post("/api/curation/entities/{journal_id}/{entity_id}/reject", response_model=SuccessResponse)
async def reject_entity_curation(
        journal_id: str,
        entity_id: str
):
    return await CurationEndpoint.handle_entity_action(journal_id, entity_id, {}, "reject")


@backend_app.post("/api/curation/entities/{journal_id}/complete", response_model=SuccessResponse)
async def complete_entity_curation(journal_id: str):
    return await CurationEndpoint.complete_phase(journal_id, "entity")


# ===== RELATIONSHIP CURATION ENDPOINTS =====
@backend_app.post("/api/curation/relationships/{journal_id}/{relationship_id}/accept", response_model=SuccessResponse)
async def accept_relationship_curation(
        journal_id: str,
        relationship_id: str,
        curated_data: Dict[str, Any]
):
    return await CurationEndpoint.handle_relationship_action(journal_id, relationship_id, curated_data, "accept")


@backend_app.post("/api/curation/relationships/{journal_id}/{relationship_id}/reject", response_model=SuccessResponse)
async def reject_relationship_curation(
        journal_id: str,
        relationship_id: str
):
    return await CurationEndpoint.handle_relationship_action(journal_id, relationship_id, {}, "reject")


@backend_app.post("/api/curation/relationships/{journal_id}/complete", response_model=SuccessResponse)
async def complete_relationship_curation(journal_id: str):
    return await CurationEndpoint.complete_phase(journal_id, "relationship")


# ===== HEALTH CHECKS =====
@backend_app.get("/api/health")
@handle_errors(500)
@inject
async def health_check(
        db: Neo4jConnection = Depends(Provide[Container.db_connection]),
        curation_manager: CurationManager = Depends(Provide[Container.curation_manager])
):
    db_healthy = db.health_check()
    stats = await curation_manager.get_curation_stats()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "services": {
            "api": "running",
            "temporal": "connected",
            "curation_db": "accessible",
            "neo4j_db": "healthy" if db_healthy else "unhealthy",
        },
        "curation_stats": stats
    }


# ===== PROCESSING CONTROL ENDPOINTS =====
@backend_app.post("/api/processing/start", response_model=SuccessResponse)
async def start_processing():
    return await ProcessingEndpoint.control_processing("start")


@backend_app.post("/api/processing/pause", response_model=SuccessResponse)
async def pause_processing():
    return await ProcessingEndpoint.control_processing("pause")


@backend_app.get("/api/processing/windows", response_model=ProcessingWindowsResponse)
async def get_processing_windows():
    return ProcessingWindowsResponse(
        default_window={
            "start_time": "06:00",
            "end_time": "12:00",
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        },
        currently_active=False,
        next_window="tomorrow 06:00"
    )


# ===== OBSIDIAN INTEGRATION ENDPOINTS =====
@backend_app.post("/api/obsidian/process-note", response_model=SuccessResponse)
@handle_errors(500)
async def process_obsidian_note(note_path: str):
    return SuccessResponse(
        success=True,
        message=f"Note {note_path} queued for processing",
        workflow_id="placeholder"
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(backend_app, host="0.0.0.0", port=8000)
