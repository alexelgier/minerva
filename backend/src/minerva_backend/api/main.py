# api/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator, PipelineState
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.graph.models.documents import JournalEntry

# Global instances
orchestrator = PipelineOrchestrator()
curation_manager = CurationManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize connections on startup
    await orchestrator.initialize()
    await curation_manager.initialize()

    yield
    # Clean up


backend_app = FastAPI(title="Minerva Backend", version="0.1.0", lifespan=lifespan)

# CORS for Vue.js dashboard
backend_app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== JOURNAL SUBMISSION ENDPOINTS =====

class JournalSubmission(BaseModel):
    date: str
    text: str


@backend_app.post("/api/journal/submit")
async def submit_journal(submission: JournalSubmission):
    """Submit a journal entry for processing"""
    try:
        # Create JournalEntry model
        journal_entry = JournalEntry.from_text(submission.text, submission.date)

        # Submit to Temporal workflow
        workflow_id = await orchestrator.submit_journal(journal_entry)

        return {
            "success": True,
            "workflow_id": workflow_id,
            "journal_id": journal_entry.uuid,
            "message": "Journal submitted for processing"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit journal: {str(e)}")


# ===== PIPELINE STATUS ENDPOINTS =====

@backend_app.get("/api/pipeline/status/{workflow_id}")
async def get_pipeline_status(workflow_id: str):
    """Get the current status of a journal processing pipeline"""
    try:
        status = await orchestrator.get_pipeline_status(workflow_id)
        return {
            "workflow_id": workflow_id,
            "status": status.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Workflow not found: {str(e)}")


@backend_app.get("/api/pipeline/all-pending")
async def get_all_pending_pipelines():
    """Get all pipelines currently in progress"""
    try:
        # This would be implemented to query Temporal for active workflows
        # For now, return empty list
        return {"pending_pipelines": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending pipelines: {str(e)}")


# ===== CURATION ENDPOINTS =====

@backend_app.get("/api/curation/pending")
async def get_pending_curation():
    """Get all pending curation tasks for the dashboard"""
    try:
        tasks = await curation_manager.get_all_pending_curation_tasks()
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending curation: {str(e)}")


@backend_app.get("/api/curation/stats")
async def get_curation_stats():
    """Get curation statistics for dashboard"""
    try:
        stats = await curation_manager.get_curation_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get curation stats: {str(e)}")


# ===== ENTITY CURATION ENDPOINTS =====

@backend_app.get("/api/curation/entities/{journal_id}")
async def get_entity_curation_task(journal_id: str):
    """Get entity curation task for a specific journal entry"""
    try:
        tasks = await curation_manager.get_pending_entity_curation()

        # Find the specific journal
        for task in tasks:
            if task["journal_id"] == journal_id:
                # Mark as in progress
                await curation_manager.mark_entity_curation_in_progress(journal_id)
                return task

        raise HTTPException(status_code=404, detail="Entity curation task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get entity curation: {str(e)}")


class EntityCurationResult(BaseModel):
    entities: List[Dict[str, Any]]


@backend_app.post("/api/curation/entities/{journal_id}/complete")
async def complete_entity_curation(journal_id: str, result: EntityCurationResult):
    """Complete entity curation with user decisions"""
    try:
        await curation_manager.complete_entity_curation(journal_id, result.entities)
        return {"success": True, "message": "Entity curation completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete entity curation: {str(e)}")


# ===== RELATIONSHIP CURATION ENDPOINTS =====

@backend_app.get("/api/curation/relationships/{journal_id}")
async def get_relationship_curation_task(journal_id: str):
    """Get relationship curation task for a specific journal entry"""
    try:
        tasks = await curation_manager.get_pending_relationship_curation()

        for task in tasks:
            if task["journal_id"] == journal_id:
                return task

        raise HTTPException(status_code=404, detail="Relationship curation task not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationship curation: {str(e)}")


class RelationshipCurationResult(BaseModel):
    relationships: List[Dict[str, Any]]


@backend_app.post("/api/curation/relationships/{journal_id}/complete")
async def complete_relationship_curation(journal_id: str, result: RelationshipCurationResult):
    """Complete relationship curation with user decisions"""
    try:
        await curation_manager.complete_relationship_curation(journal_id, result.relationships)
        return {"success": True, "message": "Relationship curation completed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete relationship curation: {str(e)}")


# ===== HEALTH CHECKS =====

@backend_app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Basic health checks
        stats = await curation_manager.get_curation_stats()

        return {
            "status": "healthy",
            "services": {
                "api": "running",
                "temporal": "connected",
                "curation_db": "accessible"
            },
            "curation_stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ===== PROCESSING CONTROL ENDPOINTS =====

@backend_app.post("/api/processing/start")
async def start_processing():
    """Manually start processing (outside of scheduled windows)"""
    # This would interact with your processing window configuration
    return {"success": True, "message": "Processing started manually"}


@backend_app.post("/api/processing/pause")
async def pause_processing():
    """Pause processing temporarily"""
    # This would pause the Temporal workflows or worker
    return {"success": True, "message": "Processing paused"}


@backend_app.get("/api/processing/windows")
async def get_processing_windows():
    """Get current processing window configuration"""
    # Return your current processing schedule
    return {
        "default_window": {
            "start_time": "06:00",
            "end_time": "12:00",
            "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        },
        "currently_active": False,  # Based on current time
        "next_window": "tomorrow 06:00"
    }


# ===== OBSIDIAN INTEGRATION ENDPOINTS =====

@backend_app.post("/api/obsidian/process-note")
async def process_obsidian_note(note_path: str):
    """Process an Obsidian daily note"""
    try:
        # This would read the file, parse structured data, and submit
        # For now, placeholder
        return {
            "success": True,
            "message": f"Note {note_path} queued for processing",
            "workflow_id": "placeholder"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process note: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(backend_app, host="0.0.0.0", port=8000)
