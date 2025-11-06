from typing import Type

from minerva_models import Person
from minerva_backend.prompt.base import Prompt


class HydratePersonPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Person]:
        return Person

    @staticmethod
    def system_prompt() -> str:
        return """Dado el nombre de una persona específica y una entrada de diario, crea un objeto Person completo.
Incluye todas las propiedades relevantes que puedas inferir de la entrada de diario.
- Mantén la fidelidad a los hechos explícitamente mencionados.
- Si una propiedad no se puede determinar, déjala vacía o como None.
- Evita inventar detalles que no estén en el texto."""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
Crea un objeto Person para <PERSON_NAME>{context['name']}</PERSON_NAME>, incluyendo todas las propiedades que puedas inferir del texto.
"""
