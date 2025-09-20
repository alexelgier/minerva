"""Request and response models for the Minerva Backend API."""
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from minerva_backend.processing.models import JournalEntryCuration, CurationStats


# ===== REQUEST MODELS =====

class JournalSubmission(BaseModel):
    """Model for journal entry submission."""
    date: str = Field(..., description="Journal date in YYYY-MM-DD format", examples=["2025-09-19"])
    text: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="Journal entry text content"
    )

    @field_validator('date')
    def validate_date_format(cls, v):
        """Validate date is in correct format."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @field_validator('text')
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

    @field_validator('curated_data')
    def validate_curated_data_for_accept(cls, curated_data: Dict[str, Any], info: ValidationInfo):
        """Ensure curated_data is provided for accept actions."""
        if info.data.get('action') == 'accept' and not curated_data:
            raise ValueError('curated_data is required when action is "accept"')
        return curated_data


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


class CurationStatsResponse(BaseResponse):
    """Curation statistics response model."""
    stats: CurationStats = Field(..., description="Curation statistics")


class PendingCurationResponse(BaseResponse):
    """Response model for pending curation tasks."""
    journal_entry: List[JournalEntryCuration] = Field(default_factory=list,
                                                      description="List of pending journals with curation tasks")
    stats: CurationStats = Field(..., description="Curation statistics")


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
