import re
from typing import List

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Feeling, Emotion, Event, Project, Concept, Resource, Entity
from minerva_backend.obsidian.obsidian_service import ObsidianService


class ExtractionService:
    def __init__(self, obsidian_service: ObsidianService):
        self.obsidian_service = obsidian_service

    async def extract_entities(self, journal_entry: JournalEntry) -> List[Entity]:
        """Stage 1-2: Extract standalone and relational entities using LLM"""

        # get [[links]] from text
        matches = re.findall(r'\[\[(.+?)\]\]', journal_entry.entry_text, re.MULTILINE)
        links = [self.obsidian_service.resolve_link(link) for link in matches]
        link_entities = [link for link in links if link['entity_id']]

        entities = []
        # Stage 1: Extract Person, Project, Concept, Resource, Event, Consumable, Place
        # 1.1 (Optional) reflexion

        # Stage 2: Extract

        return entities

    async def extract_relationships(self, journal_entry: JournalEntry, entities: List[Entity]) -> List[Relation]:
        """Stage 3: Extract relationships between entities"""
        return await self.extraction_service.extract_relationships(journal_entry.entry_text, entities)
