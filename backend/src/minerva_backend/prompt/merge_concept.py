from typing import Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class MergedConcept(BaseModel):
    title: str = Field(..., description="Merged title")
    concept: str = Field(..., description="Merged concept definition")
    analysis: str = Field(..., description="Merged analysis")
    source: str | None = Field(default=None, description="Merged source")
    summary_short: str = Field(..., description="Merged short summary (max 30 words)")
    summary: str = Field(..., description="Merged detailed summary (max 100 words)")


class MergeConceptPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[MergedConcept]:
        return MergedConcept

    @staticmethod
    def system_prompt() -> str:
        return """Eres un experto en fusionar información de conceptos de manera inteligente.

Tu tarea es tomar un concepto existente y un concepto extraído de un journal, y crear un concepto fusionado que combine la información de ambos de manera coherente.

REGLAS IMPORTANTES:
- La información más reciente NO siempre es más correcta - usa tu juicio
- Si hay contradicciones, prefiere la información más específica/detallada
- No inventes información que no esté en los conceptos originales
- Si un campo está vacío o es genérico, prioriza el otro
- Combina información complementaria de ambos conceptos

LÍMITES ESTRICTOS:
- summary (resumen largo): MÁXIMO 100 palabras
- summary_short (resumen corto): MÁXIMO 30 palabras

El resumen corto debe ser la versión más condensada del resumen largo."""

    @staticmethod
    def user_prompt(data: dict) -> str:
        return f"""Fusiona la información sobre: {data['entity_name']}

CONCEPTO EXISTENTE:
Título: {data['existing_title']}
Concepto: {data['existing_concept']}
Análisis: {data['existing_analysis']}
Fuente: {data['existing_source']}
Resumen corto: {data['existing_short_summary']}
Resumen: {data['existing_summary']}

CONCEPTO EXTRAÍDO:
Título: {data['new_title']}
Concepto: {data['new_concept']}
Análisis: {data['new_analysis']}
Fuente: {data['new_source']}
Resumen corto: {data['new_short_summary']}
Resumen: {data['new_summary']}

Crea un concepto fusionado que combine lo mejor de ambos, eliminando redundancia pero preservando detalles importantes."""
