import logging
from typing import Dict, List, Optional, Tuple

from minerva_models import ConceptRelation, ConceptRelationType
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import CuratableMapping
from minerva_backend.prompt.extract_concept_relations import (
    ConceptRelations,
    ExtractConceptRelationsPrompt,
)


class ConceptRelationProcessor(BaseEntityProcessor):
    """Specialized processor for concept relations."""

    def __init__(
        self, llm_service, entity_repositories, span_service, obsidian_service
    ):
        super().__init__(
            llm_service, entity_repositories, span_service, obsidian_service
        )
        self.logger = logging.getLogger(__name__)

    @property
    def concept_repository(self):
        """Direct access to concept repository."""
        return self.entity_repositories["Concept"]

    @property
    def entity_type(self) -> str:
        return "ConceptRelation"

    async def process(self, context: ExtractionContext) -> List[CuratableMapping]:
        """Process concept relations between extracted concepts."""
        # Get extracted concepts
        concept_entities = self._get_concept_entities(context)
        if not concept_entities:
            return []

        # Process all concepts and collect relations
        all_relations = await self._process_all_concepts(concept_entities, context)

        # Validate and convert to final result
        return self._create_relation_mappings(all_relations, context)

    def _get_concept_entities(self, context: ExtractionContext) -> List:
        """Get extracted concept entities from context."""
        return [
            e for e in (context.extracted_entities or []) if e.entity.type == "Concept"
        ]

    async def _process_all_concepts(
        self, concept_entities: List, context: ExtractionContext
    ) -> Dict:
        """Process all concepts and collect their relations."""
        all_relations: Dict[Tuple[str, str], str] = (
            {}
        )  # (source_uuid, target_uuid) -> relation_type

        for concept_entity in concept_entities:
            try:
                await self._process_single_concept(
                    concept_entity, concept_entities, context, all_relations
                )
            except Exception as e:
                self.logger.error(
                    f"Failed to process relations for concept {concept_entity.entity.name}: {e}"
                )
                continue  # Continue with next concept

        return all_relations

    async def _process_single_concept(
        self,
        concept_entity,
        concept_entities: List,
        context: ExtractionContext,
        all_relations: Dict,
    ) -> None:
        """Process relations for a single concept."""
        current_concept = concept_entity.entity

        # Load existing relations if concept exists in DB
        existing_relations = await self._load_existing_relations(current_concept)

        # Build context for relation extraction
        context_concepts = await self._build_relation_context(
            concept_entities, current_concept, context
        )

        # Extract relations for this concept
        new_relations = await self._extract_relations_for_concept(
            current_concept,
            existing_relations,
            context_concepts,
            context.journal_entry.entry_text,
        )

        # Add relations to tracking with deduplication
        self._add_relations_to_tracking(new_relations, all_relations)

    async def _load_existing_relations(self, current_concept) -> List[Dict]:
        """Load existing relations for a concept from the database."""
        if hasattr(current_concept, "existing_uuid") and current_concept.existing_uuid:
            return await self._load_existing_relations_from_db(
                current_concept.existing_uuid
            )
        else:
            return []

    def _add_relations_to_tracking(
        self, new_relations: List, all_relations: Dict
    ) -> None:
        """Add new relations to tracking with deduplication and reverse relations."""
        for relation in new_relations:
            relation_key = (relation.source_uuid, relation.target_uuid)
            if relation_key not in all_relations:
                all_relations[relation_key] = relation.type

                # Create reverse relation if needed
                reverse_type = self._get_reverse_relation_type(relation.type)
                if reverse_type:
                    reverse_key = (relation.target_uuid, relation.source_uuid)
                    if reverse_key not in all_relations:
                        all_relations[reverse_key] = reverse_type

    def _create_relation_mappings(
        self, all_relations: Dict, context: ExtractionContext
    ) -> List[CuratableMapping]:
        """Convert tracked relations to RelationSpanContextMapping objects."""
        # Validate all relations before creating Relation entities
        validated_relations = self._validate_all_relations(all_relations)

        result = []
        for (source_uuid, target_uuid), relation_type in validated_relations.items():
            concept_relation = self._create_concept_relation(
                source_uuid, target_uuid, ConceptRelationType(relation_type)
            )
            relation_spans = self._find_relation_spans(
                relation_type,
                source_uuid,
                target_uuid,
                context.journal_entry.entry_text or "",
            )

            result.append(
                CuratableMapping(
                    kind="concept_relation",
                    data=concept_relation,
                    spans=relation_spans,
                    context=None,
                )
            )

        return result

    def _create_concept_relation(
        self, source_uuid: str, target_uuid: str, relation_type: ConceptRelationType
    ) -> ConceptRelation:
        """Create a ConceptRelation entity."""
        return ConceptRelation(
            source=source_uuid,
            target=target_uuid,
            type=relation_type,
            summary_short=f"Concept relation: {relation_type}",
            summary=f"Concept relation between {source_uuid} and {target_uuid}",
        )

    def _validate_all_relations(self, all_relations: Dict) -> Dict:
        """Validate all relations for logical consistency and remove invalid ones"""
        # Import validation logic from obsidian_service
        from minerva_backend.obsidian.obsidian_service import RELATION_MAP

        validated_relations = {}
        for (source_uuid, target_uuid), relation_type in all_relations.items():
            # Check if relation type is valid
            if relation_type not in RELATION_MAP:
                self.logger.warning(f"Invalid relation type: {relation_type}")
                continue

            # Check for self-connections
            if source_uuid == target_uuid:
                self.logger.warning(
                    f"Self-connection detected: {source_uuid} -> {source_uuid}"
                )
                continue

            # Additional validation logic can be added here
            # (e.g., checking for logical conflicts like SUPPORTS + OPPOSES)

            validated_relations[(source_uuid, target_uuid)] = relation_type

        return validated_relations

    async def _load_existing_relations_from_db(self, concept_uuid: str) -> List[Dict]:
        """Load existing relations for a concept from the database"""
        # This would query the database for existing concept relations
        # Return format: [{"target_uuid": "...", "relation_type": "..."}, ...]
        # Implementation would depend on the specific database query method
        return []

    def _find_relation_spans(
        self, relation_type: str, source_uuid: str, target_uuid: str, text: str
    ) -> List:
        """Find text spans where the concept relation is mentioned"""
        # This would use the span service to find text spans
        # where the relation between concepts is mentioned
        # Implementation would depend on the specific span finding logic
        return []

    async def _build_relation_context(
        self, concept_entities, current_concept, context
    ) -> List[Dict]:
        """Build context with extracted concepts (minus current) + RAG + Recent"""
        # Get other extracted concepts (excluding current)
        other_concepts = [
            {
                "name": e.entity.name,
                "uuid": e.entity.uuid,
                "concept": e.entity.concept,
                "summary_short": e.entity.summary_short,
            }
            for e in concept_entities
            if e.entity.uuid != current_concept.uuid
        ]

        # Get RAG concepts (limit 10)
        rag_concepts = await self.concept_repository.find_relevant_concepts(
            context.journal_entry.entry_text, limit=10
        )
        rag_formatted = [
            {
                "name": c.title,
                "uuid": c.uuid,
                "concept": c.concept,
                "summary_short": c.summary_short,
            }
            for c in rag_concepts
        ]

        # Get recent concepts (limit 10)
        recent_concepts = self.concept_repository.get_concepts_with_recent_mentions(
            days=30
        )
        recent_concepts = recent_concepts[:10]
        recent_formatted = [
            {
                "name": c.title,
                "uuid": c.uuid,
                "concept": c.concept,
                "summary_short": c.summary_short,
            }
            for c in recent_concepts
        ]

        # Combine and prioritize: Extracted > RAG > Recent (max 50 total)
        all_concepts = other_concepts + rag_formatted + recent_formatted
        return all_concepts[:50]

    async def _extract_relations_for_concept(
        self, current_concept, existing_relations, context_concepts, journal_text
    ) -> List[ConceptRelation]:
        """Extract relations for a single concept using LLM"""
        # Format current concept with its relations
        current_concept_info = {
            "name": current_concept.name,
            "uuid": current_concept.uuid,
            "concept": current_concept.concept,
            "summary_short": current_concept.summary_short,
            "existing_relations": existing_relations,
        }

        # Extract relations
        prompt = ExtractConceptRelationsPrompt()
        response = await self.llm_service.generate(
            prompt=prompt.user_prompt(
                journal_text, current_concept_info, context_concepts
            ),
            system_prompt=prompt.system_prompt(),
            response_model=prompt.response_model(),
        )

        # Validate relations
        validated_relations = []
        for relation in response.relations:
            if self._validate_relation(relation):
                validated_relations.append(relation)
            else:
                self.logger.warning(f"Invalid relation rejected: {relation}")

        return validated_relations

    def _validate_relation(self, relation: ConceptRelation) -> bool:
        """Validate relation for type validity and logical consistency"""
        # Check if relation type is valid
        if relation.type not in ConceptRelationType:
            return False

        # Check for self-connections
        if relation.source == relation.target:
            return False

        # Additional validation logic can be added here
        # (e.g., checking for logical conflicts like SUPPORTS + OPPOSES)

        return True

    def _get_reverse_relation_type(self, relation_type: str) -> Optional[str]:
        """Get reverse relation type for bidirectional relations"""
        # Import RELATION_MAP from obsidian_service.py to avoid duplication
        from minerva_backend.obsidian.obsidian_service import RELATION_MAP

        if relation_type in RELATION_MAP:
            _, reverse_type = RELATION_MAP[relation_type]
            return reverse_type
        return None
