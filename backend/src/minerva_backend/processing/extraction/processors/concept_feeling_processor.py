from typing import Any, Dict, List

from minerva_models import FeelingConcept
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import EntityMapping
from minerva_backend.prompt.extract_concept_feelings import (
    ConceptFeelings,
    ExtractConceptFeelingsPrompt,
)


class ConceptFeelingProcessor(BaseEntityProcessor):
    """Procesador especializado para sentimientos sobre conceptos."""

    @property
    def entity_type(self) -> str:
        return "FeelingConcept"

    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Procesa sentimientos sobre conceptos de la entrada del diario."""

        # Get people and concepts from context
        people_context = context.get_people_context_string()
        concepts_context = context.get_concepts_context_string()

        if not people_context:
            print(
                "No hay contexto de personas disponible para procesar sentimientos sobre conceptos"
            )
            return []

        if not concepts_context:
            print(
                "No hay contexto de conceptos disponible para procesar sentimientos sobre conceptos"
            )
            return []

        journal_entry = context.journal_entry

        # Convert people context string to list of dictionaries
        people_list: list[dict[str, str]] = []
        if people_context:
            # Parse the people context string format: "- Name uuid:'uuid'"
            for line in people_context.strip().split("\n"):
                if line.startswith("- "):
                    # Extract name and uuid from format: "- Name uuid:'uuid'"
                    parts = line[2:].split(" uuid:'")
                    if len(parts) == 2:
                        name = parts[0]
                        uuid = parts[1].rstrip("'")
                        people_list.append({"name": name, "uuid": uuid})

        # Generate context for the prompt
        context_dict: dict[str, str | list[dict[str, str]]] = {
            "text": journal_entry.entry_text or "",
            "people": people_list,
            "concepts": concepts_context or [],
        }

        # Generate prompt
        prompt = ExtractConceptFeelingsPrompt()
        system_prompt = prompt.system_prompt()
        user_prompt = prompt.user_prompt(
            text=context_dict["text"],  # type: ignore[arg-type]
            people=context_dict["people"],  # type: ignore[arg-type]
            concepts=context_dict["concepts"],  # type: ignore[arg-type]
        )

        # Call LLM
        try:
            response = await self.llm_service.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_model=ConceptFeelings,
            )

            # Process response
            processed_entities = []
            for concept_feeling in response.concept_feelings:
                # Create FeelingConcept entity
                feeling = FeelingConcept(
                    name=f"Sentimiento sobre concepto",
                    timestamp=concept_feeling.timestamp,
                    intensity=concept_feeling.intensity,
                    duration=concept_feeling.duration,
                    concept_uuid=concept_feeling.concept_uuid,
                    person_uuid=concept_feeling.person_uuid,
                    summary_short=concept_feeling.summary_short,
                    summary=concept_feeling.summary,
                )

                # Add to processed entities for span processing
                processed_entities.append(
                    {
                        "entity": feeling,
                        "spans": concept_feeling.spans,
                    }
                )

            # Process spans using span service
            entities = self.span_service.process_spans(
                processed_entities, context.journal_entry
            )

            print(
                f"ConceptFeelingProcessor: Extraídos {len(entities)} sentimientos sobre conceptos"
            )
            return entities

        except Exception as e:
            print(f"Error en ConceptFeelingProcessor: {e}")
            return []
