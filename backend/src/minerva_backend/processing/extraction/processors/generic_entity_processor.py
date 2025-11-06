from typing import Any, Callable, List, Type

from minerva_models import Entity
from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.extraction.processors.base import BaseEntityProcessor
from minerva_backend.processing.models import EntityMapping
from minerva_backend.utils.logging import get_logger


class GenericEntityProcessor(BaseEntityProcessor):
    """Procesador genérico para entidades que siguen el patrón estándar."""

    def __init__(
        self,
        entity_type: str,
        prompt_class: Type,
        response_wrapper_class: Type,
        entity_class: Type,
        entity_field_name: str,
        llm_service,
        entity_repositories: dict,
        span_service,
        obsidian_service,
    ):
        super().__init__(
            llm_service, entity_repositories, span_service, obsidian_service
        )
        self._entity_type = entity_type
        self.prompt_class = prompt_class
        self.response_wrapper_class = response_wrapper_class
        self.entity_class = entity_class
        self.entity_field_name = entity_field_name
        self.logger = get_logger(
            f"minerva_backend.processing.extraction.{entity_type.lower()}_processor"
        )

    @property
    def entity_type(self) -> str:
        return self._entity_type

    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Procesa entidades genéricas de la entrada del diario."""

        self.logger.info(
            f"Starting {self.entity_type.lower()} extraction",
            context={
                "journal_id": context.journal_entry.uuid,
                "entry_length": len(context.journal_entry.entry_text or ""),
            },
        )

        result = await self._process_entity_type(
            context=context,
            prompt_class=self.prompt_class,
            response_wrapper_class=self.response_wrapper_class,
            entity_class=self.entity_class,
            entity_field_name=self.entity_field_name,
        )

        # Log extraction results
        entity_names = [entity.entity.name for entity in result]
        self.logger.info(
            f"{self.entity_type} extraction completed: {len(result)} entities extracted",
            context={
                "journal_id": context.journal_entry.uuid,
                "entity_count": len(result),
                "entity_names": entity_names,
            },
        )

        return result

    async def _process_entity_type(
        self,
        context: ExtractionContext,
        prompt_class: Any,
        response_wrapper_class: Any,
        entity_class: Any,
        entity_field_name: str,
        hydration_func: Callable = None,
        custom_context: str = None,
    ) -> List[EntityMapping]:
        """Procesamiento genérico de entidades que maneja extracción LLM, creación de entidades, deduplicación y procesamiento de spans."""

        journal_entry = context.journal_entry
        obsidian_entities = context.obsidian_entities

        context_dict = {"text": journal_entry.entry_text}
        if custom_context:
            context_dict["custom_context"] = custom_context

        result = await self.llm_service.generate(
            prompt=prompt_class.user_prompt(context_dict),
            system_prompt=prompt_class.system_prompt(),
            response_model=prompt_class.response_model(),
        )

        if not result:
            raise Exception(f"LLM no retornó datos de {self.entity_type.lower()}.")

        llm_response = result

        entity_objects: List[Entity] = []
        spans_mapping: dict[str, List] = {}  # Mapeo de nombre de entidad -> spans

        for llm_entity in getattr(llm_response, entity_field_name):
            # Preservar los spans del objeto LLM original
            spans = getattr(llm_entity, "spans", [])
            spans_mapping[llm_entity.name] = spans

            # Si hay hidratación, no construimos aún la entidad del dominio
            # (evitamos errores de validación por campos requeridos ausentes, p.ej. summary)
            if hydration_func is not None:
                # Pasamos el objeto LLM tal cual; aguas abajo se hidrata y valida
                entity_objects.append(llm_entity)
            else:
                entity_kwargs = llm_entity.model_dump()
                entity_obj = entity_class(**entity_kwargs)
                entity_objects.append(entity_obj)

        processed_entities = await self._process_and_deduplicate_entities(
            entity_objects,
            obsidian_entities,
            journal_entry,
            self.entity_type,
            hydration_func,
        )

        # Convertir a la estructura esperada por _process_spans
        entities_with_spans = []
        for item in processed_entities:
            # Obtener spans del mapeo usando el nombre canónico de la entidad
            spans = spans_mapping.get(item["canonical_name"], [])
            entities_with_spans.append({"entity": item["entity"], "spans": spans})

        return self.span_service.process_spans(entities_with_spans, journal_entry)
