from __future__ import annotations

from abc import ABC
from datetime import date, datetime, timedelta
from enum import Enum
from typing import List, Literal

from pydantic import Field, field_serializer, field_validator

from .utils import duration_validator
from .base import Node, PartitionType

# ----------------------------
# Enums
# ----------------------------


class EntityType(str, Enum):
    PERSON = "Person"
    FEELING_EMOTION = "FeelingEmotion"
    FEELING_CONCEPT = "FeelingConcept"
    EMOTION = "Emotion"
    EVENT = "Event"
    PROJECT = "Project"
    CONCEPT = "Concept"
    CONTENT = "Content"
    CONSUMABLE = "Consumable"
    PLACE = "Place"


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


class EmotionType(str, Enum):
    ANGER = "anger"
    ANNOYANCE = "annoyance"
    CONTEMPT = "contempt"
    DISGUST = "disgust"
    IRRITATION = "irritation"
    ANXIETY = "anxiety"
    EMBARRASSMENT = "embarrassment"
    FEAR = "fear"
    HELPLESSNESS = "helplessness"
    POWERLESSNESS = "powerlessness"
    WORRY = "worry"
    DOUBT = "doubt"
    ENVY = "envy"
    FRUSTRATION = "frustration"
    GUILT = "guilt"
    SHAME = "shame"
    CONFUSION = "confusion"
    BOREDOM = "boredom"
    DESPAIR = "despair"
    DISAPPOINTMENT = "disappointment"
    HURT = "hurt"
    SADNESS = "sadness"
    LONELINESS = "loneliness"
    STRESS = "stress"
    TENSION = "tension"
    AMUSEMENT = "amusement"
    DELIGHT = "delight"
    ELATION = "elation"
    EXCITEMENT = "excitement"
    HAPPINESS = "happiness"
    JOY = "joy"
    PLEASURE = "pleasure"
    SATISFACTION = "satisfaction"
    AFFECTION = "affection"
    EMPATHY = "empathy"
    LOVE = "love"
    PRIDE = "pride"
    GRATITUDE = "gratitude"
    HOPE = "hope"
    TRUST = "trust"
    ANTICIPATION = "anticipation"
    CALMNESS = "calmness"
    CONTENTMENT = "contentment"
    RELAXATION = "relaxation"
    RELIEF = "relief"
    SERENITY = "serenity"
    AWE = "awe"
    NOSTALGIA = "nostalgia"
    INTEREST = "interest"
    SURPRISE = "surprise"


class Entity(Node, ABC):
    name: str = Field(..., description="nombre de la entidad")
    type: EntityType = Field(..., description="Tipo de entidad (Persona, Evento, etc)")
    summary_short: str = Field(
        ..., description="Resumen de la entidad. Máximo 30 palabras"
    )
    summary: str = Field(..., description="Resumen de la entidad. Máximo 100 palabras")
    partition: Literal[PartitionType.DOMAIN] = PartitionType.DOMAIN
    embedding: list[float] | None = Field(
        default=None, description="Embedding of the summary field"
    )


# ----------------------------
# Specific entities (all extend Entity)
# ----------------------------


class Person(Entity):
    """Representa a una persona individual."""

    type: Literal[EntityType.PERSON] = EntityType.PERSON
    occupation: str | None = Field(default=None, description="Cargo o profesión")
    birth_date: date | None = Field(default=None, description="Fecha de nacimiento")


class Emotion(Entity):
    """Representa un tipo distinto de emoción que se puede sentir"""

    type: Literal[EntityType.EMOTION] = EntityType.EMOTION


class FeelingEmotion(Entity):
    """Relación reificada: Una persona experimenta una emoción"""

    timestamp: datetime = Field(..., description="Cuándo ocurrió este sentimiento")
    type: Literal[EntityType.FEELING_EMOTION] = EntityType.FEELING_EMOTION
    intensity: int | None = Field(
        default=None, description="Nivel de intensidad (1-10)", ge=1, le=10
    )
    duration: timedelta | None = Field(
        default=None, description="Cuánto duró el sentimiento"
    )
    emotion: EmotionType | None = Field(default=None, exclude=True)
    emotion_uuid: EmotionType | None = Field(default=None, exclude=True)
    person_uuid: str | None = Field(default=None, exclude=True)

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v):
        """Parsea duración en formato string a timedelta."""
        return duration_validator(v)

    @field_serializer("duration")
    def serialize_duration(self, value: timedelta | None) -> str | None:
        """Serialize duration field to ISO format string."""
        if value is None:
            return None
        return str(value)


