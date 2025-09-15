import json
import re
from typing import List, Dict, Any

from pydantic import BaseModel, Field

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Feeling, Emotion, Event, Project, Concept, Resource, \
    Consumable, Place, Entity
from minerva_backend.graph.models.enums import EntityType
from minerva_backend.graph.models.relations import Relation
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.prompt.extract_people import ExtractPeoplePrompt, People


class ExtractionService:
    def __init__(self, llm_service: LLMService, obsidian_service: ObsidianService):
        self.llm_service = llm_service
        self.obsidian_service = obsidian_service

    async def extract_entities(self, journal_entry: JournalEntry) -> List[Entity]:
        """Stage 1-2: Extract standalone and relational entities using LLM"""

        # get [[links]] from text
        matches = re.findall(r'\[\[(.+?)\]\]', journal_entry.entry_text, re.MULTILINE)
        links = [self.obsidian_service.resolve_link(link) for link in matches]
        links = list({d['entity_long_name']: d for d in links}.values())
        glossary = {x['entity_name']: x['short_summary'] for x in links if x['short_summary']}
        names_map = {}
        for link in links:
            if link['entity_name'] in names_map:
                raise Exception("Duplicate entity")
            names_map[link['entity_name']] = {'link_map': link}
            if link['aliases'] is not None:
                for alias in link['aliases']:
                    names_map[alias] = {'link_map': link}

        # pick top 5 glossary entries
        filtered_glossary = await self._filter_glossary(journal_entry, glossary)

        link_entities = [link for link in links if link['entity_id']]

        entities = []

        # Stage 1: Extract Person, Project, Concept, Resource, Event, Consumable, Place
        people = await self.extract_people(journal_entry, link_entities)

        # dedupe
        matches = []
        unlinked = []
        misses = []
        for person in people.people:
            if person.name in names_map:
                if names_map[person.name]['link_map']['entity_id']:
                    matches[person.name] =
                unlinked.append(names_map[person.name])
            else:
                misses.append(person)

        # projects = extract_projects()
        # concepts = extract_concepts()
        # resources = extract_resources()
        # events = extract_events()
        # consumables = extract_consumables()
        # places = extract_places()

        # 1.1 (Optional) reflexion

        # Stage 2: Extract properties (hydration)

        return entities

    async def extract_relationships(self, journal_entry: JournalEntry, entities: List[Entity]) -> List[Relation]:
        """Stage 3: Extract relationships between entities"""
        pass

    async def extract_people(self, journal_entry: JournalEntry, link_entities: List[Dict]) -> People | None:
        link_people = [p for p in link_entities if p['entity_type'] == EntityType.PERSON]
        link_people_names = [p['entity_name'] for p in link_people]

        result = await self.llm_service.generate(
            prompt=ExtractPeoplePrompt.user_prompt({'text': journal_entry.entry_text}),
            system_prompt=ExtractPeoplePrompt.system_prompt(),
            response_model=ExtractPeoplePrompt.response_model()
        )
        if result:
            return People(**result)

    async def _filter_glossary(self, journal_entry: JournalEntry, glossary: Dict[str, str]):
        pass
