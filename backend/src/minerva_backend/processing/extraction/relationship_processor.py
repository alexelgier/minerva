from typing import List

from minerva_models import Relation
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import CuratableMapping
from minerva_backend.prompt.extract_relationships import (
    ExtractRelationshipsPrompt,
    Relationships,
)


class RelationshipProcessor(BaseEntityProcessor):
    """Specialized processor for relationships between entities."""

    @property
    def entity_type(self) -> str:
        return "Relationship"

    async def process(self, context: ExtractionContext) -> List[CuratableMapping]:
        """Process relationships between extracted entities."""
        if not context.extracted_entities:
            print("No extracted entities to process relationships")
            return []

        # Generate relationships using LLM
        detected_relationships = await self._generate_relationships(context)

        # Create entity mapping for validation
        entity_map = self._create_entity_map(context.extracted_entities)

        # Process and validate relationships
        return self._process_detected_relationships(
            detected_relationships, entity_map, context.journal_entry.entry_text or ""
        )

    async def _generate_relationships(self, context: ExtractionContext) -> List:
        """Generate relationships using LLM."""
        entity_context = self._build_entity_context(context.extracted_entities)

        detected_relationships_result = await self.llm_service.generate(
            prompt=ExtractRelationshipsPrompt.user_prompt(
                {
                    "text": context.journal_entry.entry_text or "",
                    "entities": entity_context,
                }
            ),
            system_prompt=ExtractRelationshipsPrompt.system_prompt(),
            response_model=ExtractRelationshipsPrompt.response_model(),
        )

        return Relationships(**detected_relationships_result).relationships

    def _build_entity_context(self, extracted_entities) -> str:
        """Build entity context string for the prompt."""
        return "\n".join(
            [
                f"- {e.entity.name} ({e.entity.type}) uuid:'{e.entity.uuid}' short summary:'{e.entity.summary_short}'"
                for e in sorted(extracted_entities, key=lambda e: e.entity.uuid)
            ]
        )

    def _create_entity_map(self, extracted_entities) -> dict:
        """Create UUID to entity mapping for validation."""
        return {str(e.entity.uuid): e.entity for e in extracted_entities}

    def _process_detected_relationships(
        self, detected_relationships: List, entity_map: dict, entry_text: str
    ) -> List[CuratableMapping]:
        """Process and validate detected relationships."""
        result: List[CuratableMapping] = []

        for rel in detected_relationships:
            if not self._validate_relationship_uuids(rel, entity_map):
                continue

            relation = self._create_relation_from_detected(rel)
            hydrated_spans = self._hydrate_relationship_spans(rel, entry_text)

            result.append(
                CuratableMapping(
                    kind="relation",
                    data=relation,
                    spans=hydrated_spans,
                    context=rel.context,
                )
            )

        return result

    def _validate_relationship_uuids(self, rel, entity_map: dict) -> bool:
        """Validate that all UUIDs in the relationship exist in the entity map."""
        uuids_to_check = [rel.source, rel.target]
        if rel.context:
            uuids_to_check.extend([ctx.entity_uuid for ctx in rel.context])

        invalid_uuids = [uuid for uuid in uuids_to_check if uuid not in entity_map]
        if invalid_uuids:
            print(f"Invalid UUID(s) detected: {invalid_uuids}")
            return False
        return True

    def _create_relation_from_detected(self, rel) -> Relation:
        """Create a Relation object from detected relationship data."""
        rel_data = rel.model_dump(exclude={"context", "spans"})
        return Relation(**rel_data)

    def _hydrate_relationship_spans(self, rel, entry_text: str) -> List:
        """Hydrate spans for the relationship."""
        return (
            self.span_service.hydrate_spans_for_text(rel.spans, entry_text)
            if rel.spans
            else []
        )
