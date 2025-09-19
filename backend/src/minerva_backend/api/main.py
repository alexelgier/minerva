# api/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from minerva_backend.containers import Container
from .exceptions import (
    handle_errors, minerva_exception_handler, MinervaHTTPException
)
from .models import SuccessResponse
from .routers import journal, pipeline, curation, health, processing


# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    container: Container = app.state.container
    container.wire(modules=["minerva_backend.api.dependencies"])
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

backend_app.add_exception_handler(MinervaHTTPException, minerva_exception_handler)
backend_app.add_exception_handler(MinervaHTTPException, minerva_exception_handler)

backend_app.include_router(journal.router)
backend_app.include_router(pipeline.router)
backend_app.include_router(curation.router)
backend_app.include_router(health.router)
backend_app.include_router(processing.router)


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
