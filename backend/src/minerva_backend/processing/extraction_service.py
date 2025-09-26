import re
from typing import Dict, List

from rapidfuzz import fuzz

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Person
from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.repositories.base import BaseRepository
from minerva_backend.graph.repositories.concept_repository import ConceptRepository
from minerva_backend.graph.repositories.consumable_repository import ConsumableRepository
from minerva_backend.graph.repositories.content_repository import ContentRepository
from minerva_backend.graph.repositories.emotion_repository import EmotionRepository
from minerva_backend.graph.repositories.event_repository import EventRepository
from minerva_backend.graph.repositories.feeling_repository import FeelingRepository
from minerva_backend.graph.repositories.person_repository import PersonRepository
from minerva_backend.graph.repositories.place_repository import PlaceRepository
from minerva_backend.graph.repositories.project_repository import ProjectRepository
from minerva_backend.obsidian.obsidian_service import ObsidianService
from minerva_backend.processing.llm_service import LLMService
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_emotions import ExtractEmotionsPrompt, Feelings
from minerva_backend.prompt.extract_people import ExtractPeoplePrompt, People
from minerva_backend.prompt.extract_relationships import ExtractRelationshipsPrompt, Relationships
from minerva_backend.prompt.hydrate_person import HydratePersonPrompt
from minerva_backend.prompt.merge_summaries import MergeSummariesPrompt


