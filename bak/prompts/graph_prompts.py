from typing import Any

from graphiti_core.prompts import Message
from graphiti_core.prompts.prompt_helpers import to_prompt_json


def dedupe_nodes(context: dict[str, Any]) -> list[Message]:
    return [
        Message(
            role='system',
            content='You are a helpful assistant that determines whether or not ENTITIES are duplicates of other '
                    'existing entities.',
        ),
        Message(
            role='user',
            content=f"""
        Each of the following ENTITIES is to be checked for duplicates.
        Each entity in ENTITIES is represented as a JSON object with the following structure:
        {{
            id: integer id of the entity,
            name: "name of the entity",
            entity_type: "ontological classification of the entity",
            entity_type_description: "Description of what the entity type represents",
            duplication_candidates: [
                {{
                    idx: integer index of the candidate entity,
                    name: "name of the candidate entity",
                    entity_type: "ontological classification of the candidate entity",
                    ...<additional attributes>
                }}
            ]
        }}

        <ENTITIES>
        {to_prompt_json(context['nodes'], ensure_ascii=context.get('ensure_ascii', True), indent=2)}
        </ENTITIES>

        <EXISTING ENTITIES>
        {to_prompt_json(context['existing_nodes'], ensure_ascii=context.get('ensure_ascii', True), indent=2)}
        </EXISTING ENTITIES>

        For each of the above ENTITIES, determine if the entity is a duplicate of any of the EXISTING ENTITIES.

        Entities should only be considered duplicates if they refer to the *same real-world object or concept*.

        Do NOT mark entities as duplicates if:
        - They are related but distinct.
        - They have similar names or purposes but refer to separate instances or concepts.

        Task:
        Your response will be a list called entity_resolutions which contains one entry for each entity.

        For each entity, return the id of the entity as id, the name of the entity as name, and the duplicate_idx
        as an integer.

        - If an entity is a duplicate of one of the EXISTING ENTITIES, return the idx of the candidate it is a 
        duplicate of.
        - If an entity is not a duplicate of one of the EXISTING ENTITIES, return the -1 as the duplication_idx
        """,
        ),
    ]


def merge_summaries(summary1, summary2) -> list[Message]:
    return [
        Message(
            role='system',
            content='You are a helpful assistant that combines summaries.',
        ),
        Message(
            role='user',
            content=f"""
        Synthesize the information from the following two summaries into a single succinct summary.
        
        Summaries must be under 250 words.

        <SUMMARY_1>
        {summary1}
        </SUMMARY_1>

        <SUMMARY_2>
        {summary2}
        </SUMMARY_2>

""",
        ),
    ]
