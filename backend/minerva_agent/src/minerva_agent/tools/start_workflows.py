"""Workflow-launching tools that start Temporal workflows (require HITL confirmation in chat)."""

import os
from uuid import uuid4

from langchain_core.tools import tool


async def _get_temporal_client():
    """Lazy import and connect to Temporal. Uses TEMPORAL_URI env (default localhost:7233)."""
    from temporalio.client import Client
    from minerva_backend.processing.temporal_converter import create_custom_data_converter

    uri = os.getenv("TEMPORAL_URI", "localhost:7233")
    return await Client.connect(uri, data_converter=create_custom_data_converter())


async def _start_workflow(workflow_run_method, args: list, workflow_id: str) -> str:
    """Start a Temporal workflow and return the workflow ID."""
    client = await _get_temporal_client()
    await client.start_workflow(
        workflow_run_method,
        args=args,
        id=workflow_id,
        task_queue="minerva-pipeline",
    )
    return workflow_id


def create_start_quote_parsing_tool():
    """Create tool to start QuoteParsingWorkflow. Requires file_path, author, title."""

    @tool
    async def start_quote_parsing(file_path: str, author: str, title: str) -> str:
        """Start the quote parsing workflow for a markdown file. You must provide the file path (relative to the vault), author, and title. Requires user confirmation before running."""
        try:
            from minerva_backend.processing.quote_parsing_workflow import (
                QuoteParsingWorkflow,
            )
        except ImportError:
            return "Quote parsing workflow is not yet available. It will be available after the backend is updated."
        workflow_id = f"quote-{uuid4().hex[:12]}"
        await _start_workflow(
            QuoteParsingWorkflow.run,
            [{"file_path": file_path, "author": author, "title": title}],
            workflow_id,
        )
        return f"Started quote parsing workflow: {workflow_id}. You can check status with get_workflow_status."
    start_quote_parsing.name = "start_quote_parsing"
    return start_quote_parsing


def create_start_concept_extraction_tool():
    """Create tool to start ConceptExtractionWorkflow. Requires content_uuid."""

    @tool
    async def start_concept_extraction(content_uuid: str) -> str:
        """Start the concept extraction workflow for a content item (e.g. a book) that already has quotes in the graph. Provide the content UUID. Requires user confirmation before running."""
        try:
            from minerva_backend.processing.concept_extraction_workflow import (
                ConceptExtractionWorkflow,
            )
        except ImportError:
            return "Concept extraction workflow is not yet available. It will be available after the backend is updated."
        workflow_id = f"concept-{content_uuid}"
        await _start_workflow(
            ConceptExtractionWorkflow.run,
            [content_uuid],
            workflow_id,
        )
        return f"Started concept extraction workflow: {workflow_id}. You can check status with get_workflow_status."
    start_concept_extraction.name = "start_concept_extraction"
    return start_concept_extraction


def create_start_inbox_classification_tool():
    """Create tool to start InboxClassificationWorkflow. Optional inbox_path."""

    @tool
    async def start_inbox_classification(inbox_path: str = "01 - Inbox") -> str:
        """Start the inbox classification workflow to classify notes in the Obsidian inbox. Optionally provide the inbox folder path relative to the vault (default: 01 - Inbox). Requires user confirmation before running."""
        try:
            from minerva_backend.processing.inbox_classification_workflow import (
                InboxClassificationWorkflow,
            )
        except ImportError:
            return "Inbox classification workflow is not yet available. It will be available after the backend is updated."
        import time
        workflow_id = f"inbox-{int(time.time())}"
        await _start_workflow(
            InboxClassificationWorkflow.run,
            [inbox_path],
            workflow_id,
        )
        return f"Started inbox classification workflow: {workflow_id}. You can check status with get_workflow_status."
    start_inbox_classification.name = "start_inbox_classification"
    return start_inbox_classification