class ExtractionService:
    def __init__(self,
                 connection: Neo4jConnection,
                 llm_service: LLMService,
                 obsidian_service: ObsidianService):
        self.llm_service = llm_service
        self.connection = connection
        self.entity_repositories: Dict[str, BaseRepository] = {
            'Person': PersonRepository(self.connection),
            'Feeling': FeelingRepository(self.connection),
            'Emotion': EmotionRepository(self.connection),
            'Event': EventRepository(self.connection),
            'Project': ProjectRepository(self.connection),
            'Concept': ConceptRepository(self.connection),
            'Content': ContentRepository(self.connection),
            'Consumable': ConsumableRepository(self.connection),
            'Place': PlaceRepository(self.connection),
        }
        self.obsidian_service = obsidian_service

    async def extract_entities(self, journal_entry: JournalEntry) -> List[EntitySpanMapping]:
        """Stage 1-2: Extract entities and related spans"""
        entities_spans = []

        # Step 1: Build lookup tables from Obsidian links
        obsidian_entities = await self._build_obsidian_entity_lookup(journal_entry)
        people_spans = await self._process_people(journal_entry, obsidian_entities)
        entities_spans.extend(people_spans)

        # feelings_spans = await self._process_emotions(journal_entry, people_spans)
        # entities_spans.extend(feelings_spans)

        # TODO: Add other entity types
        # projects = await self._process_projects(journal_entry, obsidian_entities)
        # concepts = await self._process_concepts(journal_entry, obsidian_entities)
        # etc.

        return entities_spans

    def hydrate_spans_for_text(self, span_texts: List[str], entry_text: str) -> List[Span]:
        """
        Given a list of span texts and the entry text, return hydrated Span objects for all found spans.
        Uses exact and fuzzy phrase matching (no word-level fallback).
        """
        spans = []
        for span_text in span_texts:
            entry_text_lower = entry_text.lower()
            span_text_lower = span_text.lower()
            span_start = entry_text_lower.find(span_text_lower)
            if span_start != -1:
                span_end = span_start + len(span_text)
                actual_text = entry_text[span_start:span_end]
                spans.append(Span(start=span_start, end=span_end, text=actual_text))
            else:
                if ' ' in span_text:
                    best_phrase_match = self._find_best_phrase_match(span_text, entry_text)
                    if best_phrase_match:
                        phrase, start_pos, end_pos, score = best_phrase_match
                        spans.append(Span(start=start_pos, end=end_pos, text=phrase))
                        print(f"Fuzzy phrase match found: '{span_text}' -> '{phrase}' (score: {score})")
                    else:
                        print(f"Warning: No suitable phrase match found for span '{span_text}'")
                else:
                    print(
                        f"Warning: No exact match found for single-word span '{span_text}' and word-level fallback is disabled.")
        return spans

    def _process_spans(self, processed_entities: List[Dict], journal_entry: JournalEntry) -> List[EntitySpanMapping]:
        """
        Generalized: takes a list of dicts with 'entity' and 'spans', hydrates spans, and returns EntitySpanMapping.
        """
        result = []
        for item in processed_entities:
            hydrated_spans = self.hydrate_spans_for_text(item['spans'], journal_entry.entry_text)
            if hydrated_spans:
                result.append(EntitySpanMapping(item['entity'], hydrated_spans))
            else:
                print(f"Warning: No valid spans found for entity '{item['entity']}'")
        return result

    def _find_best_phrase_match(self, target_span: str, text: str, min_score: int = 75) -> tuple:
        """
        Find the best matching phrase in text using a sliding window approach.
        Returns (matched_phrase, start_pos, end_pos, score) or None if no good match found.
        """

        target_words = target_span.split()
        text_words = text.split()

        if not target_words or not text_words:
            raise Exception("Target span or text is empty.")

        best_match = None
        best_score = 0

        # Try different window sizes around the target length
        for window_size in range(max(1, len(target_words) - 1), len(target_words) + 3):
            if window_size > len(text_words):
                break

            for i in range(len(text_words) - window_size + 1):
                window_words = text_words[i:i + window_size]
                window_phrase = ' '.join(window_words)

                # Calculate similarity score
                score = fuzz.ratio(target_span.lower(), window_phrase.lower())

                if score > best_score and score >= min_score:
                    # Find the actual position in the original text
                    start_pos = text.find(window_phrase)
                    if start_pos != -1:
                        end_pos = start_pos + len(window_phrase)
                        best_match = (window_phrase, start_pos, end_pos, score)
                        best_score = score

        return best_match

    async def _build_obsidian_entity_lookup(self, journal_entry: JournalEntry) -> Dict[str, Dict]:
        """Build lookup tables for existing Obsidian entities and their aliases."""

        # Extract [[links]] from journal text
        link_matches = re.findall(r'\[\[(.+?)]]', journal_entry.entry_text, re.MULTILINE)

        # Always include the user (Alex Elgier) as a potential entity
        link_matches.append("Alex Elgier")

        # Resolve all links to get entity metadata
        resolved_links = []
        for link in link_matches:
            resolved = self.obsidian_service.resolve_link(link)
            resolved_links.append(resolved)

        # Remove duplicates based on entity_long_name
        unique_links = list({link['entity_long_name']: link for link in resolved_links}.values())

        # Build name-to-entity lookup (including aliases)
        name_to_entity = {}
        entities_with_db_ids = []

        for link_data in unique_links:
            entity_name = link_data['entity_name']

            # Store entities that exist in the database
            if link_data['entity_id']:
                entities_with_db_ids.append(link_data)

            # Map primary name to entity data
            if entity_name and entity_name not in name_to_entity:
                name_to_entity[entity_name] = link_data

            # Map aliases to the same entity data
            if link_data['aliases']:
                for alias in link_data['aliases']:
                    if alias not in name_to_entity:
                        name_to_entity[alias] = link_data

        return {
            'name_lookup': name_to_entity,
            'db_entities': entities_with_db_ids,
            'glossary': {link['entity_name']: link['short_summary']
                         for link in unique_links
                         if link['entity_name'] and link['short_summary']}
        }

    async def _process_and_deduplicate_people(
            self,
            llm_people: People,
            obsidian_entities: Dict[str, Dict],
            journal_entry: JournalEntry
    ) -> List[Dict]:
        """Process and deduplicate people, preserving existing entity IDs."""

        name_lookup = obsidian_entities['name_lookup']
        processed_people = []
        seen_canonical_names = set()

        for llm_person in llm_people.people:
            person_name = llm_person.name

            # Determine if this person exists in Obsidian/DB
            existing_entity_data = name_lookup.get(person_name)

            if existing_entity_data:
                # Use canonical name from Obsidian
                canonical_name = existing_entity_data['entity_long_name']
            else:
                # Use LLM-extracted name as canonical
                canonical_name = person_name

            # Skip if we've already processed this canonical entity
            if canonical_name in seen_canonical_names:
                continue
            seen_canonical_names.add(canonical_name)

            # Hydrate the person with LLM
            hydrated_person = await self._hydrate_person(journal_entry, canonical_name)
            if not hydrated_person:
                continue

            # If entity exists in DB, preserve ID and merge properties
            if existing_entity_data and existing_entity_data['entity_id']:
                hydrated_person.uuid = existing_entity_data['entity_id']

                # Load existing entity from DB and merge properties
                existing_db_entity: Person | None = self.entity_repositories['Person'].find_by_uuid(
                    existing_entity_data['entity_id'])
                if existing_db_entity:
                    hydrated_person = await self._merge_entity_properties(
                        existing_entity=existing_db_entity,
                        new_entity=hydrated_person
                    )

            processed_people.append({
                'entity': hydrated_person,
                'spans': llm_person.spans,
                'canonical_name': canonical_name,
                'had_existing_id': bool(existing_entity_data and existing_entity_data['entity_id'])
            })

        return processed_people

    async def _merge_entity_properties(self, existing_entity: Person, new_entity: Person) -> Person:
        """Merge properties from LLM extraction with existing entity data."""
        # TODO find if necessary to handle other properties. for now only handle summary merging
        # Merge summaries using LLM
        merged_summaries = await self.llm_service.generate(
            prompt=MergeSummariesPrompt.user_prompt({
                'existing_summary': existing_entity.summary,
                'existing_short_summary': existing_entity.summary_short,
                'new_summary': new_entity.summary,
                'new_short_summary': new_entity.summary_short,
                'entity_name': existing_entity.name
            }),
            system_prompt=MergeSummariesPrompt.system_prompt(),
            response_model=MergeSummariesPrompt.response_model()
        )

        # Update entity with merged summaries
        new_entity.summary = merged_summaries['summary']
        new_entity.summary_short = merged_summaries['summary_short']
        return new_entity

    async def extract_relationships(self, journal_entry: JournalEntry,
                                    entities: List[EntitySpanMapping]) -> List[RelationSpanContextMapping]:
        """Stage 3: Extract relationships between entities"""

        # 1. Detection: Find potential relationships
        entity_context = "\n".join(
            [f"- {e.entity.name} ({e.entity.type}) uuid:'{e.entity.uuid}' short summary:'{e.entity.summary_short}'" for
             e in sorted(entities, key=lambda e: e.entity.uuid)])
        detected_relationships_result = await self.llm_service.generate(
            prompt=ExtractRelationshipsPrompt.user_prompt(
                {'text': journal_entry.entry_text, 'entities': entity_context}),
            system_prompt=ExtractRelationshipsPrompt.system_prompt(),
            response_model=ExtractRelationshipsPrompt.response_model()
        )

        detected_relationships = Relationships(**detected_relationships_result).relationships

        entity_map = {str(e.entity.uuid): e.entity for e in entities}
        result = []
        for rel in detected_relationships:
            # Raise exception if we can't map detected source/target/context uuids to curated ones
            # Gather all UUIDs to validate
            uuids_to_check = [rel.source, rel.target]
            if rel.context:
                uuids_to_check.extend([ctx.entity_uuid for ctx in rel.context])

            # Check all UUIDs at once
            invalid_uuids = [uuid for uuid in uuids_to_check if uuid not in entity_map]
            if invalid_uuids:
                print(f"Invalid UUID(s) detected: {invalid_uuids}")
                continue
            rel_data = rel.model_dump(exclude={'context', 'spans'})
            relation = Relation(**rel_data)
            # Hydrate relationship spans using the generalized method
            hydrated_spans = self.hydrate_spans_for_text(rel.spans, journal_entry.entry_text) if rel.spans else []
            result.append(RelationSpanContextMapping(relation, hydrated_spans, rel.context))
        return result

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

    async def _process_people(self, journal_entry: JournalEntry,
                              obsidian_entities: Dict[str, Dict]) -> List[EntitySpanMapping]:
        result = await self.llm_service.generate(
            prompt=ExtractPeoplePrompt.user_prompt({'text': journal_entry.entry_text}),
            system_prompt=ExtractPeoplePrompt.system_prompt(),
            response_model=ExtractPeoplePrompt.response_model()
        )
        if not result:
            raise Exception("LLM did not return any people data.")
        llm_extracted_people = People(**result)

        processed_people = await self._process_and_deduplicate_people(
            llm_extracted_people, obsidian_entities, journal_entry
        )

        people_spans = self._process_spans(processed_people, journal_entry)
        return people_spans

    async def _process_emotions(self, journal_entry: JournalEntry,
                                people_spans: List[EntitySpanMapping]) -> List[EntitySpanMapping]:
        people_context = "\n".join(
            [f"- {e.entity.name} uuid:'{e.entity.uuid}'" for e in sorted(people_spans, key=lambda e: e.entity.uuid)])
        result = await self.llm_service.generate(
            prompt=ExtractEmotionsPrompt.user_prompt({'text': journal_entry.entry_text, 'people': people_context}),
            system_prompt=ExtractEmotionsPrompt.system_prompt(),
            response_model=ExtractEmotionsPrompt.response_model()
        )
        if not result:
            raise Exception("LLM did not return any feeling data.")
        llm_extracted_feelings = Feelings(**result)

        feelings_spans = self._process_spans([f.model_dump() for f in llm_extracted_feelings.feelings], journal_entry)

        return feelings_spans
