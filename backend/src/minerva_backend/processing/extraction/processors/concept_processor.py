from typing import Any, Dict, List

from minerva_models import Concept
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import EntityMapping
from minerva_backend.prompt.extract_concepts import Concepts, ExtractConceptsPrompt
from minerva_backend.utils.logging import get_logger


class ConceptProcessor(BaseEntityProcessor):
    """Procesador especializado para conceptos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_logger(
            "minerva_backend.processing.extraction.concept_processor"
        )

    @property
    def entity_type(self) -> str:
        return "Concept"

    @property
    def concept_repository(self):
        """Direct access to concept repository."""
        return self.entity_repositories["Concept"]

    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Procesa conceptos de la entrada del diario."""

        self.logger.info(
            "Starting concept extraction",
            context={
                "journal_id": context.journal_entry.uuid,
                "entry_length": len(context.journal_entry.entry_text or ""),
            },
        )

        journal_entry = context.journal_entry

        # Get enhanced concept context with 3 sections
        concept_context = await self._get_enhanced_concept_context(context)

        # Generate context for the prompt
        context_dict = {
            "text": journal_entry.entry_text or "",
            "context": concept_context or "",
        }

        # Generate prompt
        prompt = ExtractConceptsPrompt()
        system_prompt = prompt.system_prompt()
        user_prompt = prompt.user_prompt(
            text=context_dict["text"], context=context_dict["context"]
        )

        # Call LLM
        try:
            response = await self.llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=Concepts,
            )

            # Process response
            processed_entities = []
            for concept_mention in response.concepts:
                if concept_mention.existing_uuid:
                    # Merge with existing concept
                    existing_concept = await self._merge_with_existing_concept(
                        concept_mention, self.concept_repository
                    )
                    processed_entities.append(
                        {
                            "entity": existing_concept,
                            "spans": concept_mention.spans,
                        }
                    )
                else:
                    # Create new concept
                    concept = Concept(
                        name=concept_mention.name,
                        title=concept_mention.title,
                        concept=concept_mention.concept,
                        analysis=concept_mention.analysis,
                        source=concept_mention.source,
                        summary_short=concept_mention.summary_short,
                        summary=concept_mention.summary,
                    )
                    processed_entities.append(
                        {
                            "entity": concept,
                            "spans": concept_mention.spans,
                        }
                    )

            # Process spans using span service
            entities = self.span_service.process_spans(
                processed_entities, context.journal_entry
            )

            # Log extraction results
            concept_names = [entity.entity.name for entity in entities]
            self.logger.info(
                f"Concept extraction completed: {len(entities)} concepts extracted",
                context={
                    "journal_id": context.journal_entry.uuid,
                    "concept_count": len(entities),
                    "concept_names": concept_names,
                },
            )

            return entities

        except Exception as e:
            print(f"Error en ConceptProcessor: {e}")
            return []

    async def _get_enhanced_concept_context(self, context: ExtractionContext) -> str:
        """Get enhanced concept context with 3 sections: [[Linked]] + RAG + Recent"""
        try:
            # 1. Extract [[Linked]] concepts from ObsidianService
            linked_concepts = []
            for entity_data in context.obsidian_entities.get("db_entities", []):
                if entity_data.entity_type == "Concept":
                    concept = self.concept_repository.find_by_uuid(
                        entity_data.entity_id
                    )
                    if concept:
                        linked_concepts.append(concept)

            # 2. Get RAG concepts (limit 10)
            rag_concepts = await self.concept_repository.find_relevant_concepts(
                context.journal_entry.entry_text, limit=10
            )

            # 3. Get recent concepts (limit 10)
            recent_concepts = self.concept_repository.get_concepts_with_recent_mentions(
                days=30
            )
            recent_concepts = recent_concepts[:10]

            # Format context with 2 sections
            return self._format_context(linked_concepts, rag_concepts, recent_concepts)

        except Exception as e:
            print(f"Error getting enhanced concept context: {e}")
            return "No concept context available."

    def _format_context(self, linked_concepts, rag_concepts, recent_concepts) -> str:
        """Format context with 2 sections: [[Linked]] concepts + RAG + Recent concepts"""
        context_parts = []

        # Section 1: Explicit [[Linked]] concepts
        if linked_concepts:
            context_parts.append("CONCEPTOS EXPLÍCITAMENTE MENCIONADOS:")
            for concept in linked_concepts:
                context_parts.append(f"- {concept.title} (UUID: {concept.uuid})")
                context_parts.append(f"  Concepto: {concept.concept}")
                context_parts.append(f"  Resumen: {concept.summary_short}")
            context_parts.append("")

        # Section 2: RAG + Recent concepts (prioritized: RAG > Recent)
        all_related_concepts = rag_concepts + recent_concepts
        if all_related_concepts:
            context_parts.append("CONCEPTOS RELACIONADOS DE TU BASE DE CONOCIMIENTO:")
            for concept in all_related_concepts:
                context_parts.append(f"- {concept.title} (UUID: {concept.uuid})")
                context_parts.append(f"  Concepto: {concept.concept}")
                context_parts.append(f"  Resumen: {concept.summary_short}")

        return "\n".join(context_parts)

    async def _merge_with_existing_concept(
        self, concept_mention, concept_repository
    ) -> Concept:
        """Merge extracted concept with existing DB concept using LLM"""
        existing_concept = concept_repository.find_by_uuid(
            concept_mention.existing_uuid
        )

        # Prepare merge data for all fields
        merge_data = {
            "entity_name": concept_mention.name,
            "existing_title": existing_concept.title,
            "existing_concept": existing_concept.concept,
            "existing_analysis": existing_concept.analysis,
            "existing_source": existing_concept.source,
            "existing_summary": existing_concept.summary,
            "existing_short_summary": existing_concept.summary_short,
            "new_title": concept_mention.title,
            "new_concept": concept_mention.concept,
            "new_analysis": concept_mention.analysis,
            "new_source": concept_mention.source,
            "new_summary": concept_mention.summary,
            "new_short_summary": concept_mention.summary_short,
        }

        # Use merge prompt (will create MergeConceptPrompt in Phase 5)
        from minerva_backend.prompt.merge_concept import MergeConceptPrompt

        merge_prompt = MergeConceptPrompt()
        merged_concept = await self.llm_service.generate(
            prompt=merge_prompt.user_prompt(merge_data),
            system_prompt=merge_prompt.system_prompt(),
            response_model=merge_prompt.response_model(),
        )

        # Update existing concept
        existing_concept.title = merged_concept.title
        existing_concept.concept = merged_concept.concept
        existing_concept.analysis = merged_concept.analysis
        existing_concept.source = merged_concept.source
        existing_concept.summary = merged_concept.summary
        existing_concept.summary_short = merged_concept.summary_short

        return existing_concept
