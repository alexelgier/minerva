from typing import Type

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class ZettelSummary(BaseModel):
    """Summary data for a Zettel concept"""

    summary_short: str = Field(
        ...,
        description="Short summary of the concept. Max 30 words, concise and clear",
        max_length=300,
    )
    summary: str = Field(
        ...,
        description="Detailed summary of the concept. Max 100 words, comprehensive but focused",
        max_length=1000,
    )


class GenerateZettelSummaryPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[ZettelSummary]:
        return ZettelSummary

    @staticmethod
    def system_prompt() -> str:
        return """Genera resúmenes concisos y detallados para un concepto de Zettel basado en toda la información disponible.

INSTRUCCIONES:
1. Analiza toda la información proporcionada sobre el concepto
2. Genera un resumen corto (summary_short) que capture la esencia del concepto en máximo 50 palabras
3. Genera un resumen detallado (summary) que explique el concepto de manera comprehensiva en máximo 200 palabras
4. Los resúmenes deben ser claros, precisos y útiles para entender el concepto
5. Usa un lenguaje claro y directo
6. Incluye los aspectos más importantes del concepto basándote en el análisis y conexiones

CRITERIOS PARA LOS RESUMENES:
- summary_short: Debe ser una definición concisa que alguien pueda leer rápidamente
- summary: Debe incluir contexto, importancia, y relaciones del concepto
- Ambos deben ser informativos pero no repetitivos
- Usa la información de análisis y conexiones para enriquecer los resúmenes
- Mantén un tono profesional pero accesible

USO DE LAS CONEXIONES:
- Las conexiones muestran relaciones del concepto con otros conceptos
- Usa esta información para contextualizar el concepto dentro de su red de relaciones
- Si hay conexiones, menciona brevemente las más relevantes en el resumen detallado
- Las conexiones ayudan a entender el lugar del concepto en el sistema de conocimiento

FORMATO:
- summary_short: Máximo 30 palabras, una definición clara y directa
- summary: Máximo 100 palabras, explicación detallada con contexto y relevancia"""

    @staticmethod
    def user_prompt(zettel_data: dict) -> str:
        # Format connections properly
        connections = zettel_data.get("connections", {})
        connections_text = "No hay conexiones"

        if connections and isinstance(connections, dict):
            connection_lines = []
            for relation_type, concept_list in connections.items():
                if concept_list:  # Only include non-empty relations
                    concepts_str = ", ".join(concept_list)
                    connection_lines.append(f"- {relation_type}: {concepts_str}")

            if connection_lines:
                connections_text = "\n".join(connection_lines)

        return f"""Genera resúmenes para el siguiente concepto de Zettel:

TÍTULO: {zettel_data.get('title', 'Sin título')}
NOMBRE: {zettel_data.get('name', 'Sin nombre')}

CONCEPT:
{zettel_data.get('concept', 'No hay contenido del concepto disponible')}

ANÁLISIS:
{zettel_data.get('analysis', 'No hay análisis disponible')}

CONEXIONES:
{connections_text}

FUENTE:
{zettel_data.get('source', 'No hay fuente especificada')}

Basándote en toda esta información, genera un resumen corto y uno detallado que capture la esencia y el valor de este concepto."""
