import datetime
from typing import Any, Dict, List

from pydantic import BaseModel

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.services.knowledge_graph_service import (
    KnowledgeGraphService,
)


# The `JournalSubmission` model is defined in `api.main`, but to avoid potential
# circular dependencies between the processing layer and the API layer,
# we define a similar structure here. This should be kept in sync with the API model.
class JournalSubmission(BaseModel):
    content: str
    date: datetime.date
    # Psychological metrics like panas_scores, bpns_scores, etc. would go here.


class JournalProcessingPipeline:
    """
    Orchestrates the end-to-end processing of a journal entry, from submission
    to knowledge graph integration, following the phases defined in the PRD.
    """

    def __init__(self, kg_service: KnowledgeGraphService = None):
        """
        Initializes the pipeline with a KnowledgeGraphService.
        """
        self.kg_service = kg_service or KnowledgeGraphService()
        # self.llm_client = ... # To be added when LLM client is available

    def process_journal_submission(self, submission: JournalSubmission) -> str:
        """
        Main entry point for processing a journal submission.

        This method follows the data flow architecture from the PRD:
        1. Note Submission and Initial Processing
        2. Entity Extraction and Queueing
        3. Human-in-the-Loop Entity Curation (handled by frontend)
        4. Relationship Extraction and Secondary Curation (handled by frontend)
        5. Knowledge Graph Integration and Entity Evolution

        Args:
            submission: The journal submission data from the API.

        Returns:
            The UUID of the created journal entry.
        """
        # Phase 1: Note Submission and Initial Processing
        journal_entry = self._create_journal_entry_node(submission)

        # Phase 2: Entity Extraction and Queueing (Asynchronous)
        # In a real system, this would be a background task.
        extracted_entities = self._extract_entities(journal_entry.content)

        # Phase 3: Curation is handled by the frontend. We'll proceed with extracted entities.
        approved_entities = extracted_entities  # Placeholder for curation result

        # Phase 4: Relationship Extraction (Asynchronous)
        extracted_relationships = self._extract_relationships(
            journal_entry.content, approved_entities
        )
        approved_relationships = extracted_relationships  # Placeholder

        # Phase 5: Knowledge Graph Integration
        self._integrate_into_graph(
            journal_entry.uuid, approved_entities, approved_relationships
        )

        return journal_entry.uuid

    def _create_journal_entry_node(self, submission: JournalSubmission) -> JournalEntry:
        """
        Creates and stores a JournalEntry node in the knowledge graph.
        """
        # Map all fields from submission to JournalEntry
        journal_entry_data = submission.dict()
        journal_entry = JournalEntry(**journal_entry_data)

        uuid = self.kg_service.add_journal_entry(journal_entry)
        journal_entry.uuid = uuid
        return journal_entry

    def _extract_entities(self, content: str) -> List[Dict[str, Any]]:
        """
        Uses an LLM to extract entities from the journal content. Placeholder.
        """
        print(f"Extracting entities from content: {content[:50]}...")
        # This would invoke a local Ollama model (e.g., Qwen3)
        return []

    def _extract_relationships(
        self, content: str, entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Uses an LLM to extract relationships between approved entities. Placeholder.
        """
        print(f"Extracting relationships for {len(entities)} entities...")
        # This would be a second LLM pass after entity curation.
        return []

    def _integrate_into_graph(
        self,
        journal_uuid: str,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
    ):
        """
        Integrates approved entities and relationships into the knowledge graph.
        """
        print(
            f"Integrating {len(entities)} entities and {len(relationships)} "
            f"relationships for journal {journal_uuid}..."
        )
        # This would involve calls to various repository methods via KnowledgeGraphService
        # to create/merge entities and form relationships.
        pass
