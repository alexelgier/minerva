from datetime import datetime
from typing import List, Type

from pydantic import BaseModel, Field

from minerva_models import ProjectStatus
from minerva_backend.prompt.base import Prompt


class Project(BaseModel):
    """A project extracted from a text."""

    name: str = Field(..., description="Name of project")
    spans: List[str] = Field(
        ...,
        description="Exact text fragments where the project is mentioned",
        min_length=1,
    )
    status: ProjectStatus | None = Field(
        default=None, description="Estado actual del proyecto"
    )
    start_date: datetime | None = Field(
        default=None, description="Fecha de inicio del proyecto"
    )
    target_completion: datetime | None = Field(
        default=None, description="Fecha de finalización objetivo o esperada"
    )
    progress: float | None = Field(
        default=None,
        description="Porcentaje de finalización (0.0 a 100.0)",
        ge=0.0,
        le=100.0,
    )
    summary_short: str = Field(
        ..., description="Resumen del proyecto. Máximo 30 palabras"
    )
    summary: str = Field(..., description="Resumen del proyecto. Máximo 100 palabras")


class Projects(BaseModel):
    """A list of projects extracted from a text."""

    projects: List[Project] = Field(
        ..., description="List of projects mentioned in the text"
    )


class ExtractProjectsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Projects]:
        return Projects

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los proyectos mencionados en esta entrada del diario.

Para cada proyecto, incluye:
- Su nombre (título o descripción breve del proyecto)
- Todos los fragmentos de texto exactos donde aparece mencionado
- Estado del proyecto si se especifica (planificado, en progreso, completado, pausado, cancelado)
- Fecha de inicio si se menciona
- Fecha objetivo de finalización si se menciona
- Porcentaje de progreso si se especifica (0.0 a 100.0)
- Resumen corto del proyecto (máximo 30 palabras)
- Resumen detallado del proyecto (máximo 100 palabras)

## REGLAS PARA FRAGMENTOS:

Para cada mención de un proyecto, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## IDENTIFICACIÓN DE PROYECTOS:

Considera como proyectos:
- Trabajos creativos, técnicos o sociales con objetivos específicos
- Actividades que requieren planificación y seguimiento
- Iniciativas con fechas límite o metas definidas
- Referencias a "el proyecto", "mi trabajo", "la iniciativa", etc.
- Cualquier actividad que implique múltiples pasos hacia un objetivo

## CASOS ESPECIALES:

- **Referencias indirectas**: Incluye menciones como "el trabajo", "la iniciativa", "mi proyecto" si se refieren a proyectos específicos
- **Múltiples menciones**: Si un proyecto aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Proyectos sin nombre específico**: Usa una descripción breve basada en el contexto

## FORMATO DE SALIDA:

Para cada proyecto:
- **Nombre**: [Nombre o descripción breve del proyecto]
- **Fragmentos**: [Lista de fragmentos de texto exactos]
- **Estado**: [Estado actual si se menciona]
- **Fecha inicio**: [Fecha de inicio si se menciona]
- **Fecha objetivo**: [Fecha de finalización esperada si se menciona]
- **Progreso**: [Porcentaje si se especifica]
- **Resumen corto**: [Máximo 30 palabras]
- **Resumen**: [Máximo 100 palabras]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara del proyecto
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los proyectos mencionados en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Identifica proyectos de cualquier tipo: creativos, técnicos, sociales, o colaborativos
- Incluye referencias indirectas como "el trabajo", "la iniciativa", "mi proyecto" si se refieren a actividades específicas
- Extrae información sobre estado, fechas, progreso y crea resúmenes cuando sea posible

**FORMATO REQUERIDO:**
- Nombre del proyecto (o descripción breve si no tiene nombre específico)
- Lista de todos los fragmentos de texto exactos donde aparece
- Estado del proyecto (si se menciona)
- Fecha de inicio (si se menciona)
- Fecha objetivo de finalización (si se menciona)
- Porcentaje de progreso (si se especifica, entre 0.0 y 100.0)
- Resumen corto (máximo 30 palabras)
- Resumen detallado (máximo 100 palabras)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
