import re
from typing import List, Dict

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Feeling, Emotion, Event, Project, Concept, Resource, \
    Consumable, Place, Entity
from minerva_backend.graph.models.enums import EntityType
from minerva_backend.graph.models.relations import Relation
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.llm_service import LLMService




class ExtractionService:
    def __init__(self, llm_service: LLMService, obsidian_service: ObsidianService):
        self.llm_service = llm_service
        self.obsidian_service = obsidian_service

    async def extract_entities(self, journal_entry: JournalEntry) -> List[Entity]:
        """Stage 1-2: Extract standalone and relational entities using LLM"""

        # get [[links]] from text
        matches = re.findall(r'\[\[(.+?)\]\]', journal_entry.entry_text, re.MULTILINE)
        links = [self.obsidian_service.resolve_link(link) for link in matches]
        glossary = {x['entity_name']: x['short_summary'] for x in links}

        filtered_glossary = await self._filter_glossary(journal_entry, glossary)
        # pick top 5 glossary entries
        link_entities = [link for link in links if link['entity_id']]

        entities = []
        # Stage 1: Extract Person, Project, Concept, Resource, Event, Consumable, Place
        people = await self.extract_people(journal_entry, link_entities)

        # projects = extract_projects()
        # concepts = extract_concepts()
        # resources = extract_resources()
        # events = extract_events()
        # consumables = extract_consumables()
        # places = extract_places()

        # 1.1 (Optional) reflexion

        # Stage 2: Extract

        return entities

    async def extract_relationships(self, journal_entry: JournalEntry, entities: List[Entity]) -> List[Relation]:
        """Stage 3: Extract relationships between entities"""
        pass

    async def extract_people(self, journal_entry: JournalEntry, link_entities: List[Dict]):
        link_people = [p for p in link_entities if p['entity_type'] == EntityType.PERSON]
        # both prompts should live in some other file, something like
        # prompt = prompts.extract_people.user(journal_entry.entry_text)
        # system_prompt = prompts.extract_people.system()
        return await self.llm_service.generate(prompt, system_prompt, prompts.extract_people.response_model)

    async def _filter_glossary(self, journal_entry: JournalEntry, glossary: Dict[str, str]):
        pass
