"""Tool to query Temporal workflow status."""

import os

from langchain_core.tools import tool


def create_get_workflow_status_tool():
    """Create tool to get the status of a Temporal workflow by ID."""

    @tool
    async def get_workflow_status(workflow_id: str) -> str:
        """Get the status of a workflow by its ID (e.g. journal-2025-01-15-abc123, quote-abc123, concept-uuid, inbox-1234567890)."""
        try:
            from temporalio.client import Client
            from minerva_backend.processing.temporal_converter import (
                create_custom_data_converter,
            )

            uri = os.getenv("TEMPORAL_URI", "localhost:7233")
            client = await Client.connect(
                uri, data_converter=create_custom_data_converter()
            )
            handle = client.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            return (
                f"Workflow {workflow_id}: status={desc.status.name}, "
                f"run_id={desc.run_id}, start_time={desc.start_time}"
            )
        except ImportError as e:
            return f"Cannot query workflow: backend not available ({e})."
        except Exception as e:
            return f"Error getting workflow status: {e}"

    get_workflow_status.name = "get_workflow_status"
    return get_workflow_status
