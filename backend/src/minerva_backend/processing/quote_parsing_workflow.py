"""Temporal workflow for parsing quotes from markdown and writing to Neo4j after human curation."""

import asyncio
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from minerva_models import Content, Person, Quote, ResourceType, ResourceStatus


def _parse_quotes_from_content(content: str) -> List[Dict[str, Any]]:
    """Parse quotes from markdown '# Citas' section. Returns list of {text, section, page_reference}."""
    quotes = []
    citas_match = re.search(r"# Citas\n\n(.*)", content, re.DOTALL)
    if not citas_match:
        return quotes
    citas_content = citas_match.group(1)
    section_pattern = r"##\s+(.+?)\n(.*?)(?=##\s+|\Z)"
    sections = re.findall(section_pattern, citas_content, re.DOTALL)
    for section_title, section_content in sections:
        section_title = section_title.strip()
        for block in re.split(r"\n\n+", section_content.strip()):
            block = block.strip()
            if not block:
                continue
            page_match = re.search(r"\n(\d+(?:-\d+)?)\s*$", block)
            page_reference = page_match.group(1) if page_match else None
            quote_text = block[: page_match.start()].strip() if page_reference else block
            if len(quote_text) < 20:
                continue
            quotes.append({
                "text": quote_text,
                "section": section_title,
                "page_reference": page_reference,
            })
    return quotes


class QuoteParsingActivities:
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
    async def scan_markdown_file(file_path: str, vault_path: str) -> str:
        """Read markdown file content. file_path is relative to vault."""
        full = Path(vault_path).resolve() / file_path.lstrip("/")
        if not full.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")
        return full.read_text(encoding="utf-8", errors="replace")

    @activity.defn
    async def parse_quotes_and_summary(
        file_content: str, author: str, title: str
    ) -> Dict[str, Any]:
        """Parse '# Citas' section and generate summary/short summary via LLM. Returns quotes, summary, summary_short."""
        from langchain.chat_models import init_chat_model
        from langchain_core.messages import HumanMessage
        from pydantic import BaseModel, Field

        class SummaryResponse(BaseModel):
            summary: str = Field(..., description="Summary of the book. Max 100 words.")
            summary_short: str = Field(..., description="Short summary. Max 30 words.")

        quotes_data = _parse_quotes_from_content(file_content)
        model_name = os.getenv("MINERVA_QUOTE_SUMMARY_MODEL", "gemini-2.5-flash-lite")
        model_provider = os.getenv("MINERVA_QUOTE_SUMMARY_PROVIDER", "google-genai")
        try:
            llm = init_chat_model(
                model=model_name,
                model_provider=model_provider,
                temperature=0,
            )
            llm_structured = llm.with_structured_output(SummaryResponse, method="json_schema")
            prompt = f"""Book title: {title}\nAuthor: {author}\nNotes:\n{file_content[:4000]}\n\nGenerate summary and short summary."""
            response = await llm_structured.ainvoke(prompt)
            summary = response.summary
            summary_short = response.summary_short
        except Exception as e:
            activity.logger.warning(f"LLM summary failed: {e}")
            summary = f"Notes on {title} by {author}."
            summary_short = summary[:80]
        return {
            "quotes": quotes_data,
            "summary": summary,
            "summary_short": summary_short,
            "author": author,
            "title": title,
        }

    @activity.defn
    async def enrich_with_web_search(
        author: str, title: str, summary: str, summary_short: str
    ) -> Dict[str, Any]:
        """Optional enrichment. Stub: return same summaries; can plug zettel web_search_utils later."""
        return {
            "summary": summary,
            "summary_short": summary_short,
            "author_summary": f"Author of {title}",
            "author_occupation": "Author",
        }

    @activity.defn
    async def submit_quote_curation(
        workflow_id: str,
        file_path: str,
        content_title: str,
        content_author: str,
        quotes: List[Dict[str, Any]],
    ) -> None:
        """Write workflow row and quote items to curation DB."""
        from minerva_backend.containers import Container

        container = Container()
        await container.curation_manager().create_quote_workflow(
            workflow_id, file_path, content_title, content_author
        )
        items = [
            {"uuid": str(uuid4()), "original_data_json": q} for q in quotes
        ]
        await container.curation_manager().queue_quote_curation_items(workflow_id, items)
        await container.curation_manager().create_notification(
            workflow_id=workflow_id,
            workflow_type="quote_parsing",
            notification_type="curation_pending",
            title="Quotes ready for review",
            message=f"{len(quotes)} quotes from {content_title}",
            payload={"file_path": file_path, "content_title": content_title},
        )

    @activity.defn
    async def wait_for_quote_curation(workflow_id: str) -> List[Dict[str, Any]]:
        """Poll until all quote items approved/rejected; return approved items."""
        from minerva_backend.containers import Container

        container = Container()
        while True:
            pending = await container.curation_manager().get_quote_pending_count(
                workflow_id
            )
            if pending == 0:
                return await container.curation_manager().get_approved_quote_items(
                    workflow_id
                )
            activity.heartbeat()
            await asyncio.sleep(30)

    @activity.defn
    async def write_quotes_to_graph(
        workflow_id: str,
        approved_quotes: List[Dict[str, Any]],
        content_author: str,
        content_title: str,
        summary: str,
        summary_short: str,
    ) -> Dict[str, Any]:
        """Create Content, Person (if needed), AUTHORED_BY, Quote nodes, QUOTED_IN."""
        from minerva_backend.containers import Container

        container = Container()
        content_repo = container.content_repository()
        person_repo = container.person_repository()
        quote_repo = container.quote_repository()

        # Find or create author
        persons = await person_repo.search_by_name_partial(content_author)
        author_person = next(
            (p for p in persons if p.name and p.name.lower() == content_author.lower()),
            None,
        )
        if author_person is None:
            author_person = Person(
                name=content_author,
                summary=f"Author of {content_title}",
                summary_short=content_title[:50],
                occupation="Author",
            )
            author_person.uuid = await person_repo.create(author_person)

        # Create Content
        content = Content(
            name=f"{content_author} - {content_title}",
            title=content_title,
            author=content_author,
            summary=summary,
            summary_short=summary_short,
            category=ResourceType.BOOK,
            status=ResourceStatus.COMPLETED,
        )
        content_uuid = await content_repo.create(content)
        await content_repo.create_authored_by_relationship(
            author_person.uuid, content_uuid
        )

        # Create Quote nodes and QUOTED_IN
        quote_objs = []
        for q in approved_quotes:
            quote_objs.append(
                Quote(
                    text=q["text"],
                    section=q.get("section", ""),
                    page_reference=q.get("page_reference"),
                )
            )
        if quote_objs:
            await quote_repo.create_quotes_for_content(quote_objs, content_uuid)

        await container.curation_manager().complete_quote_workflow(workflow_id)
        return {"content_uuid": content_uuid, "quotes_count": len(approved_quotes)}


