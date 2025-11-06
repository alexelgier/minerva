"""Health check and system monitoring endpoints."""

import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.processing.temporal_orchestrator import PipelineOrchestrator
from minerva_backend.utils.logging import get_logger

from ...config import settings
from ..dependencies import (
    get_curation_manager,
    get_db_connection,
    get_llm_service,
    get_pipeline_orchestrator,
)
from ..exceptions import handle_errors

logger = get_logger("minerva_backend.api.health")
router = APIRouter(prefix="/api/health", tags=["health"])

# Track application start time for uptime calculation
_app_start_time = time.time()


@router.get("/")
@handle_errors(500)
async def health_check(
    curation_manager: CurationManager = Depends(get_curation_manager),
    db_connection: Neo4jConnection = Depends(get_db_connection),
    llm_service: LLMService = Depends(get_llm_service),
    pipeline_orchestrator: PipelineOrchestrator = Depends(get_pipeline_orchestrator),
) -> JSONResponse:
    """
    Frontend-focused health check for dashboard.

    Returns comprehensive status information for all services
    with rich data for frontend decision-making.
    """
    try:
        # Check all services
        services = await _check_all_services(
            curation_manager, db_connection, llm_service, pipeline_orchestrator
        )

        # Determine overall status
        overall_status = _determine_overall_status(services)

        # Calculate uptime
        uptime_seconds = time.time() - _app_start_time

        # Prepare dashboard info
        dashboard_info = _build_dashboard_info(services, overall_status)

        logger.debug(f"Health check completed: {overall_status}")

        return JSONResponse(
            content={
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": uptime_seconds,
                "version": settings.api_version,
                "services": services,
                "dashboard_info": dashboard_info,
            }
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return _build_error_response()


async def _check_all_services(
    curation_manager: CurationManager,
    db_connection: Neo4jConnection,
    llm_service: LLMService,
    pipeline_orchestrator: PipelineOrchestrator,
) -> Dict[str, Dict[str, Any]]:
    """Check all services and return their status."""
    services = {}

    # Check each service
    services["database"] = await _check_database_health(db_connection)
    services["curation"] = await _check_curation_health(curation_manager)
    services["ollama"] = await _check_ollama_health(llm_service)
    services["temporal"] = await _check_temporal_health_status(pipeline_orchestrator)

    return services


async def _check_database_health(db_connection: Neo4jConnection) -> Dict[str, Any]:
    """Check database health status."""
    try:
        # Use async health check
        db_healthy = await db_connection.health_check()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": ("Connected to Neo4j" if db_healthy else "Database unavailable"),
            "response_time_ms": 0,  # Could add timing if needed
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
            "response_time_ms": None,
        }


async def _check_curation_health(curation_manager: CurationManager) -> Dict[str, Any]:
    """Check curation system health status."""
    try:
        stats = await curation_manager.get_curation_stats()
        return {
            "status": "healthy",
            "message": "Curation system available",
            "pending_entities": stats.pending_entities,
            "pending_relationships": stats.pending_relationships,
            "completed_today": stats.completed,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Curation error: {str(e)}",
            "pending_entities": 0,
            "pending_relationships": 0,
            "completed_today": 0,
        }


async def _check_ollama_health(llm_service: LLMService) -> Dict[str, Any]:
    """Check Ollama/LLM service health status."""
    try:
        health_checker = HealthChecker(llm_service)
        ollama_healthy = await health_checker.check_ollama_health()
        return {
            "status": "healthy" if ollama_healthy else "unhealthy",
            "message": (
                "LLM service available" if ollama_healthy else "Ollama unavailable"
            ),
            "response_time_ms": 0,  # Could add timing if needed
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Ollama error: {str(e)}",
            "response_time_ms": None,
        }


async def _check_temporal_health_status(
    pipeline_orchestrator: PipelineOrchestrator,
) -> Dict[str, Any]:
    """Check Temporal workflow engine health status."""
    try:
        temporal_healthy = await _check_temporal_health(pipeline_orchestrator)
        return {
            "status": "healthy" if temporal_healthy else "unhealthy",
            "message": (
                "Workflow engine available"
                if temporal_healthy
                else "Temporal unavailable"
            ),
            "response_time_ms": 0,  # Could add timing if needed
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Temporal error: {str(e)}",
            "response_time_ms": None,
        }


