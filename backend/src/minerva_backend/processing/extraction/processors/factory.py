from typing import Any, Dict, List

from minerva_models import Consumable, Content, Event, Place, Project
from minerva_backend.processing.extraction.processors.base import (
    EntityProcessorStrategy,
)
from minerva_backend.processing.extraction.processors.concept_feeling_processor import (
    ConceptFeelingProcessor,
)
from minerva_backend.processing.extraction.processors.concept_processor import (
    ConceptProcessor,
)
from minerva_backend.processing.extraction.processors.emotion_feeling_processor import (
    EmotionFeelingProcessor,
)
from minerva_backend.processing.extraction.processors.generic_entity_processor import (
    GenericEntityProcessor,
)
from minerva_backend.processing.extraction.processors.people_processor import (
    PeopleProcessor,
)
from minerva_backend.prompt.extract_consumables import (
    Consumables,
    ExtractConsumablesPrompt,
)
from minerva_backend.prompt.extract_content import Contents, ExtractContentPrompt
from minerva_backend.prompt.extract_events import Events, ExtractEventsPrompt
from minerva_backend.prompt.extract_places import ExtractPlacesPrompt, Places

# Imports para prompts
from minerva_backend.prompt.extract_projects import ExtractProjectsPrompt, Projects


class ProcessorFactory:
    """Factory para crear procesadores de entidades."""

    @staticmethod
    def create_all_processors(
        llm_service, entity_repositories: Dict[str, Any], span_service, obsidian_service
    ) -> List[EntityProcessorStrategy]:
        """Crea todos los procesadores de entidades."""

        processors: List[EntityProcessorStrategy] = [
            # Procesador especializado para personas
            PeopleProcessor(
                llm_service, entity_repositories, span_service, obsidian_service
            ),
            # Procesador especializado para conceptos
            ConceptProcessor(
                llm_service, entity_repositories, span_service, obsidian_service
            ),
            # Procesador especializado para emociones
            EmotionFeelingProcessor(
                llm_service, entity_repositories, span_service, obsidian_service
            ),
            # Procesador especializado para sentimientos sobre conceptos
            ConceptFeelingProcessor(
                llm_service, entity_repositories, span_service, obsidian_service
            ),
            # Procesadores genéricos para otras entidades
            GenericEntityProcessor(
                entity_type="Project",
                prompt_class=ExtractProjectsPrompt,
                response_wrapper_class=Projects,
                entity_class=Project,
                entity_field_name="projects",
                llm_service=llm_service,
                entity_repositories=entity_repositories,
                span_service=span_service,
                obsidian_service=obsidian_service,
            ),
            GenericEntityProcessor(
                entity_type="Consumable",
                prompt_class=ExtractConsumablesPrompt,
                response_wrapper_class=Consumables,
                entity_class=Consumable,
                entity_field_name="consumables",
                llm_service=llm_service,
                entity_repositories=entity_repositories,
                span_service=span_service,
                obsidian_service=obsidian_service,
            ),
            GenericEntityProcessor(
                entity_type="Content",
                prompt_class=ExtractContentPrompt,
                response_wrapper_class=Contents,
                entity_class=Content,
                entity_field_name="contents",
                llm_service=llm_service,
                entity_repositories=entity_repositories,
                span_service=span_service,
                obsidian_service=obsidian_service,
            ),
            GenericEntityProcessor(
                entity_type="Event",
                prompt_class=ExtractEventsPrompt,
                response_wrapper_class=Events,
                entity_class=Event,
                entity_field_name="events",
                llm_service=llm_service,
                entity_repositories=entity_repositories,
                span_service=span_service,
                obsidian_service=obsidian_service,
            ),
            GenericEntityProcessor(
                entity_type="Place",
                prompt_class=ExtractPlacesPrompt,
                response_wrapper_class=Places,
                entity_class=Place,
                entity_field_name="places",
                llm_service=llm_service,
                entity_repositories=entity_repositories,
                span_service=span_service,
                obsidian_service=obsidian_service,
            ),
        ]

        return processors
