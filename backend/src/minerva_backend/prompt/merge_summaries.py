from typing import Type

from pydantic import BaseModel, Field


class Summaries(BaseModel):
    summary_short: str = Field(..., description="Resumen. Máximo 30 palabras")
    summary: str = Field(..., description="Resumen. Máximo 100 palabras")


class MergeSummariesPrompt:
    """Prompt for merging entity/relation summaries intelligently."""

    @staticmethod
    def response_model() -> Type[Summaries]:
        return Summaries

    @staticmethod
    def system_prompt() -> str:
        return """Eres un experto en fusionar resúmenes de manera inteligente y precisa.

Tu tarea es tomar dos pares de resúmenes (uno existente y uno nuevo), y crear un par de resúmenes fusionados que combine la información de ambos de manera coherente.

REGLAS IMPORTANTES:
- La información más reciente NO siempre es más correcta - usa tu juicio
- Si hay contradicciones, prefiere la información más específica/detallada
- No inventes información que no esté en los resúmenes originales
- Si un resumen está vacío o es genérico, prioriza el otro

LÍMITES ESTRICTOS:
- summary (resumen largo): MÁXIMO 100 palabras
- short_summary (resumen corto): MÁXIMO 30 palabras

El resumen corto debe ser la versión más condensada del resumen largo, no información diferente."""

    @staticmethod
    def user_prompt(data: dict) -> str:
        existing_summary = data['existing_summary']
        existing_short_summary = data['existing_short_summary']
        new_summary = data['new_summary']
        new_short_summary = data['new_short_summary']
        entity_name = data['entity_name']

        return f"""Fusiona la información sobre: {entity_name}

RESÚMENES EXISTENTES:
<RESUMEN_LARGO>{existing_summary}</RESUMEN_LARGO>
<RESUMEN_CORTO>{existing_short_summary}</RESUMEN_CORTO>

NUEVOS RESÚMENES:
<RESUMEN_LARGO>{new_summary}</RESUMEN_LARGO>
<RESUMEN_CORTO>{new_short_summary}</RESUMEN_CORTO>

Crea resúmenes fusionados que combinen lo mejor de ambos, eliminando redundancia pero preservando detalles importantes."""
