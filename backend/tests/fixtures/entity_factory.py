"""
Factory for creating realistic entities based on actual journal content.

This factory generates test data that closely mirrors the entities
extracted from real journal entries in the Minerva system.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from minerva_backend.graph.models.entities import (
    Consumable,
    Content,
    Emotion,
    EntityType,
    Event,
    FeelingEmotion,
    FeelingConcept,
    Person,
    Place,
    Project,
    ProjectStatus,
    ResourceStatus,
    ResourceType,
)
from minerva_backend.graph.models.relations import Relation


class EntityFactory:
    """Factory for creating realistic entities for testing."""
    
    # Sample data based on real journal entries
    SAMPLE_PEOPLE = [
        {"name": "Ana Sorin", "occupation": "Desarrolladora", "birth_date": date(1990, 5, 15)},
        {"name": "Whitehead", "occupation": "Filósofo", "birth_date": None},
        {"name": "Federico Demarchi", "occupation": "Desarrollador", "birth_date": None},
    ]
    
    SAMPLE_PLACES = [
        {"name": "patio", "category": "casa", "address": "Mi casa"},
        {"name": "Chino", "category": "restaurante", "address": "Cerca de casa"},
        {"name": "casa", "category": "hogar", "address": "Mi domicilio"},
    ]
    
    SAMPLE_PROJECTS = [
        {"name": "Minerva", "status": ProjectStatus.ACTIVE, "progress": 75.0},
        {"name": "Música", "status": ProjectStatus.ON_HOLD, "progress": 30.0},
    ]
    
    SAMPLE_CONSUMABLES = [
        {"name": "Mate", "category": "bebida"},
        {"name": "Dip de Morrón Asado", "category": "comida"},
        {"name": "Nachos", "category": "comida"},
        {"name": "Milanesa de Soja", "category": "comida"},
        {"name": "Ensalada", "category": "comida"},
        {"name": "Té", "category": "bebida"},
    ]
    
    SAMPLE_CONTENT = [
        {"name": "One Piece", "category": ResourceType.MOVIE, "status": ResourceStatus.IN_PROGRESS},
        {"name": "Elefante", "category": ResourceType.MOVIE, "status": ResourceStatus.COMPLETED},
        {"name": "YouTube", "category": ResourceType.YOUTUBE, "status": ResourceStatus.IN_PROGRESS},
    ]
    
    SAMPLE_EVENTS = [
        {"name": "Cena", "category": "comida", "location": "casa"},
        {"name": "Sexo", "category": "personal", "location": "casa"},
        {"name": "Trabajar", "category": "trabajo", "location": "casa"},
    ]
    
    SAMPLE_FEELINGS = [
        {"name": "alegría", "intensity": 8, "emotion": "happiness"},
        {"name": "triste", "intensity": 6, "emotion": "sadness"},
        {"name": "apesadumbrada", "intensity": 7, "emotion": "sadness"},
        {"name": "amorosa", "intensity": 9, "emotion": "love"},
    ]
    
    @classmethod
    def create_person(
        cls,
        name: str = None,
        occupation: str = None,
        birth_date: Optional[date] = None,
        **kwargs
    ) -> Person:
        """Create a Person entity."""
        if name is None:
            sample = cls.SAMPLE_PEOPLE[0]
            name = sample["name"]
            occupation = occupation or sample["occupation"]
            birth_date = birth_date or sample["birth_date"]
        
        return Person(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.PERSON,
            summary_short=f"Persona: {name}",
            summary=f"Persona llamada {name}. {f'Profesión: {occupation}' if occupation else ''}",
            occupation=occupation,
            birth_date=birth_date,
            **kwargs
        )
    
    @classmethod
    def create_place(
        cls,
        name: str = None,
        category: str = None,
        address: str = None,
        **kwargs
    ) -> Place:
        """Create a Place entity."""
        if name is None:
            sample = cls.SAMPLE_PLACES[0]
            name = sample["name"]
            category = category or sample["category"]
            address = address or sample["address"]
        
        return Place(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.PLACE,
            summary_short=f"Lugar: {name}",
            summary=f"Lugar llamado {name}. {f'Categoría: {category}' if category else ''}",
            category=category,
            address=address,
            **kwargs
        )
    
    @classmethod
    def create_project(
        cls,
        name: str = None,
        status: ProjectStatus = None,
        progress: float = None,
        **kwargs
    ) -> Project:
        """Create a Project entity."""
        if name is None:
            sample = cls.SAMPLE_PROJECTS[0]
            name = sample["name"]
            status = status or sample["status"]
            progress = progress or sample["progress"]
        
        return Project(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.PROJECT,
            summary_short=f"Proyecto: {name}",
            summary=f"Proyecto llamado {name}. Estado: {status.value if status else 'No especificado'}",
            status=status,
            progress=progress,
            **kwargs
        )
    
    @classmethod
    def create_consumable(
        cls,
        name: str = None,
        category: str = None,
        **kwargs
    ) -> Consumable:
        """Create a Consumable entity."""
        if name is None:
            sample = cls.SAMPLE_CONSUMABLES[0]
            name = sample["name"]
            category = category or sample["category"]
        
        return Consumable(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.CONSUMABLE,
            summary_short=f"Consumible: {name}",
            summary=f"Consumible llamado {name}. {f'Categoría: {category}' if category else ''}",
            category=category,
            **kwargs
        )
    
    @classmethod
    def create_content(
        cls,
        name: str = None,
        category: ResourceType = None,
        status: ResourceStatus = None,
        **kwargs
    ) -> Content:
        """Create a Content entity."""
        if name is None:
            sample = cls.SAMPLE_CONTENT[0]
            name = sample["name"]
            category = category or sample["category"]
            status = status or sample["status"]
        
        return Content(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.CONTENT,
            summary_short=f"Contenido: {name}",
            summary=f"Contenido llamado {name}. {f'Categoría: {category.value}' if category else ''}",
            title=name,
            category=category,
            status=status,
            **kwargs
        )
    
    @classmethod
    def create_event(
        cls,
        name: str = None,
        category: str = None,
        location: str = None,
        event_date: Optional[datetime] = None,
        **kwargs
    ) -> Event:
        """Create an Event entity."""
        if name is None:
            sample = cls.SAMPLE_EVENTS[0]
            name = sample["name"]
            category = category or sample["category"]
            location = location or sample["location"]
        
        if event_date is None:
            event_date = datetime.now()
        
        return Event(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.EVENT,
            summary_short=f"Evento: {name}",
            summary=f"Evento llamado {name}. {f'Categoría: {category}' if category else ''}",
            category=category,
            date=event_date,
            location=location,
            **kwargs
        )
    
    @classmethod
    def create_feeling_emotion(
        cls,
        name: str = None,
        intensity: int = None,
        emotion: str = None,
        person_uuid: str = None,
        **kwargs
    ) -> FeelingEmotion:
        """Create a FeelingEmotion entity."""
        if name is None:
            sample = cls.SAMPLE_FEELINGS[0]
            name = sample["name"]
            intensity = intensity or sample["intensity"]
            emotion = emotion or sample["emotion"]
        
        return FeelingEmotion(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.FEELING_EMOTION,
            summary_short=f"Sentimiento: {name}",
            summary=f"Sentimiento de {name}. Intensidad: {intensity}/10",
            timestamp=datetime.now(),
            intensity=intensity,
            person_uuid=person_uuid,
            **kwargs
        )
    
    @classmethod
    def create_feeling_concept(
        cls,
        name: str = None,
        intensity: int = None,
        person_uuid: str = None,
        concept_uuid: str = None,
        **kwargs
    ) -> FeelingConcept:
        """Create a FeelingConcept entity."""
        if name is None:
            name = "Sentimiento sobre concepto"
            intensity = intensity or 5
        
        return FeelingConcept(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.FEELING_CONCEPT,
            summary_short=f"Sentimiento: {name}",
            summary=f"Sentimiento sobre concepto. Intensidad: {intensity}/10",
            timestamp=datetime.now(),
            intensity=intensity,
            person_uuid=person_uuid,
            concept_uuid=concept_uuid,
            **kwargs
        )
    
    @classmethod
    def create_emotion(cls, name: str = "happiness") -> Emotion:
        """Create an Emotion entity."""
        return Emotion(
            uuid=str(uuid4()),
            name=name,
            type=EntityType.EMOTION,
            summary_short=f"Emoción: {name}",
            summary=f"Tipo de emoción: {name}"
        )
    
    @classmethod
    def create_relation(
        cls,
        source_uuid: str,
        target_uuid: str,
        proposed_types: List[str] = None,
        summary_short: str = None,
        summary: str = None,
        **kwargs
    ) -> Relation:
        """Create a Relation entity."""
        if proposed_types is None:
            proposed_types = ["RELATED_TO", "MENTIONED"]
        
        if summary_short is None:
            summary_short = "Relación entre entidades"
        
        if summary is None:
            summary = "Relación establecida entre dos entidades del conocimiento"
        
        return Relation(
            uuid=str(uuid4()),
            source=source_uuid,
            target=target_uuid,
            type="RELATED_TO",
            proposed_types=proposed_types,
            summary_short=summary_short,
            summary=summary,
            **kwargs
        )
    
    @classmethod
    def create_entity_set(cls) -> Dict[str, List]:
        """Create a complete set of sample entities for testing."""
        return {
            "people": [cls.create_person() for _ in range(3)],
            "places": [cls.create_place() for _ in range(3)],
            "projects": [cls.create_project() for _ in range(2)],
            "consumables": [cls.create_consumable() for _ in range(5)],
            "content": [cls.create_content() for _ in range(3)],
            "events": [cls.create_event() for _ in range(3)],
            "feelings": [cls.create_feeling_emotion() for _ in range(4)],
            "emotions": [cls.create_emotion() for _ in range(5)],
        }
