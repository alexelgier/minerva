from typing import List, Type

from pydantic import BaseModel, Field

from minerva_models import ResourceStatus, ResourceType
from minerva_backend.prompt.base import Prompt


class Content(BaseModel):
    """Un elemento de contenido extraído de un texto."""

    name: str = Field(..., description="Nombre del contenido")
    spans: List[str] = Field(
        ...,
        description="Fragmentos de texto exactos donde se menciona el contenido",
        min_length=1,
    )
    title: str = Field(..., description="Título o nombre del recurso de contenido")
    category: ResourceType = Field(
        ..., description="Categoría del recurso de contenido"
    )
    url: str | None = Field(
        default=None,
        description="URL web o ubicación donde se puede acceder al contenido",
    )
    quotes: List[str] | None = Field(
        default=None, description="Citas o extractos notables del contenido"
    )
    status: ResourceStatus | None = Field(
        default=None, description="Estado de consumo actual"
    )
    author: str | None = Field(
        default=None, description="Creador, autor, artista o director del contenido"
    )
    summary_short: str = Field(
        ..., description="Resumen breve del contenido. Máximo 30 palabras"
    )
    summary: str = Field(
        ..., description="Resumen detallado del contenido. Máximo 100 palabras"
    )


class Contents(BaseModel):
    """Una lista de elementos de contenido extraídos de un texto."""

    contents: List[Content] = Field(
        ..., description="Lista de contenido mencionado en el texto"
    )


class ExtractContentPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Contents]:
        return Contents

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los elementos de contenido mencionados en esta entrada del diario.

Para cada elemento de contenido, incluye:
- Su nombre (título específico o descripción del contenido)
- Todos los fragmentos de texto exactos donde aparece mencionado
- Categoría del contenido (video, libro, música, película, artículo, etc.)
- Resumen breve del contenido (máximo 30 palabras)
- Resumen detallado del contenido (máximo 100 palabras)

## REGLAS PARA FRAGMENTOS:

Para cada mención de contenido, extrae:
- La oración completa donde aparece
- Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender la mención
- Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

## IDENTIFICACIÓN DE CONTENIDO:

Considera como contenido:
- Videos (YouTube, TikTok, documentales, tutoriales, etc.)
- Libros (novelas, libros de texto, artículos, papers, etc.)
- Música (canciones, álbumes, sinfonías, playlists, etc.)
- Películas y series de TV (films, series, episodios, etc.)
- Podcasts y contenido de audio
- Juegos (videojuegos, juegos de mesa, etc.)
- Contenido educativo (cursos, conferencias, tutoriales, etc.)
- Contenido de redes sociales (posts, threads, stories, etc.)
- Documentación (docs técnicos, manuales, guías, etc.)
- Artículos de noticias y posts de blog
- Referencias a "el video", "ese libro", "la canción", "el documental", etc.

## CATEGORÍAS PRINCIPALES:

- **Video**: Videos de YouTube, documentales, tutoriales, vlogs, contenido corto
- **Libro**: Novelas, libros de no ficción, libros de texto, e-books
- **Música**: Canciones, álbumes, playlists, piezas clásicas, podcasts
- **Película**: Films, series de TV, episodios, contenido de streaming
- **Artículo**: Artículos de noticias, posts de blog, papers de investigación, ensayos
- **Juego**: Videojuegos, juegos móviles, juegos de mesa, juegos online
- **Curso**: Cursos educativos, conferencias, talleres, entrenamientos
- **Documentación**: Docs técnicos, manuales, guías, referencias
- **Social**: Posts de redes sociales, threads, stories, memes
- **Otro**: Cualquier otro tipo de contenido no cubierto arriba

## CASOS ESPECIALES:

- **Referencias indirectas**: Incluye menciones como "el video", "ese libro", "el documental" si se refieren a contenido específico
- **Múltiples menciones**: Si el contenido aparece varias veces en oraciones consecutivas, puedes crear un solo fragmento que las incluya todas
- **Contenido sin nombres específicos**: Usa una descripción breve basada en el contexto
- **Series/Colecciones**: Trata episodios individuales o capítulos separadamente de la serie general cuando se mencionen específicamente

## FORMATO DE SALIDA:

Para cada elemento de contenido:
- **Nombre**: [Título específico o descripción del contenido]
- **Fragmentos**: [Lista de fragmentos de texto exactos]
- **Categoría**: [Categoría del contenido]
- **Resumen breve**: [Máximo 30 palabras]
- **Resumen**: [Máximo 100 palabras]

## VERIFICACIÓN FINAL:

Confirma que cada fragmento:
- Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
- Contiene al menos una mención clara del contenido
- Tiene suficiente contexto para entender la referencia
- Es texto continuo sin omisiones

**CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los elementos de contenido mencionados en esta entrada del diario.

**INSTRUCCIONES:**
- Para cada mención, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
- Cada fragmento debe ser texto continuo copiado exactamente del original
- Identifica contenido de cualquier tipo: videos, libros, música, películas, artículos, juegos, cursos, etc.
- Incluye referencias indirectas como "el video", "ese libro", "el documental" si se refieren a contenido específico
- Categoriza cada elemento de contenido apropiadamente y crea resúmenes descriptivos

**CATEGORÍAS DISPONIBLES:**
- Video: Videos de YouTube, documentales, tutoriales, vlogs, contenido corto
- Libro: Novelas, no ficción, libros de texto, e-books, contenido escrito
- Música: Canciones, álbumes, playlists, piezas clásicas, contenido de audio
- Película: Films, series de TV, episodios, contenido de streaming
- Artículo: Artículos de noticias, posts de blog, papers de investigación, ensayos, piezas escritas
- Juego: Videojuegos, juegos móviles, juegos de mesa, juegos online
- Curso: Cursos educativos, conferencias, talleres, materiales de entrenamiento
- Documentación: Docs técnicos, manuales, guías, materiales de referencia
- Social: Posts de redes sociales, threads, stories, memes, contenido social
- Otro: Otros tipos de contenido no cubiertos arriba

**FORMATO REQUERIDO:**
- Nombre del contenido (o descripción breve si no tiene nombre específico)
- Lista de todos los fragmentos de texto exactos donde aparece
- Categoría del contenido
- Resumen breve (máximo 30 palabras)
- Resumen detallado (máximo 100 palabras)

**IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

---

<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
"""
