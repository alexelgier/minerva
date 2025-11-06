from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from minerva_backend.processing.extraction.context import ExtractionContext
from minerva_backend.processing.models import EntityMapping


class EntityProcessorStrategy(ABC):
    """Interfaz base para procesadores de entidades."""

    @abstractmethod
    async def process(self, context: ExtractionContext) -> List[EntityMapping]:
        """Procesa entidades del tipo específico y retorna las entidades extraídas."""
        pass

    @property
    @abstractmethod
    def entity_type(self) -> str:
        """Retorna el tipo de entidad que procesa este strategy."""
        pass


class BaseEntityProcessor(EntityProcessorStrategy):
    """Procesador base que implementa funcionalidad común para procesamiento de entidades."""

    def __init__(
        self,
        llm_service,
        entity_repositories: Dict[str, Any],
        span_service,
        obsidian_service,
    ):
        self.llm_service = llm_service
        self.entity_repositories = entity_repositories
        self.span_service = span_service
        self.obsidian_service = obsidian_service

    async def _process_and_deduplicate_entities(
        self,
        llm_entities: List[Any],
        obsidian_entities: Dict[str, Dict],
        journal_entry,
        entity_type: str,
        hydration_func: Callable = None,
    ) -> List[Dict]:
        """Procesamiento genérico de entidades y deduplicación, preservando IDs de entidades existentes."""

        name_lookup = obsidian_entities["name_lookup"]
        processed_entities: List[Dict] = []
        seen_canonical_names = set()

        for llm_entity in llm_entities:
            entity_name = llm_entity.name

            # Determinar si esta entidad existe en Obsidian/DB
            # CRITICAL FIX: Only look up entities of the same type to prevent cross-pollination
            existing_entity_data = name_lookup.get(entity_name)

            # Filter by entity type to prevent cross-pollination
            if existing_entity_data and existing_entity_data.entity_type != entity_type:
                # Log potential cross-pollination detection
                print(
                    f"⚠️  CROSS-POLLINATION PREVENTED: Entity '{entity_name}' exists as {existing_entity_data.entity_type} but being processed as {entity_type}"
                )
                existing_entity_data = None

            if existing_entity_data:
                # Usar nombre canónico de Obsidian
                canonical_name = existing_entity_data.entity_long_name
            else:
                # Usar nombre extraído por LLM como canónico
                canonical_name = entity_name

            if canonical_name in seen_canonical_names:
                continue
            seen_canonical_names.add(canonical_name)

            # Crear o hidratar la entidad
            if hydration_func:
                hydrated_entity = await hydration_func(journal_entry, canonical_name)
                if not hydrated_entity:
                    continue
            else:
                # Convert LLM entity to domain entity
                entity_kwargs = llm_entity.model_dump()
                entity_kwargs["name"] = canonical_name
                # Get the entity class from the processor
                try:
                    entity_class = self.entity_repositories[entity_type].entity_class
                    hydrated_entity = entity_class(**entity_kwargs)
                except (KeyError, AttributeError) as e:
                    raise RuntimeError(
                        f"Failed to create domain entity for {entity_type}: {e}. Entity class lookup failed or entity creation failed. This indicates a configuration error."
                    )

            # Si la entidad existe en DB, preservar ID y fusionar propiedades
            if existing_entity_data and existing_entity_data.entity_id:
                hydrated_entity.uuid = existing_entity_data.entity_id

                existing_db_entity = self.entity_repositories[entity_type].find_by_uuid(
                    existing_entity_data.entity_id
                )
                if existing_db_entity:
                    hydrated_entity = await self._merge_entity_properties(
                        existing_entity=existing_db_entity, new_entity=hydrated_entity
                    )

            processed_entities.append(
                {
                    "entity": hydrated_entity,
                    "canonical_name": canonical_name,
                    "had_existing_id": bool(
                        existing_entity_data and existing_entity_data.entity_id
                    ),
                }
            )

        # Log deduplication results
        print(
            f"📊 {entity_type} deduplication: {len(llm_entities)} LLM entities → {len(processed_entities)} processed entities"
        )

        return processed_entities

    async def _merge_entity_properties(self, existing_entity, new_entity):
        """Fusiona propiedades de extracción LLM con datos de entidad existente."""
        from minerva_backend.prompt.merge_summaries import MergeSummariesPrompt

        merged_summaries = await self.llm_service.generate(
            prompt=MergeSummariesPrompt.user_prompt(
                {
                    "existing_summary": existing_entity.summary or "",
                    "existing_short_summary": existing_entity.summary_short or "",
                    "new_summary": new_entity.summary or "",
                    "new_short_summary": new_entity.summary_short or "",
                    "entity_name": existing_entity.name,
                }
            ),
            system_prompt=MergeSummariesPrompt.system_prompt(),
            response_model=MergeSummariesPrompt.response_model(),
        )

        new_entity.summary = merged_summaries.summary
        new_entity.summary_short = merged_summaries.summary_short
        return new_entity
