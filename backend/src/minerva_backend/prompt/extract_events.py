from datetime import datetime, timedelta
from typing import List, Type

from pydantic import BaseModel, Field, field_validator

from minerva_models import ProjectStatus
from minerva_backend.prompt.base import Prompt
from minerva_models.utils import duration_validator


class Event(BaseModel):
    """Representa un suceso o actividad notable que ocurrió en un momento específico."""

    category: str = Field(
        ..., description="Categoría del evento (reunión, entrenamiento, etc)"
    )
    date: datetime = Field(..., description="Cuándo ocurrió el evento")
    duration: timedelta | None = Field(
        default=None, description="Duración del evento (p. ej., 2 horas, 30 minutos)"
    )
    location: str | None = Field(default=None, description="Dónde tuvo lugar el evento")
    name: str = Field(..., description="Nombre del evento")
    spans: List[str] = Field(
        ...,
        description="Fragmentos de texto exactos donde se menciona el evento",
        min_length=1,
    )
    summary_short: str = Field(
        ..., description="Resumen del evento. Máximo 30 palabras"
    )
    summary: str = Field(..., description="Resumen del evento. Máximo 100 palabras")

    @field_validator("duration", mode="before")
    @classmethod
    def parse_duration(cls, v):
        """Parsea duración en formato string a timedelta."""
        return duration_validator(v)


class Events(BaseModel):
    """Una lista de eventos extraídos de un texto."""

    events: List[Event] = Field(
        ..., description="Lista de eventos mencionados en el texto"
    )


class ExtractEventsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Events]:
        return Events

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los eventos mencionados en esta entrada del diario.

Para cada evento, incluye:
- Su nombre (título o descripción breve del evento)
- Todos los fragmentos de texto exactos donde aparece mencionado
- Categoría del evento (reunión, entrenamiento, cita, celebración, trabajo, etc.)
- Fecha y hora cuando ocurrió el evento
- Duración del evento si se menciona (p. ej., 2 horas, 30 minutos)
- Ubicación donde tuvo lugar si se especifica
- Resumen corto del evento (máximo 30 palabras)
- Resumen detallado del evento (máximo 100 palabras)

## REGLAS PARA FRAGMENTOS:

Para cada mención de un evento, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## IDENTIFICACIÓN DE EVENTOS:

Considera como eventos:
- **Música**: Ensayos, conciertos, grabaciones, clases de música, jam sessions, composición
- **Programación**: Sesiones de coding, reuniones de trabajo, deployment, debugging, code reviews
- **Trabajo general**: Reuniones laborales, presentaciones, deadlines, citas profesionales
- **Aprendizaje**: Tutoriales, cursos online, documentación, clases, talleres
- **Social**: Encuentros con amigos, fiestas, celebraciones, actividades sociales
- **Salud**: Citas médicas, entrenamientos, terapias, actividades de bienestar
- **Cultural**: Eventos artísticos, exposiciones, conciertos como audiencia
- **Personal**: Eventos familiares, citas importantes, actividades personales
- **Colaboración**: Sesiones con otros músicos, pair programming, trabajo en equipo
- **Ocio**: Entretenimiento, hobbies, actividades recreativas, tiempo libre
- **Viajes**: Desplazamientos, vacaciones, excursiones
- Referencias a "el ensayo", "la sesión", "el deploy", "la reunión", "la cita", etc.
- Cualquier actividad que ocurrió en un momento específico

## CATEGORÍAS PRINCIPALES:

- **Música**: Ensayos, conciertos, grabaciones, composición, práctica, clases musicales
- **Programación**: Coding sessions, debugging, deployment, code reviews, desarrollo
- **Trabajo**: Reuniones laborales, presentaciones, deadlines, actividades profesionales
- **Colaboración**: Jam sessions, pair programming, reuniones de equipo, trabajo conjunto
- **Aprendizaje**: Tutoriales, cursos, documentación, talleres, formación
- **Social**: Encuentros con amigos, fiestas, celebraciones, actividades sociales
- **Salud**: Citas médicas, entrenamientos, terapias, actividades de bienestar
- **Presentación**: Conciertos, demos técnicas, shows, presentaciones públicas
- **Cultural**: Eventos artísticos, exposiciones, conciertos como audiencia
- **Personal**: Actividades familiares, citas importantes, eventos personales
- **Ocio**: Entretenimiento, hobbies, actividades recreativas
- **Viaje**: Desplazamientos, vacaciones, excursiones
- **Setup**: Configuración de equipos, instalación de software, preparativos técnicos
- **Otro**: Cualquier otro tipo de evento no cubierto arriba

## CASOS ESPECIALES:

- **Referencias indirectas**: Incluye menciones como "la reunión", "el entrenamiento", "la cita" si se refieren a eventos específicos
- **Múltiples menciones**: Si un evento aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Eventos sin nombre específico**: Usa una descripción breve basada en el contexto
- **Eventos recurrentes**: Trata cada instancia por separado si se mencionan fechas específicas

## FORMATO DE SALIDA:

Para cada evento:
- **Nombre**: [Nombre o descripción breve del evento]
- **Fragmentos**: [Lista de fragmentos de texto exactos]
- **Categoría**: [Categoría del evento]
- **Fecha**: [Cuándo ocurrió el evento]
- **Duración**: [Duración si se menciona]
- **Ubicación**: [Dónde tuvo lugar si se especifica]
- **Resumen corto**: [Máximo 30 palabras]
- **Resumen**: [Máximo 100 palabras]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara del evento
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los eventos mencionados en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Identifica eventos de cualquier tipo: reuniones, actividades sociales, entrenamientos, citas, etc.
- Incluye referencias indirectas como "la reunión", "el entrenamiento", "la cita" si se refieren a eventos específicos
- Extrae información sobre fecha, duración, ubicación y categoría cuando sea posible

**CATEGORÍAS DISPONIBLES:**
- Música: Ensayos, conciertos, grabaciones, composición, práctica, clases musicales
- Programación: Coding sessions, debugging, deployment, code reviews, desarrollo
- Trabajo: Reuniones laborales, presentaciones, deadlines, actividades profesionales
- Colaboración: Jam sessions, pair programming, reuniones de equipo, trabajo conjunto
- Aprendizaje: Tutoriales, cursos, documentación, talleres, formación
- Social: Encuentros con amigos, fiestas, celebraciones, actividades sociales
- Salud: Citas médicas, entrenamientos, terapias, actividades de bienestar
- Presentación: Conciertos, demos técnicas, shows, presentaciones públicas
- Cultural: Eventos artísticos, exposiciones, conciertos como audiencia
- Personal: Actividades familiares, citas importantes, eventos personales
- Ocio: Entretenimiento, hobbies, actividades recreativas
- Viaje: Desplazamientos, vacaciones, excursiones
- Setup: Configuración de equipos, instalación de software, preparativos técnicos
- Otro: Otros tipos de eventos no cubiertos en las categorías anteriores

**FORMATO REQUERIDO:**
- Nombre del evento (o descripción breve si no tiene nombre específico)
- Lista de todos los fragmentos de texto exactos donde aparece
- Categoría del evento
- Fecha y hora cuando ocurrió el evento
- Duración del evento (si se menciona)
- Ubicación donde tuvo lugar (si se especifica)
- Resumen corto (máximo 30 palabras)
- Resumen detallado (máximo 100 palabras)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
