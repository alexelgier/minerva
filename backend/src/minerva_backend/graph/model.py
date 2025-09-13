from __future__ import annotations

from abc import ABC
from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import List, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


# ----------------------------
# Core entity + relationship + partition types
# ----------------------------

class EntityType(str, Enum):
    PERSON = "PERSON"
    FEELING = "FEELING"
    EMOTION = "EMOTION"
    EVENT = "EVENT"
    PROJECT = "PROJECT"
    CONCEPT = "CONCEPT"
    RESOURCE = "RESOURCE"


class DocumentType(str, Enum):
    JOURNAL_ENTRY = "JOURNAL_ENTRY"


class RelationshipType(str, Enum):
    RELATED_TO = "RELATED_TO"


class PartitionType(str, Enum):
    DOMAIN = "DOMAIN"
    LEXICAL = "LEXICAL"


# ----------------------------
# Base Entity
# ----------------------------

class Node(BaseModel, ABC):
    """Entidad abstracta. Todos los nodos tienen al menos estos campos."""
    partition: PartitionType = Field(..., description='partición del grafo')
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        extra = "allow"  # allow schema evolution (new fields in future)
        use_enum_values = True


class Entity(Node, ABC):
    name: str = Field(..., description='nombre de la entidad')
    type: EntityType = Field(..., description="Tipo de entidad (Persona, Evento, etc)")
    summary_short: str = Field(..., description="Resumen de la entidad. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen de la entidad. Máximo 300 palabras")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Tipo de partición (siempre DOMAIN)")
    name_embedding: list[float] | None = Field(default=None, description='embedding del nombre')


class Document(Node, ABC):
    type: DocumentType = Field(..., description="Tipo de documento")
    text: str = Field(..., description="El texto original del documento")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Tipo de partición (siempre LEXICAL)")


class Chunk(Node, ABC):
    text: str = Field(..., description="El texto del fragmento")
    partition: Literal[PartitionType.LEXICAL] = Field(PartitionType.LEXICAL.value,
                                                      description="Tipo de partición (siempre LEXICAL)")
    embedding: list[float] | None = Field(default=None, description='embedding del fragmento')


# ----------------------------
# Enums
# ----------------------------

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


# ----------------------------
# Specific entities (all extend Entity)
# ----------------------------

class Person(Entity):
    """Representa a una persona individual."""
    type: Literal[EntityType.PERSON] = Field(EntityType.PERSON.value, description="Tipo de entidad (siempre PERSON)")
    occupation: str | None = Field(default=None, description="Cargo o profesión")
    birth_date: date | None = Field(default=None, description="Fecha de nacimiento")


class Emotion(Entity):
    """Representa un tipo distinto de emoción que se puede sentir"""
    type: Literal[EntityType.EMOTION] = Field(EntityType.EMOTION.value, description="Tipo de entidad (siempre EMOTION)")


class Feeling(Entity):
    """Relación reificada: Una persona experimenta una emoción o pensamiento sobre algo"""
    timestamp: datetime = Field(..., description="Cuándo ocurrió este sentimiento")
    type: Literal[EntityType.FEELING] = Field(EntityType.FEELING.value, description="Tipo de entidad (siempre FEELING)")
    intensity: int | None = Field(default=None, description="Nivel de intensidad (1-10)", ge=1, le=10)
    duration: timedelta | None = Field(default=None, description="Cuánto duró el sentimiento")


class Event(Entity):
    """Representa un suceso o actividad notable que ocurrió en un momento específico."""
    category: str = Field(..., description="Categoría del evento (reunión, entrenamiento, etc)")
    date: datetime = Field(..., description="Cuándo ocurrió el evento")
    type: Literal[EntityType.EVENT] = Field(EntityType.EVENT.value, description="Tipo de entidad (siempre EVENT)")
    duration: timedelta | None = Field(default=None, description="Duración del evento (p. ej., 2 horas, 30 minutos)")
    location: str | None = Field(default=None, description="Dónde tuvo lugar el evento")


class Project(Entity):
    """Representa una iniciativa, objetivo o esfuerzo de varios pasos en curso con progreso rastreable."""
    type: Literal[EntityType.PROJECT] = Field(EntityType.PROJECT.value, description="Tipo de entidad (siempre PROJECT)")
    status: ProjectStatus | None = Field(default=None, description="Estado actual del proyecto")
    start_date: datetime | None = Field(default=None, description="Fecha de inicio del proyecto")
    target_completion: datetime | None = Field(default=None, description="Fecha de finalización objetivo o esperada")
    progress: float | None = Field(default=None, description="Porcentaje de finalización (0.0 a 100.0)", ge=0.0, le=100.0)


class Concept(Entity):
    """Representa una idea o concepto atómico en tu sistema de conocimiento zettelkasten."""
    title: str = Field(..., description="Título conciso del concepto o idea")
    analysis: str = Field(..., description="Tu análisis personal, ideas y comprensión del concepto")
    type: Literal[EntityType.CONCEPT] = Field(EntityType.CONCEPT.value, description="Tipo de entidad (siempre CONCEPT)")


class Resource(Entity):
    """Representa contenido externo (libros, artículos, videos) que sirve como fuente de información o entretenimiento."""
    title: str = Field(..., description="Título o nombre del recurso")
    category: ResourceType = Field(..., description="Categoría del recurso")
    type: Literal[EntityType.RESOURCE] = Field(EntityType.RESOURCE.value, description="Tipo de entidad (siempre RESOURCE)")
    url: str | None = Field(default=None, description="URL web o ubicación donde se puede acceder al recurso")
    quotes: List[str] | None = Field(default=None, description="Citas o extractos notables del recurso")
    status: ResourceStatus | None = Field(default=None, description="Estado de consumo actual")
    author: str | None = Field(default=None, description="Creador o autor del recurso")


class JournalEntry(Document):
    date: date = Field(..., description="Fecha de la entrada del diario")
    type: Literal[DocumentType.JOURNAL_ENTRY] = Field(DocumentType.JOURNAL_ENTRY.value,
                                                      description="Tipo de documento (siempre JOURNAL_ENTRY)")
    entry_text: str | None = Field(default=None, description="El texto principal de la entrada del diario")
    panas_pos: List[float] | None = Field(default=None, description="Puntuaciones positivas PANAS")
    panas_neg: List[float] | None = Field(default=None, description="Puntuaciones negativas PANAS")
    bpns: List[float] | None = Field(default=None, description="Puntuaciones BPNS")
    flourishing: List[float] | None = Field(default=None, description="Puntuaciones de florecimiento")
    wake: datetime | None = Field(default=None, description="Fecha y hora de despertar")
    sleep: datetime | None = Field(default=None, description="Fecha y hora de dormir")
