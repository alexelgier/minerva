"""Temporal workflow for concept extraction from content quotes, with human curation."""

import asyncio
import os
import time
from datetime import timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from temporalio import activity, workflow
from temporalio.common import RetryPolicy


class ConceptExtractionActivities:
    @activity.defn
    async def emit_notification(
        workflow_id: str,
        workflow_type: str,
        notification_type: str,
        title: str,
        message: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Write a notification to the curation DB (for UI display)."""
        from minerva_backend.containers import Container

        container = Container()
        await container.curation_manager().create_notification(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            notification_type=notification_type,
            title=title,
            message=message,
            payload=payload,
        )

    @activity.defn
    async def load_content_and_quotes(content_uuid: str) -> Dict[str, Any]:
        """Fetch Content and Quote nodes from Neo4j for the given content."""
        from minerva_backend.containers import Container

        container = Container()
        content_repo = container.content_repository()
        quote_repo = container.quote_repository()
        content = await content_repo.find_by_uuid(content_uuid)
        if not content:
            raise ValueError(f"Content not found: {content_uuid}")
        quotes = await quote_repo.find_quotes_by_content(content_uuid)
        return {
            "content_uuid": content_uuid,
            "content": content.model_dump() if hasattr(content, "model_dump") else content.dict(),
            "quotes": [
                q.model_dump() if hasattr(q, "model_dump") else q.dict()
                for q in quotes
            ],
        }

    @activity.defn
    async def extract_candidate_concepts(
        content_uuid: str, quotes: List[Dict], user_suggestions: str | None
    ) -> List[Dict[str, Any]]:
        """LLM: Extract candidate concepts from quotes. Stub: one placeholder concept."""
        from langchain.chat_models import init_chat_model
        from langchain_core.messages import HumanMessage, SystemMessage
        from pydantic import BaseModel, Field

        class CandidateConcept(BaseModel):
            concept_id: str = Field(..., description="Temporary ID")
            title: str = Field(..., description="Title")
            concept: str = Field(..., description="Concept text")
            analysis: str = Field(..., description="Analysis")
            source_quote_ids: List[str] = Field(..., description="Quote UUIDs")

        class CandidateConceptsResponse(BaseModel):
            candidate_concepts: List[CandidateConcept]

        if not quotes:
            return []
        model_name = os.getenv("MINERVA_CONCEPT_EXTRACT_MODEL", "gemini-2.5-pro")
        model_provider = os.getenv("MINERVA_CONCEPT_EXTRACT_PROVIDER", "google-genai")
        try:
            llm = init_chat_model(
                model=model_name,
                model_provider=model_provider,
                temperature=0,
            )
            llm_structured = llm.with_structured_output(
                CandidateConceptsResponse, method="json_schema"
            )
            quotes_text = "\n".join(
                f"- [{q.get('uuid', '')}] {q.get('text', '')[:200]}"
                for q in quotes[:20]
            )
            prompt = f"Content UUID: {content_uuid}. Quotes:\n{quotes_text}\n\nExtract 1-5 atomic concepts (Zettels). Use Spanish for title/concept/analysis. source_quote_ids: list of quote UUIDs that form each concept."
            out = await llm_structured.ainvoke(
                [HumanMessage(content=prompt)]
            )
            return [c.model_dump() for c in out.candidate_concepts]
        except Exception as e:
            activity.logger.warning(f"LLM extraction failed: {e}")
            return [
                {
                    "concept_id": f"temp-{uuid4().hex[:8]}",
                    "title": "Concepto placeholder",
                    "concept": "Extracción no disponible.",
                    "analysis": "",
                    "source_quote_ids": [q.get("uuid", "") for q in quotes[:1] if q.get("uuid")],
                }
            ]

    @activity.defn
    async def detect_duplicates(
        candidates: List[Dict], content_uuid: str
    ) -> Dict[str, Any]:
        """Stub: return novel_concepts = candidates, existing_with_new_quotes = []."""
        return {
            "novel_concepts": candidates,
            "existing_with_new_quotes": [],
        }

    @activity.defn
    async def discover_relations(
        novel_concepts: List[Dict], content_uuid: str
    ) -> List[Dict[str, Any]]:
        """Stub: return empty relations."""
        return []

    @activity.defn
    async def self_critique(
        concepts: List[Dict], relations: List[Dict]
    ) -> Dict[str, Any]:
        """Stub: return passes=True."""
        return {"passes": True, "issues": []}

    @activity.defn
    async def refine_extraction(
        concepts: List[Dict], relations: List[Dict], issues: List[str]
    ) -> Dict[str, Any]:
        """Stub: return same concepts and relations."""
        return {"concepts": concepts, "relations": relations}

    @activity.defn
    async def submit_concept_curation(
        workflow_id: str,
        content_uuid: str,
        concepts: List[Dict],
        relations: List[Dict],
    ) -> None:
        """Write concepts and relations to curation DB."""
        from minerva_backend.containers import Container

        container = Container()
        await container.curation_manager().create_concept_workflow(
            workflow_id, content_uuid
        )
        concept_items = [
            {
                "uuid": c.get("concept_id", str(uuid4())),
                "original_data_json": c,
            }
            for c in concepts
        ]
        await container.curation_manager().queue_concept_curation_items(
            workflow_id, concept_items
        )
        rel_items = [
            {
                "uuid": str(uuid4()),
                "original_data_json": r,
            }
            for r in relations
        ]
        await container.curation_manager().queue_concept_relation_curation_items(
            workflow_id, rel_items
        )
        await container.curation_manager().create_notification(
            workflow_id=workflow_id,
            workflow_type="concept_extraction",
            notification_type="curation_pending",
            title="Concepts ready for review",
            message=f"{len(concepts)} concepts, {len(relations)} relations from content",
            payload={"content_uuid": content_uuid},
        )

    @activity.defn
    async def wait_for_concept_curation(
        workflow_id: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Poll until all items approved/rejected; return (approved_concepts, approved_relations)."""
        from minerva_backend.containers import Container

        container = Container()
        while True:
            pending = await container.curation_manager().get_concept_pending_count(
                workflow_id
            )
            if pending == 0:
                concepts = await container.curation_manager().get_approved_concept_items(
                    workflow_id
                )
                relations = await container.curation_manager().get_approved_concept_relation_items(
                    workflow_id
                )
                return (concepts, relations)
            activity.heartbeat()
            await asyncio.sleep(30)

    @activity.defn
    async def write_concepts_to_graph(
        workflow_id: str,
        content_uuid: str,
        approved_concepts: List[Dict],
        approved_relations: List[Dict],
    ) -> List[str]:
        """Create Concept nodes, SUPPORTS (Quote->Concept), and concept relations in Neo4j."""
        from minerva_backend.containers import Container
        from minerva_models import Concept

        container = Container()
        concept_repo = container.concept_repository()
        connection = container.db_connection()
        concept_uuids = []
        for c in approved_concepts:
            title = c.get("title", "Sin título")
            concept_text = c.get("concept", "")
            concept = Concept(
                name=title,
                summary=concept_text[:500] if concept_text else title,
                summary_short=(concept_text[:80] if concept_text else title),
                title=title,
                concept=concept_text,
                analysis=c.get("analysis", ""),
                source=c.get("source"),
            )
            c_uuid = await concept_repo.create(concept)
            concept_uuids.append(c_uuid)
            # SUPPORTS: Quote -> Concept
            for qid in c.get("source_quote_ids", []):
                if not qid:
                    continue
                query = """
                MATCH (q:Quote {uuid: $quote_uuid})
                MATCH (c:Concept {uuid: $concept_uuid})
                MERGE (q)-[:SUPPORTS]->(c)
                """
                async with connection.session_async() as session:
                    await session.run(
                        query, quote_uuid=qid, concept_uuid=c_uuid
                    )
        # Concept-to-concept relations (stub: skip if no relations)
        for rel in approved_relations:
            src = rel.get("source_concept_id") or rel.get("source_id")
            tgt = rel.get("target_concept_id") or rel.get("target_id")
            rel_type = rel.get("relation_type", "RELATES_TO")
            if not src or not tgt:
                continue
            query = """
            MATCH (a:Concept {uuid: $src}), (b:Concept {uuid: $tgt})
            MERGE (a)-[r:RELATION {type: $rel_type}]->(b)
            """
            async with connection.session_async() as session:
                await session.run(
                    query, src=src, tgt=tgt, rel_type=rel_type
                )
        return concept_uuids

    @activity.defn
    async def create_obsidian_files(
        content_uuid: str,
        approved_concepts: List[Dict],
        concept_uuids: List[str],
    ) -> None:
        """Stub: Obsidian zettel file creation (can plug obsidian_service later)."""
        activity.logger.info(
            f"create_obsidian_files stub: {len(approved_concepts)} concepts for content {content_uuid}"
        )

    @activity.defn
    async def mark_content_processed(content_uuid: str) -> None:
        """Stub: Mark content as processed (update Content node if field exists)."""
        activity.logger.info(f"mark_content_processed stub: {content_uuid}")


@workflow.defn(name="ConceptExtraction")
class ConceptExtractionWorkflow:
    """Extract concepts from content quotes and write to Neo4j after human curation."""

    @workflow.run
    async def run(self, content_uuid: str) -> Dict[str, Any]:
        workflow_id = f"concept-{content_uuid}"
        await workflow.execute_activity(
            ConceptExtractionActivities.emit_notification,
            args=[
                workflow_id,
                "concept_extraction",
                "workflow_started",
                "Concept extraction started",
                f"Content: {content_uuid}",
                {"content_uuid": content_uuid},
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )
        llm_retry = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_attempts=3,
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
        )

        data = await workflow.execute_activity(
            ConceptExtractionActivities.load_content_and_quotes,
            args=[content_uuid],
            start_to_close_timeout=timedelta(minutes=5),
        )
        quotes = data["quotes"]
        if not quotes:
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "message": "No quotes for this content",
            }

        concepts = await workflow.execute_activity(
            ConceptExtractionActivities.extract_candidate_concepts,
            args=[content_uuid, quotes, None],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=llm_retry,
        )
        dup_result = await workflow.execute_activity(
            ConceptExtractionActivities.detect_duplicates,
            args=[concepts, content_uuid],
            start_to_close_timeout=timedelta(minutes=5),
        )
        novel = dup_result["novel_concepts"]
        relations = await workflow.execute_activity(
            ConceptExtractionActivities.discover_relations,
            args=[novel, content_uuid],
            start_to_close_timeout=timedelta(minutes=5),
        )
        critique = await workflow.execute_activity(
            ConceptExtractionActivities.self_critique,
            args=[novel, relations],
            start_to_close_timeout=timedelta(minutes=3),
        )
        if not critique.get("passes"):
            refined = await workflow.execute_activity(
                ConceptExtractionActivities.refine_extraction,
                args=[novel, relations, critique.get("issues", [])],
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=llm_retry,
            )
            novel = refined.get("concepts", novel)
            relations = refined.get("relations", relations)

        await workflow.execute_activity(
            ConceptExtractionActivities.submit_concept_curation,
            args=[workflow_id, content_uuid, novel, relations],
            start_to_close_timeout=timedelta(minutes=2),
        )
        approved_concepts, approved_relations = await workflow.execute_activity(
            ConceptExtractionActivities.wait_for_concept_curation,
            args=[workflow_id],
            schedule_to_close_timeout=timedelta(days=7),
            heartbeat_timeout=timedelta(minutes=2),
        )

        if approved_concepts:
            concept_uuids = await workflow.execute_activity(
                ConceptExtractionActivities.write_concepts_to_graph,
                args=[workflow_id, content_uuid, approved_concepts, approved_relations],
                start_to_close_timeout=timedelta(minutes=10),
            )
            await workflow.execute_activity(
                ConceptExtractionActivities.create_obsidian_files,
                args=[content_uuid, approved_concepts, concept_uuids],
                start_to_close_timeout=timedelta(minutes=5),
            )
            await workflow.execute_activity(
                ConceptExtractionActivities.mark_content_processed,
                args=[content_uuid],
                start_to_close_timeout=timedelta(minutes=1),
            )
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "concepts_created": len(concept_uuids),
            }
        return {"workflow_id": workflow_id, "status": "completed", "concepts_created": 0}
