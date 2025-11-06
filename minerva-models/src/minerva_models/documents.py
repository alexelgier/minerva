from __future__ import annotations

import re
from datetime import date
from datetime import date as date_type
from datetime import datetime, time, timedelta
from typing import Any, List, Literal
from uuid import uuid4

from pydantic import Field, field_serializer

from .base import Document, LexicalType


class JournalEntry(Document):
    date: date_type = Field(..., description="Fecha de la entrada del diario")
    type: Literal[LexicalType.JOURNAL_ENTRY] = Field(
        default=LexicalType.JOURNAL_ENTRY,
        description="Tipo de documento (siempre JOURNAL_ENTRY)",
    )
    entry_text: str | None = Field(
        default=None, description="El texto principal de la entrada del diario"
    )
    panas_pos: List[float] | None = Field(
        default=None, description="Puntuaciones positivas PANAS"
    )
    panas_neg: List[float] | None = Field(
        default=None, description="Puntuaciones negativas PANAS"
    )
    bpns: List[float] | None = Field(default=None, description="Puntuaciones BPNS")
    flourishing: List[float] | None = Field(
        default=None, description="Puntuaciones de florecimiento"
    )
    wake: datetime | None = Field(default=None, description="Fecha y hora de despertar")
    sleep: datetime | None = Field(default=None, description="Fecha y hora de dormir")

    @field_serializer("date")
    def serialize_date(self, value: date_type) -> str:
        """Serialize date field to ISO format string."""
        return value.isoformat()

    @field_serializer("wake", "sleep")
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """Serialize datetime fields to ISO format string."""
        if value is None:
            return None
        return value.isoformat()

    @classmethod
    def from_text(cls, text: str, journal_date: str) -> JournalEntry:
        """Parse journal entry from text and return a JournalEntry object."""
        journal_entry = {}

        # Parse different sections
        journal_entry.update(cls._parse_panas_positive(text))
        journal_entry.update(cls._parse_panas_negative(text))
        journal_entry.update(cls._parse_bpns(text))
        journal_entry.update(cls._parse_flourishing(text))
        journal_entry.update(cls._parse_date(journal_date))
        journal_entry.update(
            cls._parse_wake_sleep(text, journal_entry.get("date") or date.today())
        )
        journal_entry.update(cls._parse_narration(text))

        return cls(
            uuid=journal_date,
            date=journal_entry["date"],
            text=text,
            type=LexicalType.JOURNAL_ENTRY,
            entry_text=journal_entry.get("text"),
            panas_pos=journal_entry.get("panas_pos"),
            panas_neg=journal_entry.get("panas_neg"),
            bpns=journal_entry.get("bpns"),
            flourishing=journal_entry.get("flourishing"),
            wake=journal_entry.get("wake"),
            sleep=journal_entry.get("sleep"),
        )

    @classmethod
    def _parse_panas_positive(cls, text: str) -> dict:
        """Parse PANAS positive affect scores from text."""
        panas_pos_match = re.search(
            r"## PANAS.*?Positive Affect.*?"
            r"Interested::\s*(\d+).*?"
            r"Excited::\s*(\d+).*?"
            r"Strong::\s*(\d+).*?"
            r"Enthusiastic::\s*(\d+).*?"
            r"Proud::\s*(\d+).*?"
            r"Alert::\s*(\d+).*?"
            r"Inspired::\s*(\d+).*?"
            r"Determined::\s*(\d+).*?"
            r"Attentive::\s*(\d+).*?"
            r"Active::\s*(\d+)",
            text,
            re.DOTALL,
        )
        if panas_pos_match:
            return {"panas_pos": [int(val) for val in panas_pos_match.groups()]}
        return {}

    @classmethod
    def _parse_panas_negative(cls, text: str) -> dict:
        """Parse PANAS negative affect scores from text."""
        panas_neg_match = re.search(
            r"Negative Affect.*?"
            r"Distressed::\s*(\d+).*?"
            r"Upset::\s*(\d+).*?"
            r"Guilty::\s*(\d+).*?"
            r"Scared::\s*(\d+).*?"
            r"Hostile::\s*(\d+).*?"
            r"Irritable::\s*(\d+).*?"
            r"Ashamed::\s*(\d+).*?"
            r"Nervous::\s*(\d+).*?"
            r"Jittery::\s*(\d+).*?"
            r"Afraid::\s*(\d+)",
            text,
            re.DOTALL,
        )
        if panas_neg_match:
            return {"panas_neg": [int(val) for val in panas_neg_match.groups()]}
        return {}

    @classmethod
    def _parse_bpns(cls, text: str) -> dict:
        """Parse BPNS scores from text."""
        bpns_match = re.search(
            r"## BPNS.*?"
            r"Autonomy.*?"
            r"I feel like I can make choices about the things I do::\s*(\d+).*?"
            r"I feel free to decide how I do my daily tasks::\s*(\d+).*?"
            r"Competence.*?"
            r"I feel capable at the things I do::\s*(\d+).*?"
            r"I can successfully complete challenging tasks::\s*(\d+).*?"
            r"Relatedness.*?"
            r"I feel close and connected with the people around me::"
            r"\s*(\d+).*?I get along well with the people I interact with daily::"
            r"\s*(\d+).*?I feel supported by others in my life::\s*(\d+)",
            text,
            re.DOTALL,
        )
        if bpns_match:
            return {"bpns": [int(val) for val in bpns_match.groups()]}
        return {}

    @classmethod
    def _parse_flourishing(cls, text: str) -> dict:
        """Parse Flourishing Scale scores from text."""
        flour_match = re.search(
            r"## Flourishing Scale.*?I lead a purposeful and meaningful life::\s*(\d+).*?"
            r"My social relationships are supportive and rewarding::\s*(\d+).*?"
            r"I am engaged and interested in my daily activities::\s*(\d+).*?"
            r"I actively contribute to the happiness and well-being of others::\s*(\d+).*?"
            r"I am competent and capable in the activities that are important to me::\s*(\d+).*?"
            r"I am a good person and live a good life::\s*(\d+).*?"
            r"I am optimistic about my future::\s*(\d+).*?"
            r"People respect me::\s*(\d+)",
            text,
            re.DOTALL,
        )
        if flour_match:
            return {"flourishing": [int(val) for val in flour_match.groups()]}
        return {}

    @classmethod
    def _parse_date(cls, journal_date: str) -> dict:
        """Parse date from journal date string."""
        journal_date_parts = journal_date.split("-")
        base_date = date_type(
            int(journal_date_parts[0]),
            int(journal_date_parts[1]),
            int(journal_date_parts[2]),
        )
        return {"date": base_date}

    @classmethod
    def _parse_wake_sleep(cls, text: str, base_date: date_type) -> dict:
        """Parse wake and sleep times from text."""
        wake_bed_match = re.search(
            r"Wake time:\s*(\d\d:?\d\d).*?Bedtime:\s*(\d\d:?\d\d)", text, re.DOTALL
        )
        if not wake_bed_match:
            return {}

        wake_time_str = "".join(wake_bed_match.groups()[0].split(":"))
        sleep_time_str = "".join(wake_bed_match.groups()[1].split(":"))

        wake_time = time(int(wake_time_str[:2]), int(wake_time_str[2:]))
        sleep_time = time(int(sleep_time_str[:2]), int(sleep_time_str[2:]))

        wake_datetime = datetime.combine(base_date, wake_time)
        sleep_datetime = datetime.combine(
            base_date + timedelta(days=1) if sleep_time < wake_time else base_date,
            sleep_time,
        )

        return {"wake": wake_datetime, "sleep": sleep_datetime}

    @classmethod
    def _parse_narration(cls, text: str) -> dict:
        """Parse main narration text from journal entry."""
        journal_text = re.search(
            r"(.+?)(?=\n*---\n*-\s*Imagen, Detalle:|\n*---.*## Noticias|\n*---.*## Sleep)",
            text,
            re.DOTALL,
        )
        if journal_text:
            return {"text": journal_text.group(0)}
        return {}


class Span(Document):
    """A span of text in a document."""

    type: Literal[LexicalType.SPAN] = LexicalType.SPAN
    start: int = Field(..., description="Character start index in the Document text")
    end: int = Field(..., description="Character end index (exclusive)")
    text: str = Field(..., description="The exact substring from the entry text")


class Chunk(Document):
    """A chunk of text in a document."""

    type: Literal[LexicalType.CHUNK] = LexicalType.CHUNK

    def __init__(self, text: str, uuid: str = None, **kwargs) -> None:
        super().__init__(uuid=uuid if uuid else str(uuid4()), text=text, **kwargs)

class Quote(Document):
    type: Literal[LexicalType.QUOTE] = LexicalType.QUOTE
    text: str
    section: str
    page_reference: str | None
    embedding: list[float] | None = Field(
        default=None, description="Embedding of the quote text for semantic search"
    )

