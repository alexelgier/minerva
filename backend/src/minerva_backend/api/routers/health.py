"""Health check and system monitoring endpoints."""
import logging
import time
from datetime import datetime
from fastapi import APIRouter, Depends

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.processing.curation_manager import CurationManager
from ..models import HealthCheckResponse, CurationStatsResponse
from ..dependencies import get_db_connection, get_curation_manager
from ..exceptions import handle_errors
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])

# Track application start time for uptime calculation
_app_start_time = time.time()


@router.get("/", response_model=HealthCheckResponse)
@handle_errors(500)
async def health_check(
        db: Neo4jConnection = Depends(get_db_connection),
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> HealthCheckResponse:
    """
    Comprehensive health check for all system components.

    Returns detailed status information for each service and
    overall system health assessment.
    """
    try:
        # Test database connectivity
        db_healthy = db.health_check()

        # Get curation system status
        curation_stats_dict = await curation_manager.get_curation_stats()
        curation_stats = CurationStatsResponse(**curation_stats_dict)

        # Test individual services
        service_statuses = {
            "api": "healthy",
            "neo4j_db": "healthy" if db_healthy else "unhealthy",
            "curation_db": "healthy",  # Assume healthy if we got stats
            "temporal": "unknown",  # Would need actual connectivity test
            "ollama": "unknown"  # Would need actual connectivity test
        }

        # Determine overall health
        unhealthy_services = [k for k, v in service_statuses.items() if v == "unhealthy"]
        degraded_services = [k for k, v in service_statuses.items() if v == "unknown"]

        if unhealthy_services:
            overall_status = "unhealthy"
        elif degraded_services:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        uptime_seconds = time.time() - _app_start_time

        logger.debug(f"Health check completed: {overall_status}")

        return HealthCheckResponse(
            status=overall_status,
            services=service_statuses,
            curation_stats=curation_stats,
            uptime_seconds=uptime_seconds,
            version=settings.api_version
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")

        # Return unhealthy status if health check itself fails
        return HealthCheckResponse(
            status="unhealthy",
            services={
                "api": "unhealthy",
                "neo4j_db": "unknown",
                "curation_db": "unknown",
                "temporal": "unknown",
                "ollama": "unknown"
            },
            curation_stats=CurationStatsResponse(),  # Empty stats
            uptime_seconds=time.time() - _app_start_time,
            version=settings.api_version
        )


@router.get("/db")
@handle_errors(500)
async def database_health(
        db: Neo4jConnection = Depends(get_db_connection)
) -> dict:
    """
    Detailed database health check.

    Returns specific information about Neo4j connectivity,
    query performance, and data integrity.
    """
    try:
        start_time = time.time()

        # Basic connectivity test
        is_connected = db.health_check()

        connection_time = time.time() - start_time

        # Additional database metrics could be added here
        # - Query a few basic nodes to test read performance
        # - Check database version
        # - Verify essential indexes exist

        return {
            "success": True,
            "database_healthy": is_connected,
            "connection_time_seconds": round(connection_time, 3),
            "database_type": "neo4j",
            "additional_checks": {
                "basic_connectivity": is_connected,
                "query_performance": "not_tested",  # Could add actual query timing
                "index_integrity": "not_tested"  # Could verify indexes
            }
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "success": False,
            "database_healthy": False,
            "error": str(e),
            "database_type": "neo4j"
        }


@router.get("/curation")
@handle_errors(500)
async def curation_health(
        curation_manager: CurationManager = Depends(get_curation_manager)
) -> dict:
    """
    Detailed curation system health check.

    Returns information about curation database connectivity,
    queue health, and processing backlog status.
    """
    try:
        start_time = time.time()

        # Get comprehensive curation statistics
        stats = await curation_manager.get_curation_stats()

        query_time = time.time() - start_time

        # Assess curation system health based on statistics
        backlog_concerning = stats.get('total_pending', 0) > 100
        old_tasks_concerning = stats.get('oldest_pending_age_hours', 0) > 48

        health_status = "healthy"
        if backlog_concerning or old_tasks_concerning:
            health_status = "degraded"

        health_issues = []
        if backlog_concerning:
            health_issues.append("Large backlog detected")
        if old_tasks_concerning:
            health_issues.append("Old pending tasks detected")

        return {
            "success": True,
            "curation_healthy": health_status == "healthy",
            "health_status": health_status,
            "query_time_seconds": round(query_time, 3),
            "statistics": stats,
            "health_issues": health_issues,
            "recommendations": _get_curation_recommendations(stats)
        }

    except Exception as e:
        logger.error(f"Curation health check failed: {e}")
        return {
            "success": False,
            "curation_healthy": False,
            "error": str(e),
            "health_status": "unhealthy"
        }


@router.get("/system")
@handle_errors(500)
async def system_health() -> dict:
    """
    System-level health check including resource utilization.

    Returns information about CPU, memory, disk usage, and
    other system-level metrics relevant to Minerva operation.
    """
    try:
        import psutil

        # System resource information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Application-specific metrics
        uptime_seconds = time.time() - _app_start_time

        return {
            "success": True,
            "system_resources": {
                "cpu_usage_percent": cpu_percent,
                "memory_usage_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024 ** 3), 2),
                "disk_usage_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024 ** 3), 2)
            },
            "application_metrics": {
                "uptime_seconds": uptime_seconds,
                "uptime_hours": round(uptime_seconds / 3600, 2),
                "api_version": settings.api_version,
                "debug_mode": settings.debug
            },
            "resource_warnings": _get_resource_warnings(cpu_percent, memory.percent, disk.percent)
        }

    except ImportError:
        # psutil not available
        return {
            "success": False,
            "error": "System monitoring unavailable (psutil not installed)",
            "application_metrics": {
                "uptime_seconds": time.time() - _app_start_time,
                "api_version": settings.api_version,
                "debug_mode": settings.debug
            }
        }
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _get_curation_recommendations(stats: dict) -> list[str]:
    """Generate recommendations based on curation statistics."""
    recommendations = []

    total_pending = stats.get('total_pending', 0)
    oldest_age = stats.get('oldest_pending_age_hours', 0)

    if total_pending > 50:
        recommendations.append("Consider dedicating time to curation to reduce backlog")

    if oldest_age > 24:
        recommendations.append("Review oldest pending tasks to maintain workflow momentum")

    if stats.get('avg_processing_time_minutes', 0) > 10:
        recommendations.append("Processing times are high - consider system optimization")

    if not recommendations:
        recommendations.append("Curation system is operating optimally")

    return recommendations


def _get_resource_warnings(cpu_percent: float, memory_percent: float, disk_percent: float) -> list[str]:
    """Generate warnings based on system resource usage."""
    warnings = []

    if cpu_percent > 80:
        warnings.append("High CPU usage detected")

    if memory_percent > 80:
        warnings.append("High memory usage detected")

    if disk_percent > 85:
        warnings.append("Low disk space available")

    return warnings