from typing import Any, Dict, List

from minerva_models import FeelingEmotion
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import EntityMapping
from minerva_backend.prompt.extract_emotions import ExtractEmotionsPrompt, Feelings


class EmotionFeelingProcessor(BaseEntityProcessor):
    """Procesador especializado para emociones/sentimientos."""

    @property
    def entity_type(self) -> str:
        return "FeelingEmotion"

    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Procesa emociones de la entrada del diario."""

        # Las emociones requieren contexto de personas
        people_context = context.get_people_context_string()
        if not people_context:
            print("No hay contexto de personas disponible para procesar emociones")
            return []

        journal_entry = context.journal_entry

        # Generar contexto para el prompt
        context_dict = {
            "text": journal_entry.entry_text or "",
            "people": people_context,
        }

        result = await self.llm_service.generate(
            prompt=ExtractEmotionsPrompt.user_prompt(context_dict),
            system_prompt=ExtractEmotionsPrompt.system_prompt(),
            response_model=ExtractEmotionsPrompt.response_model(),
        )

        if not result:
            raise Exception("LLM no retornó datos de sentimientos.")

        llm_extracted_feelings = result

        # Crear diccionario de personas para mapear UUIDs a nombres
        people_dict = {}
        for entity_mapping in context.extracted_entities or []:
            if entity_mapping.entity.type == "Person":
                people_dict[str(entity_mapping.entity.uuid)] = (
                    entity_mapping.entity.name
                )

        feelings: List[Dict[str, Any]] = []
        for feeling in llm_extracted_feelings.feelings:
            feelings.append(
                {
                    "entity": FeelingEmotion(
                        name=f"{people_dict[feeling.person_uuid]} siente {feeling.emotion}",
                        timestamp=feeling.timestamp,
                        intensity=feeling.intensity,
                        duration=feeling.duration,
                        emotion=feeling.emotion,
                        person_uuid=feeling.person_uuid,
                        summary=feeling.summary,
                        summary_short=feeling.summary_short,
                    ),
                    "spans": feeling.spans,
                }
            )

        return self.span_service.process_spans(feelings, journal_entry)
