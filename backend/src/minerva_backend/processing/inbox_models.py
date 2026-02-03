"""Pydantic models for InboxClassificationWorkflow."""

from typing import List

from pydantic import BaseModel, ConfigDict


class InboxFile(BaseModel):
    """A file in the inbox to be classified."""

    source_path: str  # relative to vault, e.g. "01 - Inbox/note.md"
    note_title: str = ""


class ClassificationSuggestion(BaseModel):
    """LLM suggestion for where to move a note."""

    uuid: str
    source_path: str
    target_folder: str  # e.g. "03 - Projects/ProjectX"
    note_title: str
    reason: str = ""


class ApprovedMove(BaseModel):
    """Approved move: source_path -> target_folder."""

    uuid: str
    source_path: str
    target_folder: str

    model_config = ConfigDict(arbitrary_types_allowed=True)
