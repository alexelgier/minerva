from dataclasses import dataclass
from typing import Dict, List, Optional

from minerva_models import JournalEntry
from minerva_backend.graph.services.knowledge_graph_service import KnowledgeGraphService
from minerva_backend.processing.models import EntityMapping


@dataclass
class ExtractionContext:
    """Contexto compartido durante la extracción de entidades."""

    journal_entry: JournalEntry
    obsidian_entities: Dict[str, Dict]
    kg_service: KnowledgeGraphService
    people_context: Optional[Dict[str, str]] = None
    extracted_entities: Optional[List[EntityMapping]] = None

    def __post_init__(self):
        if self.extracted_entities is None:
            self.extracted_entities = []

    def add_entities(self, entities: List[EntityMapping]):
        """Agrega entidades extraídas al contexto."""
        if self.extracted_entities is None:
            self.extracted_entities = []
        self.extracted_entities.extend(entities)

    def get_people_context_string(self) -> str:
        """Retorna el contexto de personas como string para prompts."""
        if not self.extracted_entities:
            return ""

        people_entities = [
            e for e in self.extracted_entities if e.entity.type == "Person"
        ]
        return "\n".join(
            [
                f"- {e.entity.name} uuid:'{e.entity.uuid}'"
                for e in sorted(people_entities, key=lambda e: e.entity.uuid)
            ]
        )

    def get_concepts_context_string(self) -> List[Dict[str, str]]:
        """Retorna el contexto de conceptos como lista de diccionarios para prompts."""
        if not self.extracted_entities:
            return []

        concept_entities = [
            e for e in self.extracted_entities if e.entity.type == "Concept"
        ]
        return [
            {"name": e.entity.name, "uuid": e.entity.uuid}
            for e in sorted(concept_entities, key=lambda e: e.entity.uuid)
        ]