class FeelingConcept(Entity):
    """Relación reificada: Una persona experimenta un sentimiento sobre un concepto"""

    timestamp: datetime = Field(..., description="Cuándo ocurrió este sentimiento")
    type: Literal[EntityType.FEELING_CONCEPT] = EntityType.FEELING_CONCEPT
    intensity: int | None = Field(
        default=None, description="Nivel de intensidad (1-10)", ge=1, le=10
    )
    duration: timedelta | None = Field(
        default=None, description="Cuánto duró el sentimiento"
    )
    person_uuid: str | None = Field(default=None, exclude=True)
    concept_uuid: str | None = Field(default=None, exclude=True)

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v):
        """Parsea duración en formato string a timedelta."""
        return duration_validator(v)

    @field_serializer("duration")
    def serialize_duration(self, value: timedelta | None) -> str | None:
        """Serialize duration field to ISO format string."""
        if value is None:
            return None
        return str(value)


class Event(Entity):
    """Representa un suceso o actividad notable que ocurrió en un momento específico."""

    category: str = Field(
        ..., description="Categoría del evento (reunión, entrenamiento, etc)"
    )
    date: datetime = Field(..., description="Cuándo ocurrió el evento")
    type: Literal[EntityType.EVENT] = EntityType.EVENT
    duration: timedelta | None = Field(
        default=None, description="Duración del evento (p. ej., 2 horas, 30 minutos)"
    )
    location: str | None = Field(default=None, description="Dónde tuvo lugar el evento")

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v):
        """Parsea duración en formato string a timedelta."""
        return duration_validator(v)

    @field_serializer("duration")
    def serialize_duration(self, value: timedelta | None) -> str | None:
        """Serialize duration field to ISO format string."""
        if value is None:
            return None
        return str(value)


class Project(Entity):
    """Representa una iniciativa, objetivo o esfuerzo de varios pasos en curso con progreso rastreable."""

    type: Literal[EntityType.PROJECT] = EntityType.PROJECT
    status: ProjectStatus | None = Field(
        default=None, description="Estado actual del proyecto"
    )
    start_date: datetime | None = Field(
        default=None, description="Fecha de inicio del proyecto"
    )
    target_completion: datetime | None = Field(
        default=None, description="Fecha de finalización objetivo o esperada"
    )
    progress: float | None = Field(
        default=None,
        description="Porcentaje de finalización (0.0 a 100.0)",
        ge=0.0,
        le=100.0,
    )


class Concept(Entity):
    """Representa una idea o concepto atómico en tu sistema de conocimiento zettelkasten."""

    title: str = Field(..., description="Título conciso del concepto o idea")
    concept: str = Field(
        ...,
        description="Contenido del concepto extraído de la sección 'Concepto' del Zettel",
    )
    analysis: str = Field(
        ..., description="Tu análisis personal, ideas y comprensión del concepto"
    )
    source: str | None = Field(
        default=None, description="Fuente del concepto (libro, artículo, etc.)"
    )
    type: Literal[EntityType.CONCEPT] = EntityType.CONCEPT


class Content(Entity):
    """Representa contenido (libros, artículos, videos, etc.) que sirve como fuente de información o entretenimiento."""

    title: str = Field(..., description="Título o nombre del recurso")
    category: ResourceType = Field(..., description="Categoría del recurso")
    type: Literal[EntityType.CONTENT] = EntityType.CONTENT
    url: str | None = Field(
        default=None,
        description="URL web o ubicación donde se puede acceder al recurso",
    )
    quotes: List[str] | None = Field(
        default=None, description="Citas o extractos notables del recurso"
    )
    status: ResourceStatus | None = Field(
        default=None, description="Estado de consumo actual"
    )
    author: str | None = Field(default=None, description="Creador o autor del recurso")


class Consumable(Entity):
    """Representa un artículo que se puede consumir: comida, bebida, cigarrillos, medicamentos."""

    type: Literal[EntityType.CONSUMABLE] = EntityType.CONSUMABLE
    category: str | None = Field(
        default=None,
        description="Categoría del consumible (p. ej., comida, bebida, medicamento)",
    )


class Place(Entity):
    """Representa una ubicación (mi casa, un parque, etc.)"""

    type: Literal[EntityType.PLACE] = EntityType.PLACE
    address: str | None = Field(
        default=None, description="Dirección o descripción de la ubicación"
    )
    category: str | None = Field(
        default=None,
        description="Categoría del lugar (p. ej., casa, parque, restaurante)",
    )

