from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class Person(BaseModel):
    """A person extracted from a text."""
    name: str = Field(..., description="Name of person")
    spans: List[str] = Field(..., description="Exact text fragments where the person is mentioned", min_length=1)


class People(BaseModel):
    """A list of people extracted from a text."""
    people: List[Person] = Field(..., description="List of people mentioned in the text")


class ExtractPeoplePrompt(Prompt):
    @staticmethod
    def response_model() -> Type[People]:
        return People

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todas las personas mencionadas en esta entrada del diario, incluyendo siempre al narrador (Alex Elgier).

Para cada persona, incluye:
- Su nombre
- Todos los fragmentos de texto exactos donde aparece mencionada

## REGLAS PARA FRAGMENTOS:

Para cada mención de una persona, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## CASOS ESPECIALES:

- **Narrador**: Todas las menciones en primera persona ("yo", "me", "mi", "pensé", "fui", etc.) se refieren a Alex Elgier
- **Pronombres**: Para "él", "ella", "su", etc., incluye suficiente contexto para identificar claramente a quién se refiere
- **Múltiples menciones**: Si una persona aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Referencias indirectas**: Incluye menciones como "mi hermano", "la doctora", "el jefe" si se refieren a personas específicas

## FORMATO DE SALIDA:

Para cada persona:
- **Nombre**: [Nombre de la persona]
- **Fragmentos**: [Lista de fragmentos de texto exactos]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara de la persona
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todas las personas mencionadas en esta entrada del diario, incluyendo siempre al narrador (Alex Elgier).

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Todas las menciones en primera persona ("yo", "me", "mi") se refieren a Alex Elgier
- Incluye referencias indirectas como "mi hermano", "la doctora" si se refieren a personas específicas

**FORMATO REQUERIDO:**
- Nombre de la persona
- Lista de todos los fragmentos de texto exactos donde aparece

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
