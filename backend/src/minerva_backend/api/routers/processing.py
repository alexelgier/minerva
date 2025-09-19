"""Processing control and scheduling endpoints."""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends

from ..models import ProcessingControl, SuccessResponse, ProcessingWindowsResponse
from ..exceptions import handle_errors, ProcessingError
from ...config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/processing", tags=["processing"])


# This could be enhanced with a proper processing manager class
class ProcessingManager:
    """Simple processing state manager."""

    def __init__(self):
        self._is_active = False
        self._manual_control = False
        self._manual_end_time = None

    def is_currently_active(self) -> bool:
        """Check if processing is currently active."""
        if self._manual_control:
            if self._manual_end_time and datetime.now() > self._manual_end_time:
                self._manual_control = False
                self._manual_end_time = None
                return False
            return self._is_active

        # Check if we're in the default processing window
        now = datetime.now()
        start_time = datetime.strptime(settings.default_processing_start, "%H:%M").time()
        end_time = datetime.strptime(settings.default_processing_end, "%H:%M").time()
        current_time = now.time()

        return start_time <= current_time <= end_time

    def start_manual_processing(self, duration_hours: int = None):
        """Start manual processing session."""
        self._is_active = True
        self._manual_control = True
        if duration_hours:
            self._manual_end_time = datetime.now() + timedelta(hours=duration_hours)
        logger.info(f"Manual processing started for {duration_hours or 'indefinite'} hours")

    def pause_processing(self):
        """Pause all processing."""
        self._is_active = False
        self._manual_control = True
        logger.info("Processing paused manually")

    def resume_processing(self):
        """Resume processing."""
        self._is_active = True
        self._manual_control = True
        logger.info("Processing resumed manually")

    def get_next_window_description(self) -> str:
        """Get description of next processing window."""
        if self._manual_control and self._is_active:
            if self._manual_end_time:
                return f"Manual session until {self._manual_end_time.strftime('%H:%M')}"
            return "Manual session (indefinite)"

        now = datetime.now()
        tomorrow = now + timedelta(days=1)
        return f"Tomorrow {settings.default_processing_start}"


# Global processing manager instance
processing_manager = ProcessingManager()


@router.post("/control", response_model=SuccessResponse)
@handle_errors(400)
async def control_processing(control: ProcessingControl) -> SuccessResponse:
    """
    Control processing operations (start/pause/resume).

    Allows manual override of automatic processing windows
    for immediate processing needs or system maintenance.
    """
    try:
        if control.action == "start":
            processing_manager.start_manual_processing(control.duration_hours)
            message = f"Processing started manually"
            if control.duration_hours:
                message += f" for {control.duration_hours} hours"

        elif control.action == "pause":
            processing_manager.pause_processing()
            message = "Processing paused manually"

        elif control.action == "resume":
            processing_manager.resume_processing()
            message = "Processing resumed manually"

        else:
            raise ProcessingError(f"Unknown action: {control.action}")

        return SuccessResponse(
            message=message,
            data={
                "action": control.action,
                "duration_hours": control.duration_hours,
                "currently_active": processing_manager.is_currently_active()
            }
        )

    except Exception as e:
        logger.error(f"Processing control failed: {e}")
        raise ProcessingError(f"Failed to control processing: {str(e)}")


@router.get("/status")
@handle_errors(500)
async def get_processing_status() -> dict:
    """
    Get current processing status and activity information.

    Returns information about active processing sessions,
    queue lengths, and system resource usage.
    """
    try:
        currently_active = processing_manager.is_currently_active()

        return {
            "success": True,
            "currently_active": currently_active,
            "manual_control": processing_manager._manual_control,
            "next_window": processing_manager.get_next_window_description(),
            "default_window": {
                "start_time": settings.default_processing_start,
                "end_time": settings.default_processing_end
            },
            "queue_info": {
                "estimated_pending_time_minutes": 0,  # Would come from actual queue
                "active_workflows": 0  # Would come from Temporal
            }
        }

    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        raise


@router.get("/windows", response_model=ProcessingWindowsResponse)
@handle_errors(500)
async def get_processing_windows() -> ProcessingWindowsResponse:
    """
    Get processing window configuration and current status.

    Returns information about automated processing schedules
    and current processing state.
    """
    try:
        return ProcessingWindowsResponse(
            default_window={
                "start_time": settings.default_processing_start,
                "end_time": settings.default_processing_end,
                "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "timezone": "local"
            },
            currently_active=processing_manager.is_currently_active(),
            next_window=processing_manager.get_next_window_description(),
            manual_control=processing_manager._manual_control
        )

    except Exception as e:
        logger.error(f"Failed to get processing windows: {e}")
        raise


@router.post("/windows/configure")
@handle_errors(400)
async def configure_processing_window(
        start_time: str,
        end_time: str,
        days: list[str] = None
) -> SuccessResponse:
    """
    Configure the default processing window.

    This would typically update configuration that persists
    across application restarts.
    """
    try:
        # Validate time format
        datetime.strptime(start_time, "%H:%M")
        datetime.strptime(end_time, "%H:%M")

        # In a real implementation, this would update persistent configuration
        logger.info(f"Processing window configured: {start_time} - {end_time}")

        return SuccessResponse(
            message="Processing window configured successfully",
            data={
                "start_time": start_time,
                "end_time": end_time,
                "days": days or ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            }
        )

    except ValueError as e:
        raise ProcessingError("Invalid time format. Use HH:MM format.")
    except Exception as e:
        logger.error(f"Failed to configure processing window: {e}")
        raise ProcessingError(f"Failed to configure processing window: {str(e)}")


@router.get("/queue/stats")
@handle_errors(500)
async def get_queue_statistics() -> dict:
    """
    Get detailed processing queue statistics.

    Returns information about pending workflows, processing times,
    and system resource utilization.
    """
    try:
        # In a real implementation, this would query actual queue data
        return {
            "success": True,
            "queue_stats": {
                "total_pending_journals": 0,
                "pending_entity_extraction": 0,
                "pending_relationship_extraction": 0,
                "pending_curation_reviews": 0,
                "average_processing_time_minutes": 0,
                "estimated_completion_time": "No pending work"
            },
            "system_stats": {
                "cpu_usage_percent": 0,  # Would come from system monitoring
                "memory_usage_percent": 0,
                "ollama_model_loaded": False
            }
        }

    except Exception as e:
        logger.error(f"Failed to get queue statistics: {e}")
        raise
