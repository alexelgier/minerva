from typing import Type, Dict, Any

from pydantic import BaseModel, Field

from minerva_backend.graph.models.enums import RelationshipType
from minerva_backend.prompt.base import Prompt


class HydratedRelation(BaseModel):
    """A hydrated relationship with all its properties."""
    type: RelationshipType = Field(..., description="The type of relationship.")
    properties: Dict[str, Any] = Field(default_factory=dict,
                                       description="Additional properties, like 'context' or 'emotion' related to the interaction.")


class HydrateRelationshipPrompt(Prompt):
    @staticmethod
    def response_model() -> Type[HydratedRelation]:
        return HydratedRelation

    @staticmethod
    def system_prompt() -> str:
        return """
You are an expert knowledge graph extractor. Your task is to analyze a relationship between two entities from a journal entry and extract its details.
Given the source entity, target entity, and a description of their interaction, determine the relationship type and any relevant properties.
The relationship type must be one of the following: AFFECTS, CAUSES, ENABLES, INFLUENCES, INHIBITS, IS_A, PART_OF, PRECEDES, USES, FEELS, MENTIONS, CONTAINS.
Extract properties like the context of the interaction or any emotion involved.
"""

    @staticmethod
    def user_prompt(context: dict[str, str]) -> str:
        return f"""
Journal Entry Text:
---
{context['text']}
---

Interaction Details:
- Source Entity: {context['source']}
- Target Entity: {context['target']}
- Description: {context['description']}

Based on the text and interaction details, extract the relationship type and properties.
"""
