from datetime import datetime
from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class Place(BaseModel):
    """Un lugar extraído de un texto."""

    name: str = Field(..., description="Nombre del lugar")
    spans: List[str] = Field(
        ...,
        description="Fragmentos de texto exactos donde se menciona el lugar",
        min_length=1,
    )
    summary_short: str = Field(..., description="Resumen del lugar. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen del lugar. Máximo 100 palabras")
    address: str | None = Field(
        default=None, description="Dirección o descripción de la ubicación"
    )
    category: str | None = Field(
        default=None,
        description="Categoría del lugar (p. ej., casa, parque, restaurante)",
    )


class Places(BaseModel):
    """Una lista de lugares extraídos de un texto."""

    places: List[Place] = Field(
        ..., description="Lista de lugares mencionados en el texto"
    )


class ExtractPlacesPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Places]:
        return Places

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los lugares mencionados en esta entrada del diario.

Para cada lugar, incluye:
- Su nombre (nombre específico o descripción del lugar)
- Todos los fragmentos de texto exactos donde aparece mencionado
- Categoría del lugar (casa, trabajo, restaurante, parque, etc.)
- Dirección o descripción de la ubicación si se menciona
- Resumen corto del lugar (máximo 30 palabras)
- Resumen detallado del lugar (máximo 100 palabras)

## REGLAS PARA FRAGMENTOS:

Para cada mención de un lugar, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## IDENTIFICACIÓN DE LUGARES:

Considera como lugares:
- Ubicaciones físicas específicas (casa, oficina, restaurante, parque)
- Espacios de trabajo (estudio, coworking, sala de reuniones)
- Lugares de ocio (bar, cine, club, venue)
- Espacios públicos (calle, plaza, estación)
- Referencias indirectas como "la casa", "el lugar", "ahí"
- Direcciones, barrios, ciudades

## CATEGORÍAS PRINCIPALES:

- **Hogar**: Casa, departamento, habitaciones
- **Trabajo**: Oficinas, estudios, coworking
- **Comercial**: Restaurantes, tiendas, bares
- **Público**: Parques, calles, estaciones
- **Cultural**: Teatros, museos, venues
- **Otro**: Otros lugares

## CASOS ESPECIALES:

- **Referencias indirectas**: Incluye menciones como "la casa", "el lugar", "ahí" si se refieren a lugares específicos
- **Múltiples menciones**: Si un lugar aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Lugares sin nombre específico**: Usa una descripción breve basada en el contexto
- **Lugares temporales**: Incluye lugares mencionados aunque la visita sea pasada o futura

## FORMATO DE SALIDA:

Para cada lugar:
- **Nombre**: [Nombre específico o descripción del lugar]
- **Fragmentos**: [Lista de fragmentos de texto exactos]
- **Categoría**: [Categoría del lugar]
- **Dirección**: [Dirección o ubicación si se menciona]
- **Resumen corto**: [Máximo 30 palabras]
- **Resumen**: [Máximo 100 palabras]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara del lugar
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los lugares mencionados en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Identifica lugares de cualquier tipo: casas, oficinas, restaurantes, parques, estudios, etc.
- Incluye referencias indirectas como "la casa", "el lugar", "ahí" si se refieren a ubicaciones específicas
- Extrae información sobre categoría, dirección y contexto cuando sea posible

**CATEGORÍAS DISPONIBLES:**
- Hogar: Casa, departamento, habitaciones
- Trabajo: Oficinas, estudios, coworking, espacios de trabajo
- Comercial: Restaurantes, tiendas, bares, centros comerciales
- Público: Parques, calles, estaciones, plazas
- Cultural: Museos, teatros, venues, centros culturales
- Otro: Otros tipos de lugares

**FORMATO REQUERIDO:**
- Nombre del lugar (o descripción breve si no tiene nombre específico)
- Lista de todos los fragmentos de texto exactos donde aparece
- Categoría del lugar
- Dirección o descripción de ubicación (si se menciona)
- Resumen corto (máximo 30 palabras)
- Resumen detallado (máximo 100 palabras)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
