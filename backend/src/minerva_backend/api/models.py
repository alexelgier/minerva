"""Request and response models for the Minerva Backend API."""
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, validator
import re


# ===== REQUEST MODELS =====

class JournalSubmission(BaseModel):
    """Model for journal entry submission."""

    date: str = Field(
        ...,
        description="Journal date in YYYY-MM-DD format",
        example="2025-09-19"
    )
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Journal entry text content"
    )

    @validator('date')
    def validate_date_format(cls, v):
        """Validate date is in correct format."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @validator('text')
    def validate_text_content(cls, v):
        """Validate text content is not empty."""
        if not v.strip():
            raise ValueError('Journal text cannot be empty')
        return v.strip()


class CurationAction(BaseModel):
    """Model for curation actions (accept/reject)."""

    action: Literal["accept", "reject"] = Field(
        ...,
        description="Action to take on the curation item"
    )
    curated_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Curated data (required for accept action)"
    )

    @validator('curated_data')
    def validate_curated_data_for_accept(cls, v, values):
        """Ensure curated_data is provided for accept actions."""
        if values.get('action') == 'accept' and not v:
            raise ValueError('curated_data is required when action is "accept"')
        return v


class ProcessingControl(BaseModel):
    """Model for processing control actions."""

    action: Literal["start", "pause", "resume"] = Field(
        ...,
        description="Processing control action"
    )
    duration_hours: Optional[int] = Field(
        None,
        ge=1,
        le=24,
        description="Duration in hours (for manual processing sessions)"
    )


# ===== RESPONSE MODELS =====

class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(default=True, description="Whether the operation was successful")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class SuccessResponse(BaseResponse):
    """Standard success response model."""

    message: str = Field(..., description="Success message")
    workflow_id: Optional[str] = Field(None, description="Associated workflow ID")
    journal_id: Optional[str] = Field(None, description="Associated journal ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class ErrorResponse(BaseResponse):
    """Error response model."""

    success: bool = Field(default=False)
    error: Dict[str, Any] = Field(..., description="Error details")


class PipelineStatusResponse(BaseResponse):
    """Pipeline status response model."""

    workflow_id: str = Field(..., description="Workflow identifier")
    status: Dict[str, Any] = Field(..., description="Detailed status information")


class PendingPipelinesResponse(BaseResponse):
    """Response model for pending pipelines list."""

    pending_pipelines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of pending pipeline workflows"
    )
    total_count: int = Field(default=0, description="Total number of pending pipelines")


class CurationTask(BaseModel):
    """Model for individual curation tasks."""

    id: str = Field(..., description="Task identifier")
    journal_id: str = Field(..., description="Associated journal entry ID")
    type: Literal["entity", "relationship"] = Field(..., description="Type of curation task")
    status: Literal["pending", "in_progress", "completed"] = Field(..., description="Task status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    data: Dict[str, Any] = Field(..., description="Task data to be curated")


class CurationStatsResponse(BaseResponse):
    """Curation statistics response model."""

    total_pending: int = Field(default=0, description="Total pending curation tasks")
    entities_pending: int = Field(default=0, description="Pending entity curation tasks")
    relationships_pending: int = Field(default=0, description="Pending relationship curation tasks")
    avg_processing_time_minutes: float = Field(default=0.0, description="Average processing time in minutes")
    oldest_pending_age_hours: float = Field(default=0.0, description="Age of oldest pending task in hours")
    completed_today: int = Field(default=0, description="Tasks completed today")


class PendingCurationResponse(BaseResponse):
    """Response model for pending curation tasks."""

    tasks: List[CurationTask] = Field(default_factory=list, description="List of pending curation tasks")
    stats: CurationStatsResponse = Field(..., description="Curation statistics")


class ProcessingWindowsResponse(BaseResponse):
    """Processing windows configuration response."""

    default_window: Dict[str, Any] = Field(..., description="Default processing window configuration")
    currently_active: bool = Field(..., description="Whether processing is currently active")
    next_window: str = Field(..., description="Description of next processing window")
    manual_control: bool = Field(default=False, description="Whether manual control is active")


class HealthCheckResponse(BaseResponse):
    """Health check response model."""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall system health")
    services: Dict[str, str] = Field(..., description="Individual service statuses")
    curation_stats: CurationStatsResponse = Field(..., description="Current curation statistics")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    version: str = Field(..., description="API version")


# ===== UTILITY MODELS =====

class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Any = Field(..., description="Invalid value that was provided")
