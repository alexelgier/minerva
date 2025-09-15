from __future__ import annotations

from abc import ABC
from datetime import date, datetime, timedelta
from typing import List, Literal

from pydantic import Field

from .base import Node
from .enums import EntityType, ProjectStatus, ResourceStatus, ResourceType, PartitionType


class Entity(Node, ABC):
    name: str = Field(..., description='nombre de la entidad')
    type: EntityType = Field(..., description="Tipo de entidad (Persona, Evento, etc)")
    summary_short: str = Field(..., description="Resumen de la entidad. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen de la entidad. Máximo 300 palabras")
    partition: Literal[PartitionType.DOMAIN] = Field(PartitionType.DOMAIN.value,
                                                     description="Tipo de partición (siempre DOMAIN)")
    name_embedding: list[float] | None = Field(default=None, description='embedding del nombre')


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
    progress: float | None = Field(default=None, description="Porcentaje de finalización (0.0 a 100.0)", ge=0.0,
                                   le=100.0)


class Concept(Entity):
    """Representa una idea o concepto atómico en tu sistema de conocimiento zettelkasten."""
    title: str = Field(..., description="Título conciso del concepto o idea")
    analysis: str = Field(..., description="Tu análisis personal, ideas y comprensión del concepto")
    type: Literal[EntityType.CONCEPT] = Field(EntityType.CONCEPT.value, description="Tipo de entidad (siempre CONCEPT)")


class Resource(Entity):
    """Representa contenido (libros, artículos, videos, etc.) que sirve como fuente de información o entretenimiento."""
    title: str = Field(..., description="Título o nombre del recurso")
    category: ResourceType = Field(..., description="Categoría del recurso")
    type: Literal[EntityType.RESOURCE] = Field(EntityType.RESOURCE.value,
                                               description="Tipo de entidad (siempre RESOURCE)")
    url: str | None = Field(default=None, description="URL web o ubicación donde se puede acceder al recurso")
    quotes: List[str] | None = Field(default=None, description="Citas o extractos notables del recurso")
    status: ResourceStatus | None = Field(default=None, description="Estado de consumo actual")
    author: str | None = Field(default=None, description="Creador o autor del recurso")


class Consumable(Entity):
    """Representa un artículo que se puede consumir: comida, bebida, cigarrillos, medicamentos."""
    type: Literal[EntityType.CONSUMABLE] = Field(EntityType.CONSUMABLE.value,
                                                 description="Tipo de entidad (siempre CONSUMABLE)")
    category: str | None = Field(default=None,
                                 description="Categoría del consumible (p. ej., comida, bebida, medicamento)")


class Place(Entity):
    """Representa una ubicación (mi casa, un parque, etc.)"""
    type: Literal[EntityType.PLACE] = Field(EntityType.PLACE.value, description="Tipo de entidad (siempre PLACE)")
    address: str | None = Field(default=None, description="Dirección o descripción de la ubicación")
    category: str | None = Field(default=None, description="Categoría del lugar (p. ej., casa, parque, restaurante)")
