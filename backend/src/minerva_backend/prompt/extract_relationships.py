from typing import List, Optional, Type

from pydantic import BaseModel, Field

from minerva_models import Relation
from minerva_backend.prompt.base import Prompt


class RelationshipContext(BaseModel):
    """Una entidad relacionada de alguna manera con la relación"""

    entity_uuid: str = Field(..., description="El UUID de la entidad")
    sub_type: List[str] = Field(
        ..., description="Propuestas de subtipo para la relación", min_length=1
    )

    def __hash__(self):
        return hash(self.entity_uuid + "".join(self.sub_type))


class Relationship(Relation):
    """Una relación entre dos entidades encontrada en el texto."""

    spans: List[str] = Field(
        ...,
        description="Exact text fragments where the relationship is mentioned",
        min_length=1,
    )
    context: Optional[List[RelationshipContext]] = Field(
        default=None,
        description="Entidades relacionadas de alguna " "manera con la relación",
    )


class Relationships(BaseModel):
    """Una lista de relaciones encontradas en el texto."""

    relationships: List[Relationship] = Field(
        ..., description="Una lista de relaciones"
    )


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
- Un resumen detallado de la relación (máximo 100 palabras)
- Fragmentos de texto exactos que respalden la relación
- OPCIONAL: Entidades de contexto que estén relacionadas de alguna manera con la relación principal

## REGLAS PARA FRAGMENTOS:

Para cada relación, extrae:
- La oración completa donde aparece la relación
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la relación
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## CASOS ESPECIALES:

- **Narrador**: Todas las menciones en primera persona ("yo", "me", "mi", "pensé", "fui", etc.) se refieren a Alex Elgier
- **Pronombres**: Para "él", "ella", "su", etc., incluye suficiente contexto para identificar claramente a quién se refiere
- **Múltiples menciones**: Si una relación aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas

ENTIDADES DE CONTEXTO (opcional):
Incluye entidades que proporcionen contexto adicional a la relación principal, como:
- Lugares donde ocurre la interacción
- Personas presentes durante la relación
- Objetos o conceptos que influyen en la relación
- Circunstancias temporales relevantes

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara de la relación
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original."""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todas las relaciones entre las entidades de la lista, basándote en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada relación, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Todas las menciones en primera persona ("yo", "me", "mi") se refieren a Alex Elgier
- Concéntrate ÚNICAMENTE en relaciones explícitamente mencionadas, no infieras

**FORMATO REQUERIDO:**
- UUID de entidad origen y destino
- Subtipo(s) de la relación
- Resumen breve y detallado
- Lista de fragmentos de texto exactos donde aparece la relación
- Contexto opcional (entidades relacionadas)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>

<ENTITY_LIST>
{context['entities']}
</ENTITY_LIST>"""
