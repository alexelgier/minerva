import re
import json
from .llm_utils import call_llm
from .prompts import METADATA_SYSTEM_PROMPT, METADATA_USER_PROMPT


def suggest_metadata(narrative):
    """Suggest semantic metadata based on the narrative."""
    message = METADATA_USER_PROMPT.format(narrative=narrative)
    response = call_llm(message, METADATA_SYSTEM_PROMPT)

    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    except:
        return {}


def interact_with_metadata(suggested_metadata):
    """Allow the user to confirm or edit the suggested metadata."""
    print("\n=== METADATOS SUGERIDOS ===")
    final_metadata = {}

    fields = [
        'clima', 'actividad_principal', 'lugar_principal',
        'personas', 'proyectos', 'estado_predominante', 'sensacion_corporal'
    ]

    for field in fields:
        suggested_value = suggested_metadata.get(field, '')
        print(f"{field}: {suggested_value}")

        response = input(f"Ingresa valor para {field} (enter para mantener, 'none' para omitir): ").strip()

        if response.lower() == 'none':
            continue
        elif response:
            if ',' in response:
                final_metadata[field] = [item.strip() for item in response.split(',')]
            else:
                final_metadata[field] = response
        elif suggested_value:
            final_metadata[field] = suggested_value

    return final_metadata
