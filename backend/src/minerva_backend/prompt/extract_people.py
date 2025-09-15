from typing import List, Type

from pydantic import BaseModel, Field, conset

from minerva_backend.prompt.base import Prompt


class Person(BaseModel):
    """A person extracted from a text."""
    name: str = Field(..., description="Name of person")
    chunks: conset(str, min_length=1) = Field(..., description="Chunks of text where the person is mentioned")


class People(BaseModel):
    """A list of people extracted from a text."""
    people: List[Person] = Field(..., description="List of people mentioned in the text")


class ExtractPeoplePrompt(Prompt):
    @staticmethod
    def response_model() -> Type[People]:
        return People

    @staticmethod
    def system_prompt() -> str:
        return """Extrae todas las personas mencionadas en esta entrada del diario, incluyendo el narrador (Alex Elgier)
Para cada persona, incluye su nombre y todos los fragmentos de texto relevantes (chunks), citados directamente sin modificar.
Un chunk debe ser:
- Una oración o frase completa que mencione a la persona, máximo 3 oraciones.
Cada persona aparece una vez con todos sus chunks.
Incluye solo personas explícitamente mencionadas en el texto.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""<JOURNAL_ENTRY>
{context['text']}
</JOURNAL_ENTRY>
Extrae todas las personas mencionadas en esta entrada del diario."""
