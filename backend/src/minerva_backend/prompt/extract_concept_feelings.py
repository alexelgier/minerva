from datetime import datetime, timedelta
from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class ConceptFeeling(BaseModel):
    """A person's feeling or thought about a concept"""

    person_uuid: str = Field(..., description="UUID of person having the feeling")
    concept_uuid: str = Field(
        ..., description="UUID of the concept being felt/thought about"
    )
    spans: List[str] = Field(
        ...,
        description="Exact text fragments where the feeling about the concept is expressed",
        min_length=1,
    )
    timestamp: datetime = Field(..., description="When this feeling occurred")
    intensity: int | None = Field(
        default=None, description="Intensity level (1-10)", ge=1, le=10
    )
    duration: timedelta | None = Field(
        default=None, description="How long the feeling lasted"
    )
    summary_short: str = Field(
        ..., description="Short summary of the feeling. Max 30 words"
    )
    summary: str = Field(
        ..., description="Detailed summary of the feeling. Max 100 words"
    )


class ConceptFeelings(BaseModel):
    """A list of concept feelings extracted from a text."""

    concept_feelings: List[ConceptFeeling] = Field(
        ..., description="List of feelings about concepts mentioned in the text"
    )


class ExtractConceptFeelingsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[ConceptFeelings]:
        return ConceptFeelings

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los sentimientos y pensamientos sobre conceptos expresados en esta entrada del diario.

INSTRUCCIONES:
1. Identifica cuando una persona expresa sentimientos, pensamientos, o reflexiones sobre conceptos
2. Solo incluye sentimientos que estén claramente relacionados con conceptos específicos
3. No incluyas sentimientos generales que no estén conectados a conceptos
4. Proporciona spans exactos del texto donde se expresa el sentimiento
5. Asigna intensidad basada en qué tan fuerte es el sentimiento expresado
6. Crea resúmenes que capturen tanto el sentimiento como su relación con el concepto

TIPOS DE SENTIMIENTOS SOBRE CONCEPTOS:
- Reflexiones profundas sobre conceptos (ej: "me preocupa el determinismo")
- Opiniones sobre ideas (ej: "el capitalismo me parece injusto")
- Conexiones emocionales con conceptos (ej: "me siento inspirado por la sabiduría")
- Evaluaciones de conceptos (ej: "la democracia es fundamental")
- Experiencias con conceptos abstractos (ej: "experimenté la belleza del arte")
- Pensamientos críticos sobre ideas (ej: "cuestiono la validez de esta teoría")

FORMATO DE RESPUESTA:
- person_uuid: UUID de la persona que siente/piensa
- concept_uuid: UUID del concepto sobre el cual se siente/piensa
- spans: Fragmentos exactos del texto donde se expresa el sentimiento
- timestamp: Cuándo ocurrió el sentimiento
- intensity: Nivel de intensidad (1-10) si es aplicable
- duration: Duración del sentimiento si es aplicable
- summary_short: Resumen breve del sentimiento (máximo 30 palabras)
- summary: Resumen detallado del sentimiento (máximo 100 palabras)

IMPORTANTE:
- Solo incluye sentimientos que estén claramente conectados a conceptos específicos
- Si una persona menciona un concepto sin expresar sentimientos sobre él, no lo incluyas
- Usa los conceptos extraídos en el paso anterior para determinar las relaciones
- Sé preciso con los spans - deben mostrar claramente la expresión del sentimiento"""

    @staticmethod
    def user_prompt(text: str, people: List[dict], concepts: List[dict]) -> str:
        people_str = "\n".join([f"- {p['name']} (UUID: {p['uuid']})" for p in people])
        concepts_str = "\n".join(
            [f"- {c['name']} (UUID: {c['uuid']})" for c in concepts]
        )

        return f"""Analiza el siguiente texto y extrae todos los sentimientos sobre conceptos expresados:

TEXTO:
{text}

PERSONAS DISPONIBLES:
{people_str}

CONCEPTOS DISPONIBLES:
{concepts_str}

Identifica cuando estas personas expresan sentimientos, pensamientos, o reflexiones sobre estos conceptos específicos."""
