from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class Consumable(BaseModel):
    """A consumable extracted from a text."""

    name: str = Field(..., description="Name of consumable")
    spans: List[str] = Field(
        ...,
        description="Exact text fragments where the consumable is mentioned",
        min_length=1,
    )
    category: str | None = Field(
        default=None,
        description="Categoría del consumible (p. ej., comida, bebida, " "medicamento)",
    )
    summary_short: str = Field(
        ..., description="Resumen del consumible. Máximo 30 palabras"
    )
    summary: str = Field(..., description="Resumen del consumible. Máximo 100 palabras")


class Consumables(BaseModel):
    """A list of consumables extracted from a text."""

    consumables: List[Consumable] = Field(
        ..., description="List of consumables mentioned in the text"
    )


class ExtractConsumablesPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Consumables]:
        return Consumables

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los consumibles mencionados en esta entrada del diario.

Para cada consumible, incluye:
- Su nombre (nombre específico del producto o descripción del consumible)
- Todos los fragmentos de texto exactos donde aparece mencionado
- Categoría del consumible (comida, bebida, medicamento, suplemento, alcohol, etc.)
- Resumen corto del consumible (máximo 30 palabras)
- Resumen detallado del consumible (máximo 100 palabras)

## REGLAS PARA FRAGMENTOS:

Para cada mención de un consumible, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## IDENTIFICACIÓN DE CONSUMIBLES:

Considera como consumibles:
- Alimentos y bebidas (comidas, snacks, café, agua, alcohol, etc.)
- Medicamentos y suplementos (vitaminas, pastillas, remedios, etc.)
- Sustancias consumidas por vía oral, inhalada o aplicada
- Productos de consumo personal que se ingieren o aplican al cuerpo
- Referencias a "la pastilla", "mi medicamento", "el café", "el alcohol", etc.

## CATEGORÍAS PRINCIPALES:

- **Comida**: Alimentos sólidos, snacks, comidas principales
- **Bebida**: Líquidos, bebidas alcohólicas y no alcohólicas
- **Medicamento**: Fármacos recetados, medicamentos de venta libre
- **Suplemento**: Vitaminas, minerales, suplementos nutricionales
- **Drogas**: Sustancias psicoactivas, drogas recreativas o medicinales
- **Otro**: Cualquier otro tipo de consumible

## CASOS ESPECIALES:

- **Referencias indirectas**: Incluye menciones como "la pastilla", "mi medicamento", "el desayuno" si se refieren a consumibles específicos
- **Múltiples menciones**: Si un consumible aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Consumibles sin nombre específico**: Usa una descripción breve basada en el contexto

## FORMATO DE SALIDA:

Para cada consumible:
- **Nombre**: [Nombre específico o descripción del consumible]
- **Fragmentos**: [Lista de fragmentos de texto exactos]
- **Categoría**: [Categoría del consumible]
- **Resumen corto**: [Máximo 30 palabras]
- **Resumen**: [Máximo 100 palabras]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara del consumible
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los consumibles mencionados en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Identifica consumibles de cualquier tipo: alimentos, bebidas, medicamentos, suplementos, etc.
- Incluye referencias indirectas como "la pastilla", "mi medicamento", "el café" si se refieren a consumibles específicos
- Categoriza cada consumible apropiadamente y crea resúmenes descriptivos

**CATEGORÍAS DISPONIBLES:**
- Comida: Alimentos sólidos, snacks, comidas
- Bebida: Líquidos, bebidas (incluye alcohol como subcategoría)
- Medicamento: Fármacos, medicinas
- Suplemento: Vitaminas, minerales, suplementos nutricionales
- Drogas: Sustancias psicoactivas, drogas recreativas, alcohol, cannabis, etc.
- Otro: Otros tipos de consumibles

**FORMATO REQUERIDO:**
- Nombre del consumible (o descripción breve si no tiene nombre específico)
- Lista de todos los fragmentos de texto exactos donde aparece
- Categoría del consumible
- Resumen corto (máximo 30 palabras)
- Resumen detallado (máximo 100 palabras)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
