from typing import List, Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class ConceptMention(BaseModel):
    """A concept mentioned in the text"""

    name: str = Field(..., description="Name of the concept (same as title)")
    title: str = Field(..., description="Title of the concept (same as name)")
    concept: str = Field(..., description="Concept definition or exposition")
    analysis: str = Field(..., description="Analysis and understanding of the concept")
    source: str | None = Field(default=None, description="Source if mentioned in text")
    spans: List[str] = Field(
        ...,
        description="Exact text fragments where the concept is mentioned",
        min_length=1,
    )
    existing_uuid: str | None = Field(
        default=None, description="UUID of existing concept if it exists, None if new"
    )
    summary_short: str = Field(
        ..., description="Short summary of the concept. Max 30 words"
    )
    summary: str = Field(
        ..., description="Detailed summary of the concept. Max 100 words"
    )


class Concepts(BaseModel):
    """A list of concepts extracted from a text."""

    concepts: List[ConceptMention] = Field(
        ..., description="List of concepts mentioned in the text"
    )


class ExtractConceptsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Concepts]:
        return Concepts

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todos los conceptos e ideas mencionados en esta entrada del diario.

INSTRUCCIONES:
1. Identifica conceptos, ideas, teorías, principios, o nociones abstractas mencionados
2. Incluye conceptos tanto explícitos como implícitos
3. Para cada concepto, determina si ya existe en la base de conocimiento (existing_uuid) o es nuevo (None)
4. Proporciona spans exactos del texto donde se menciona cada concepto
5. Extrae el contenido del concepto basado en el contexto del texto
6. Crea resúmenes concisos pero informativos

TIPOS DE CONCEPTOS A EXTRAER:
- Conceptos filosóficos (ej: "existencialismo", "determinismo")
- Conceptos psicológicos (ej: "cognición", "subconsciente")
- Conceptos sociales (ej: "capitalismo", "democracia")
- Conceptos científicos (ej: "evolución", "entropía")
- Conceptos artísticos (ej: "estética", "narrativa")
- Conceptos personales (ej: "ambición", "sabiduría")
- Teorías y marcos conceptuales
- Principios y valores abstractos

FORMATO DE RESPUESTA:
- name: Nombre del concepto (usar el término más preciso)
- title: Título del concepto (mismo que name)
- concept: Definición o exposición del concepto
- analysis: Análisis y comprensión del concepto
- source: Fuente si se menciona en el texto
- spans: Fragmentos exactos del texto donde aparece
- existing_uuid: UUID si existe en la base de conocimiento, None si es nuevo
- summary_short: Resumen breve (máximo 30 palabras)
- summary: Resumen detallado (máximo 100 palabras)

IMPORTANTE:
- Solo extrae conceptos reales, no nombres propios o eventos específicos
- Si un concepto se menciona múltiples veces, inclúyelo una sola vez con todos los spans
- Usa el contexto proporcionado para determinar si un concepto ya existe
- El campo 'concept' debe contener la definición principal del concepto
- El campo 'analysis' debe contener tu análisis y comprensión del concepto"""

    @staticmethod
    def user_prompt(text: str, context: str = "") -> str:
        base_prompt = f"""Analiza el siguiente texto y extrae todos los conceptos e ideas mencionados:

TEXTO:
{text}"""

        if context:
            base_prompt += f"""

CONTEXTO DE CONCEPTOS EXISTENTES:
{context}

Usa este contexto para determinar si los conceptos ya existen en tu base de conocimiento."""

        return base_prompt
