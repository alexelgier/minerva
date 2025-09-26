from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.graph.models.enums import EmotionType
from minerva_backend.prompt.base import Prompt


class Feeling(BaseModel):
    """An occurrence of feeling an emotion in the text"""
    emotion: EmotionType = Field(..., description="Type of emotion felt")
    person_uuid: str = Field(..., description="UUID of person feeling the emotion")
    spans: List[str] = Field(..., description="Exact text fragments where the feeling is mentioned", min_length=1)


class Feelings(BaseModel):
    """A list of feelings extracted from a text."""
    feelings: List[Feeling] = Field(..., description="List of feelings mentioned in the text")


class ExtractEmotionsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Feelings]:
        return Feelings

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los sentimientos y emociones expresados en esta entrada del diario.

    Para cada sentimiento, incluye:
    - El tipo de emoción sentida (usando los tipos disponibles)
    - El UUID de la persona que siente la emoción
    - Todos los fragmentos de texto exactos donde se expresa el sentimiento

    ## TIPOS DE EMOCIONES DISPONIBLES:
    Anger, Annoyance, Contempt, Disgust, Irritation, Anxiety, Embarrassment, Fear, Helplessness, Powerlessness, Worry, Doubt, Envy, Frustration, Guilt, Shame, Confusion, Boredom, Despair, Disappointment, Hurt, Sadness, Loneliness, Stress, Tension, Amusement, Delight, Elation, Excitement, Happiness, Joy, Pleasure, Satisfaction, Affection, Empathy, Love, Pride, Gratitude, Hope, Trust, Anticipation, Calmness, Contentment, Relaxation, Relief, Serenity, Awe, Nostalgia, Interest, Surprise
    
    Usa ÚNICAMENTE estos tipos de emoción:
    
    
    ## REGLAS PARA FRAGMENTOS:

    Para cada expresión emocional, extrae:
    - La oración completa donde aparece la emoción
    - Hasta 2 oraciones adicionales de contexto (anterior o posterior) si ayudan a entender el sentimiento
    - Cada fragmento debe ser texto continuo del original (sin saltos ni omisiones)

    ## CASOS ESPECIALES:

    - **Narrador**: Todas las emociones en primera persona ("me siento", "estoy", "me da", etc.) se refieren a Alex Elgier
    - **Emociones de otros**: Para emociones de terceras personas, asegúrate de identificar correctamente quién las siente
    - **Emociones implícitas**: Incluye sentimientos que se expresan indirectamente a través de acciones o descripciones
    - **Múltiples emociones**: Una persona puede sentir varias emociones diferentes en el mismo texto

    ## FORMATO DE SALIDA:

    Para cada sentimiento:
    - **Emoción**: [Tipo de emoción de la lista anterior]
    - **Persona**: [UUID de quien siente la emoción]
    - **Fragmentos**: [Lista de fragmentos de texto exactos]

    ## VERIFICACIÓN FINAL:

    Confirma que cada fragmento:
    - Es texto copiado exactamente del original (incluye puntuación, mayúsculas, espacios)
    - Contiene al menos una expresión emocional clara
    - Tiene suficiente contexto para entender el sentimiento
    - Es texto continuo sin omisiones

    **CRÍTICO**: Copia el texto EXACTAMENTE como aparece. No modifiques, no resumas, no corrijas errores del original."""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""Extrae todos los sentimientos y emociones expresados en esta entrada del diario.

    **INSTRUCCIONES:**
    - Para cada emoción, extrae la oración completa más hasta 2 oraciones de contexto si es relevante
    - Cada fragmento debe ser texto continuo copiado exactamente del original
    - Todas las emociones en primera persona ("me siento", "estoy") se refieren a Alex Elgier
    - Identifica correctamente el UUID de la persona que siente cada emoción
    - Incluye emociones tanto explícitas como implícitas

    **FORMATO REQUERIDO:**
    - Tipo de emoción (usar solo tipos de la lista disponible)
    - UUID de la persona que siente la emoción
    - Lista de todos los fragmentos de texto exactos donde se expresa

    **IMPORTANTE:** Copia el texto EXACTAMENTE como aparece en el original, sin modificar nada.

    ---
    <PEOPLE>
    {context['people']}
    </PEOPLE>

    <JOURNAL_ENTRY>
    {context['text']}
    </JOURNAL_ENTRY>

    """
