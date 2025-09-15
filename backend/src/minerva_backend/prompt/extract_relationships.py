from typing import Type, List

from pydantic import BaseModel, Field, conlist

from minerva_backend.prompt.base import Prompt


class SimpleRelationship(BaseModel):
    """Una relación simple entre dos entidades."""
    source_entity_uuid: str = Field(..., description="El UUID de la entidad origen")
    target_entity_uuid: str = Field(..., description="El UUID de la entidad destino")
    sub_type: conlist(str, min_length=1) = Field(..., description="Propuestas de subtipo para la relación")
    summary_short: str = Field(..., description="Resumen breve de la relación. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen detallado de la relación. Máximo 300 palabras")


class Relationships(BaseModel):
    """Una lista de relaciones encontradas en el texto."""
    relationships: List[SimpleRelationship] = Field(..., description="Una lista de relaciones")


class ExtractRelationshipsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Relationships]:
        return Relationships

    @staticmethod
    def system_prompt() -> str:
        return """Eres un experto en la extracción de grafos de conocimiento.
Tu tarea es identificar relaciones entre una lista dada de entidades, basándote en una entrada de diario.
Ten en cuenta que el narrador de la entrada de diario es la persona Alex Elgier (incluida en la lista de entidades).
Todas las menciones en primera persona ("yo", "me", "mi", "pensé", etc.) deben interpretarse como referencias a la entidad Alex Elgier.
Concéntrate ÚNICAMENTE en las relaciones mencionadas explícitamente en el texto. No infieras relaciones.
La relación debe ser entre dos entidades de la lista proporcionada.

Para cada relación extrae:
- El UUID de la entidad origen
- El UUID de la entidad destino
- Al menos una propuesta de subtipo para la relación
- Un resumen breve de la relación (máximo 30 palabras)
- Un resumen detallado de la relación (máximo 300 palabras)"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
<ENTITY_LIST>
{context['entities']}
</ENTITY_LIST>
Con base en la entrada del diario, identifica todas las relaciones entre las entidades de la lista.
"""
