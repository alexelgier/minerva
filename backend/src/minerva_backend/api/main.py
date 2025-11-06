"""
Minerva Backend API Application

This module contains the main FastAPI application for the Minerva Backend system.
It provides endpoints for journal processing, entity extraction, knowledge graph
management, and human curation workflows.

The application uses dependency injection for service management and includes
comprehensive error handling and CORS configuration for frontend integration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from minerva_backend.containers import Container, initialize_async_services
from minerva_backend.utils.logging import get_logger, setup_logging

from .exceptions import MinervaHTTPException, handle_errors, minerva_exception_handler
from .models import SuccessResponse
from .routers import curation, health, journal, pipeline, processing

# Initialize logging
setup_logging()
logger = get_logger("minerva_backend.api")


# --- FastAPI App Initialization ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    Initializes all required services and ensures proper cleanup.

    Startup:
    - Wires dependency injection modules
    - Initializes curation manager
    - Initializes temporal pipeline orchestrator

    Shutdown:
    - Closes database connections
    - Cleans up resources
    """
    logger.info("Starting Minerva Backend application", context={"stage": "startup"})

    try:
        container = Container()
        app.state.container = container
        logger.info("Wiring dependency injection modules", context={"stage": "startup"})
        container.wire(
            modules=[
                "minerva_backend.api.dependencies",
                "minerva_backend.processing.temporal_orchestrator",
            ]
        )

        # Initialize all async services
        logger.info("Initializing async services", context={"stage": "startup"})
        await initialize_async_services(container)

        logger.info(
            "Minerva Backend application started successfully",
            context={"stage": "startup"},
        )

        # Sync Zettels to database on startup
        logger.info("Syncing Zettels to database", context={"stage": "startup"})
        obsidian_service = container.obsidian_service()
        await obsidian_service.sync_zettels_to_db()

        yield

    except Exception as e:
        logger.error(
            "Failed to start Minerva Backend application",
            context={"stage": "startup", "error": str(e)},
        )
        raise
    finally:
        logger.info(
            "Shutting down Minerva Backend application", context={"stage": "shutdown"}
        )
        try:
            # Close database connections
            await container.db_connection().close_all()
            logger.info("Database connections closed", context={"stage": "shutdown"})
        except Exception as e:
            logger.error(
                "Error closing database connections",
                context={"stage": "shutdown", "error": str(e)},
            )


# Initialize FastAPI application
backend_app = FastAPI(
    title="Minerva Backend",
    version="0.1.0",
    description="Personal Knowledge Management System - Backend API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
backend_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom exception handler
backend_app.add_exception_handler(MinervaHTTPException, minerva_exception_handler)

# Include API routers
backend_app.include_router(journal.router)
backend_app.include_router(pipeline.router)
backend_app.include_router(curation.router)
backend_app.include_router(health.router)
backend_app.include_router(processing.router)


# ===== OBSIDIAN INTEGRATION ENDPOINTS =====
@backend_app.post(
    "/api/obsidian/process-note",
    response_model=SuccessResponse,
    summary="Process Obsidian Note",
    description="Queue an Obsidian note for processing through the Minerva pipeline",
    tags=["Obsidian Integration"],
)
@handle_errors(500)
async def process_obsidian_note(note_path: str):
    """
    Process an Obsidian note through the Minerva pipeline.

    This endpoint accepts a file path to an Obsidian note and queues it for
    processing through the complete Minerva pipeline, including entity extraction,
    human curation, and knowledge graph updates.

    Args:
        note_path (str): The file path to the Obsidian note to process

    Returns:
        SuccessResponse: Confirmation that the note has been queued for processing

    Raises:
        ValidationError: If the note path is invalid or empty
        ProcessingError: If the note cannot be queued for processing
        InternalError: If an unexpected error occurs

    Example:
        ```python
        response = await process_obsidian_note("/path/to/note.md")
        # Returns: {"success": true, "message": "Note /path/to/note.md queued for processing", "workflow_id": "placeholder"}
        ```
    """
    logger.info(
        "Processing Obsidian note",
        context={"note_path": note_path, "stage": "obsidian_processing"},
    )

    try:
        # TODO: Implement actual Obsidian note processing
        logger.info(
            "Obsidian note queued for processing",
            context={"note_path": note_path, "workflow_id": "placeholder"},
        )

        return SuccessResponse(
            success=True,
            message=f"Note {note_path} queued for processing",
            workflow_id="placeholder",
            journal_id=None,
            data=None,
        )

    except Exception as e:
        logger.error(
            "Failed to process Obsidian note",
            context={"note_path": note_path, "error": str(e)},
        )
        raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(backend_app, host="0.0.0.0", port=8000)
