import re
from typing import List, Dict, Any

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person, Entity
from minerva_backend.graph.models.enums import EntityType
from minerva_backend.graph.models.relations import Relation
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.prompt.extract_people import ExtractPeoplePrompt, People
from minerva_backend.prompt.hydrate_person import HydratePersonPrompt


class ExtractionService:
    def __init__(self, llm_service: LLMService, obsidian_service: ObsidianService):
        self.llm_service = llm_service
        self.obsidian_service = obsidian_service

    async def extract_entities(self, journal_entry: JournalEntry) -> List[Entity]:
        """Stage 1-2: Extract standalone and relational entities using LLM"""

        # get [[links]] from text
        matches = re.findall(r'\[\[(.+?)\]\]', journal_entry.entry_text, re.MULTILINE)
        links = [self.obsidian_service.resolve_link(link) for link in matches]
        links.append(self.obsidian_service.resolve_link("Alex Elgier"))
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

        if not people or not people.people:
            return entities

        # Deduplicate people based on Obsidian links and aliases
        unique_people_to_hydrate: Dict[str, Dict[str, Any]] = {}
        for person in people.people:
            if person.name in names_map:
                link_info = names_map[person.name]['link_map']
                canonical_name = link_info['entity_long_name']
                if canonical_name not in unique_people_to_hydrate:
                    unique_people_to_hydrate[canonical_name] = {
                        "name": canonical_name,
                        "link_info": link_info
                    }
            else:
                # This person does not have an Obsidian note
                if person.name not in unique_people_to_hydrate:
                    unique_people_to_hydrate[person.name] = {
                        "name": person.name,
                        "link_info": None
                    }

        # Stage 2: Extract properties (hydration)
        hydrated_people: List[Person] = []
        for person_info in unique_people_to_hydrate.values():
            hydrated_person = await self._hydrate_person(journal_entry, person_info['name'])

            if hydrated_person:
                # If person was linked to a note with a DB entry, preserve the ID
                if person_info['link_info'] and person_info['link_info']['entity_id']:
                    hydrated_person.uuid = person_info['link_info']['entity_id']
                hydrated_people.append(hydrated_person)

        entities.extend(hydrated_people)

        # projects = extract_projects()
        # concepts = extract_concepts()
        # resources = extract_resources()
        # events = extract_events()
        # consumables = extract_consumables()
        # places = extract_places()

        # 1.1 (Optional) reflexion

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

    async def _hydrate_person(self, journal_entry: JournalEntry, person_name: str) -> Person | None:
        """Hydrates a single person entity with more details using an LLM call."""
        result = await self.llm_service.generate(
            prompt=HydratePersonPrompt.user_prompt({'text': journal_entry.entry_text, 'name': person_name}),
            system_prompt=HydratePersonPrompt.system_prompt(),
            response_model=HydratePersonPrompt.response_model()
        )
        if result:
            return Person(**result)
        return None

    async def _filter_glossary(self, journal_entry: JournalEntry, glossary: Dict[str, str]):
        pass
