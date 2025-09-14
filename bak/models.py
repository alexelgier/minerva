"""
Graphiti Entity and Relation Types for Personal Diary System
Designed for Obsidian-based diary entries with rich interconnections
"""

from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional

from pydantic import Field, BaseModel


# ============================================================================
# ENUMS FOR STANDARDIZED VALUES
# ============================================================================
class ProjectStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResourceType(str, Enum):
    BOOK = "BOOK"
    ARTICLE = "ARTICLE"
    YOUTUBE = "YOUTUBE"
    MOVIE = "MOVIE"
    MISC = "MISC"


class ResourceStatus(str, Enum):
    WANT_TO_CONSUME = "WANT_TO_CONSUME"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    REFERENCE = "REFERENCE"
    ABANDONED = "ABANDONED"


# ============================================================================
# ENTITY DEFINITIONS
# ============================================================================

class Person(BaseModel):
    """Represents an individual person."""
    full_name: str = Field(..., description="Full name of the person")
    occupation: Optional[str] = Field(None, description="Current job title or profession")
    birth_date: Optional[date] = Field(None, description="Date of birth (YYYY-MM-DD)")


class Emotion(BaseModel):
    """Represents a distinct type of emotion that can be felt (e.g., happiness, anxiety, frustration, grief)"""


class Feeling(BaseModel):
    """Reified relationship: Person experiences Emotion or Thought about something"""
    intensity: int = Field(..., description="Intensity level (1-10)")
    timestamp: datetime = Field(..., description="When this feeling occurred")
    duration: Optional[timedelta] = Field(None, description="How long the feeling lasted")


class Event(BaseModel):
    """Represents a notable occurrence or activity that happened at a specific time."""
    type: str = Field(..., description="Category of event (e.g., practice, study, meeting, exercise)")
    date: datetime = Field(..., description="Date and time when the event occurred")
    duration: Optional[timedelta] = Field(None, description="Duration of the event (e.g., 2 hours, 30 minutes)")
    location: Optional[str] = Field(None, description="Where the event took place")


class Project(BaseModel):
    """Represents an ongoing initiative, goal, or multistep endeavor with trackable progress."""
    project_name: str = Field(..., description="Name or title of the project")
    status: Optional[ProjectStatus] = Field(None, description="Current status of the project")
    start_date: Optional[datetime] = Field(None, description="Date when the project was started")
    target_completion: Optional[datetime] = Field(None, description="Target or expected completion date")
    progress: Optional[float] = Field(None, description="Completion percentage (0.0 to 100.0)")


class Concept(BaseModel):
    """Represents an atomic idea or concept in your zettelkasten knowledge system."""
    title: str = Field(..., description="Concise title of the concept or idea")
    analysis: str = Field(..., description="Your personal analysis, insights, and understanding of the concept")


class Resource(BaseModel):
    """Represents external content (books, articles, videos) that serve as a source of information or entertainment."""
    title: str = Field(..., description="Title or name of the resource")
    type: ResourceType = Field(..., description="Category of resource")
    url: Optional[str] = Field(None, description="Web URL or location where the resource can be accessed")
    quotes: Optional[list[str]] = Field(None, description="Notable quotes or excerpts from the resource")
    status: Optional[ResourceStatus] = Field(None, description="Current consumption status")
    author: Optional[str] = Field(None, description="Creator or author of the resource")


# ============================================================================
# RELATION DEFINITIONS
# ============================================================================

entity_types = {
    "Person": Person,
    "Emotion": Emotion,
    "Feeling": Feeling,
    "Event": Event,
    "Project": Project,
    "Concept": Concept,
    "Resource": Resource
}

edge_types = None

edge_type_map = None