@workflow.defn(name="QuoteParsing")
class QuoteParsingWorkflow:
    """Parse quotes from markdown and write to Neo4j after human curation."""

    @workflow.run
    async def run(self, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        from minerva_backend.config import settings

        file_path = input_payload["file_path"]
        author = input_payload["author"]
        title = input_payload["title"]
        vault_path = settings.OBSIDIAN_VAULT_PATH
        workflow_id = f"quote-{uuid4().hex[:12]}"

        await workflow.execute_activity(
            QuoteParsingActivities.emit_notification,
            args=[
                workflow_id,
                "quote_parsing",
                "workflow_started",
                "Quote parsing started",
                f"File: {file_path}",
                {"file_path": file_path, "title": title, "author": author},
            ],
            start_to_close_timeout=timedelta(seconds=30),
        )
        content = await workflow.execute_activity(
            QuoteParsingActivities.scan_markdown_file,
            args=[file_path, vault_path],
            start_to_close_timeout=timedelta(minutes=5),
        )

        llm_retry = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            maximum_attempts=3,
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=2),
        )
        parsed = await workflow.execute_activity(
            QuoteParsingActivities.parse_quotes_and_summary,
            args=[content, author, title],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=llm_retry,
        )
        enrichment = await workflow.execute_activity(
            QuoteParsingActivities.enrich_with_web_search,
            args=[
                parsed["author"],
                parsed["title"],
                parsed["summary"],
                parsed["summary_short"],
            ],
            start_to_close_timeout=timedelta(minutes=2),
        )
        summary = enrichment.get("summary") or parsed["summary"]
        summary_short = enrichment.get("summary_short") or parsed["summary_short"]

        await workflow.execute_activity(
            QuoteParsingActivities.submit_quote_curation,
            args=[
                workflow_id,
                file_path,
                parsed["title"],
                parsed["author"],
                parsed["quotes"],
            ],
            start_to_close_timeout=timedelta(minutes=2),
        )
        approved = await workflow.execute_activity(
            QuoteParsingActivities.wait_for_quote_curation,
            args=[workflow_id],
            schedule_to_close_timeout=timedelta(days=7),
            heartbeat_timeout=timedelta(minutes=2),
        )

        if approved:
            result = await workflow.execute_activity(
                QuoteParsingActivities.write_quotes_to_graph,
                args=[
                    workflow_id,
                    approved,
                    parsed["author"],
                    parsed["title"],
                    summary,
                    summary_short,
                ],
                start_to_close_timeout=timedelta(minutes=10),
            )
            return {"workflow_id": workflow_id, "status": "completed", **result}
        return {"workflow_id": workflow_id, "status": "completed", "quotes_count": 0}
