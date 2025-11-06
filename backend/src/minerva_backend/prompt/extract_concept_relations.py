from typing import List, Type

from pydantic import BaseModel, Field

from minerva_models import ConceptRelationType
from minerva_backend.prompt.base import Prompt


class ConceptRelation(BaseModel):
    type: ConceptRelationType = Field(..., description="Type of relation")
    source_uuid: str = Field(..., description="UUID of the source concept")
    target_uuid: str = Field(..., description="UUID of the target concept")


class ConceptRelations(BaseModel):
    relations: List[ConceptRelation] = Field(
        ..., description="List of concept relations"
    )


class ExtractConceptRelationsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[ConceptRelations]:
        return ConceptRelations

    @staticmethod
    def system_prompt() -> str:
        return """Extrae relaciones para un concepto específico basándote en el texto del diario y el contexto de conceptos relacionados.

INSTRUCCIONES:
1. Analiza el concepto actual y encuentra sus relaciones con otros conceptos
2. Usa ÚNICAMENTE los tipos de relación definidos en ConceptRelationType
3. Puedes inferir relaciones implícitas si están claramente sugeridas en el texto
4. Considera tanto el texto del diario como el contexto de conceptos relacionados
5. No inventes relaciones que no estén justificadas por el contenido

TIPOS DE RELACIÓN DISPONIBLES:
- GENERALIZES: A generaliza B (A es más general que B)
- SPECIFIC_OF: A es específico de B (A es más específico que B)
- PART_OF: A es parte de B
- HAS_PART: A tiene parte B
- SUPPORTS: A apoya B
- SUPPORTED_BY: A es apoyado por B
- OPPOSES: A se opone a B (simétrico)
- SIMILAR_TO: A es similar a B (simétrico)
- RELATES_TO: A se relaciona con B (simétrico)

FORMATO DE RESPUESTA:
- type: Tipo de relación de la lista anterior
- source_uuid: UUID del concepto origen (siempre el concepto actual)
- target_uuid: UUID del concepto objetivo

IMPORTANTE:
- source_uuid debe ser siempre el UUID del concepto actual
- Usa los UUIDs de los conceptos proporcionados en el contexto
- Solo sugiere relaciones que estén justificadas por el contenido"""

    @staticmethod
    def user_prompt(
        journal_text: str, current_concept: dict, context_concepts: List[dict]
    ) -> str:
        # Format current concept
        current_info = f"""
CONCEPTO ACTUAL:
- Nombre: {current_concept['name']} (UUID: {current_concept['uuid']})
- Concepto: {current_concept['concept']}
- Resumen: {current_concept['summary_short']}
- Relaciones existentes: {current_concept.get('existing_relations', [])}
"""

        # Format context concepts
        context_str = "\n".join(
            [
                f"- {c['name']} (UUID: {c['uuid']})\n  Concepto: {c['concept']}\n  Resumen: {c['summary_short']}"
                for c in context_concepts
            ]
        )

        return f"""Analiza el siguiente texto del diario y encuentra relaciones para el concepto actual:

TEXTO DEL DIARIO:
{journal_text}

{current_info}

CONCEPTOS EN CONTEXTO:
{context_str}

Encuentra relaciones entre el concepto actual y los conceptos en contexto basándote en el texto del diario."""
