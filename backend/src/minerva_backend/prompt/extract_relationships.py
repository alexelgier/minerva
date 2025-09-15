from typing import Type, List

from pydantic import BaseModel, Field

from minerva_backend.prompt.base import Prompt


class SimpleRelationship(BaseModel):
    """A simple relationship between two entities."""
    source_entity_name: str = Field(..., description="The name of the source entity.")
    target_entity_name: str = Field(..., description="The name of the target entity.")
    description: str = Field(..., description="A short sentence describing the relationship from the text.")


class Relationships(BaseModel):
    """A list of relationships found in the text."""
    relationships: List[SimpleRelationship] = Field(..., description="A list of relationships.")


class ExtractRelationshipsPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[Relationships]:
        return Relationships

    @staticmethod
    def system_prompt() -> str:
        return """
You are an expert knowledge graph extractor.
Your task is to identify relationships between a given list of entities, based on a journal entry.
Focus ONLY on relationships explicitly mentioned in the text. Do not infer relationships.
The relationship should be between two entities from the provided list.
For each relationship, extract the source entity name, the target entity name, and a short description of the interaction.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""
Journal Entry Text:
---
{context['text']}
---

List of Entities:
---
{context['entities']}
---

Based on the journal entry, identify all relationships between the entities in the list.
"""