def _determine_overall_status(services: Dict[str, Dict[str, Any]]) -> str:
    """Determine overall system status based on individual service statuses."""
    unhealthy_services = [k for k, v in services.items() if v["status"] == "unhealthy"]
    return "unhealthy" if unhealthy_services else "healthy"


def _build_dashboard_info(
    services: Dict[str, Dict[str, Any]], overall_status: str
) -> Dict[str, Any]:
    """Build dashboard information for frontend."""
    curation_service = services.get("curation", {})
    return {
        "curation_backlog": curation_service.get("pending_entities", 0)
        + curation_service.get("pending_relationships", 0),
        "recent_activity": f"{curation_service.get('completed_today', 0)} journals processed today",
        "system_load": "normal" if overall_status == "healthy" else "high",
    }


def _build_error_response() -> JSONResponse:
    """Build error response when health check itself fails."""
    return JSONResponse(
        content={
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - _app_start_time,
            "version": settings.api_version,
            "services": {
                "database": {"status": "unknown", "message": "Health check failed"},
                "curation": {"status": "unknown", "message": "Health check failed"},
                "ollama": {"status": "unknown", "message": "Health check failed"},
                "temporal": {"status": "unknown", "message": "Health check failed"},
            },
            "dashboard_info": {
                "curation_backlog": 0,
                "recent_activity": "System unavailable",
                "system_load": "unknown",
            },
        }
    )


@router.get("/curation")
@handle_errors(500)
async def curation_health(
    curation_manager: CurationManager = Depends(get_curation_manager),
) -> JSONResponse:
    """
    Curation-specific health check with detailed statistics.

    Returns comprehensive curation system information
    for frontend dashboard widgets.
    """
    try:
        start_time = time.time()

        # Get comprehensive curation statistics
        stats = await curation_manager.get_curation_stats()

        query_time = time.time() - start_time

        # Calculate totals
        total_pending = stats.pending_entities + stats.pending_relationships
        total_completed = stats.completed

        # Determine health status (no degraded logic for backlog)
        health_status = "healthy"  # Always healthy if we can get stats

        # Prepare recommendations
        recommendations = []
        if total_pending > 50:
            recommendations.append(
                "Consider dedicating time to curation to reduce backlog"
            )
        # Note: oldest_pending_age_hours and avg_processing_time_minutes are not available in CurationStats
        # These recommendations are disabled until those fields are added to the model

        if not recommendations:
            recommendations.append("Curation system is operating optimally")

        return JSONResponse(
            content={
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "query_time_seconds": round(query_time, 3),
                "statistics": {
                    "pending_entities": stats.pending_entities,
                    "pending_relationships": stats.pending_relationships,
                    "total_pending": total_pending,
                    "completed_today": total_completed,
                    "oldest_pending_age_hours": 0,  # Not available in current model
                    "avg_processing_time_minutes": 0,  # Not available in current model
                },
                "recommendations": recommendations,
            }
        )

    except Exception as e:
        logger.error(f"Curation health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "statistics": {
                    "pending_entities": 0,
                    "pending_relationships": 0,
                    "total_pending": 0,
                    "completed_today": 0,
                    "oldest_pending_age_hours": 0,
                    "avg_processing_time_minutes": 0,
                },
                "recommendations": ["Curation system unavailable"],
            }
        )


class HealthChecker:
    """Helper class for health checks with proper dependency injection."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def check_ollama_health(self) -> bool:
        """Quick Ollama health check without running inference."""
        try:
            # Simple connectivity test - just check if service is initialized
            # and can make a basic request (not inference)
            if hasattr(self.llm_service, "is_available"):
                return await self.llm_service.is_available()
            else:
                # Fallback: just check if service exists and is callable
                return self.llm_service is not None
        except Exception:
            return False


async def _check_temporal_health(temporal_orchestrator: PipelineOrchestrator) -> bool:
    """Quick Temporal health check."""
    try:
        # Simple connectivity test - just check if service is initialized
        if hasattr(temporal_orchestrator, "is_available"):
            return await temporal_orchestrator.is_available()
        else:
            # Fallback: just check if service exists and is callable
            return temporal_orchestrator is not None
    except Exception:
        return False
