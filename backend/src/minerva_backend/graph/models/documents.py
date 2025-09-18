from __future__ import annotations

import re
from datetime import datetime, time, timedelta
from datetime import date as date_type
from typing import List, Literal, Any
from uuid import uuid4

from pydantic import Field

from .base import Document, LexicalType


class JournalEntry(Document):
    date: date_type = Field(..., description="Fecha de la entrada del diario")
    type: Literal[LexicalType.JOURNAL_ENTRY] = Field(LexicalType.JOURNAL_ENTRY.value,
                                                     description="Tipo de documento (siempre JOURNAL_ENTRY)")
    entry_text: str | None = Field(default=None, description="El texto principal de la entrada del diario")
    panas_pos: List[float] | None = Field(default=None, description="Puntuaciones positivas PANAS")
    panas_neg: List[float] | None = Field(default=None, description="Puntuaciones negativas PANAS")
    bpns: List[float] | None = Field(default=None, description="Puntuaciones BPNS")
    flourishing: List[float] | None = Field(default=None, description="Puntuaciones de florecimiento")
    wake: datetime | None = Field(default=None, description="Fecha y hora de despertar")
    sleep: datetime | None = Field(default=None, description="Fecha y hora de dormir")

    @classmethod
    def from_text(cls, text: str, journal_date: str) -> JournalEntry:
        """Parse journal entry from text and return a JournalEntry object."""
        journal_entry = {}

        # PANAS Positive
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
            text, re.DOTALL)
        if panas_pos_match:
            journal_entry['panas_pos'] = [int(val) for val in panas_pos_match.groups()]

        # PANAS Negative
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
            text, re.DOTALL)
        if panas_neg_match:
            journal_entry['panas_neg'] = [int(val) for val in panas_neg_match.groups()]

        # BPNS
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
            text, re.DOTALL)
        if bpns_match:
            journal_entry['bpns'] = [int(val) for val in bpns_match.groups()]

        # Flourishing
        flour_match = re.search(
            r"## Flourishing Scale.*?I lead a purposeful and meaningful life::\s*(\d+).*?"
            r"My social relationships are supportive and rewarding::\s*(\d+).*?"
            r"I am engaged and interested in my daily activities::\s*(\d+).*?"
            r"I actively contribute to the happiness and well-being of others::\s*(\d+).*?"
            r"I am competent and capable in the activities that are important to me::\s*(\d+).*?"
            r"I am a good person and live a good life::\s*(\d+).*?"
            r"I am optimistic about my future::\s*(\d+).*?"
            r"People respect me::\s*(\d+)",
            text, re.DOTALL)
        if flour_match:
            journal_entry['flourishing'] = [int(val) for val in flour_match.groups()]

        # Date
        journal_date_str = journal_date
        journal_date = journal_date.split("-")
        base_date = date_type(int(journal_date[0]), int(journal_date[1]), int(journal_date[2]))
        journal_entry['date'] = base_date

        # Wake / Bed
        wake_bed_match = re.search(
            r"Wake time:\s*(\d\d:?\d\d).*?Bedtime:\s*(\d\d:?\d\d)",
            text, re.DOTALL)
        if wake_bed_match:
            wake = "".join(wake_bed_match.groups()[0].split(":"))
            wake = time(int(wake[:2]), int(wake[2:]))
            sleep = "".join(wake_bed_match.groups()[1].split(":"))
            sleep = time(int(sleep[:2]), int(sleep[2:]))
            journal_entry['wake'] = datetime.combine(journal_entry['date'], wake)
            journal_entry['sleep'] = datetime.combine(base_date + timedelta(days=1) if sleep < wake else base_date,
                                                      sleep)

        # Narration
        journal_text = re.search(
            r"(.+?)(?=\n*---\n*-\s*Imagen, Detalle:|\n*---.*## Noticias|\n*---.*## Sleep)",
            text, re.DOTALL)
        if journal_text:
            journal_entry['text'] = journal_text.group(0)

        return cls(
            id=journal_date_str,
            date=journal_entry['date'],
            text=text,
            entry_text=journal_entry['text'] if 'text' in journal_entry else None,
            panas_pos=journal_entry.get('panas_pos'),
            panas_neg=journal_entry.get('panas_neg'),
            bpns=journal_entry.get('bpns'),
            flourishing=journal_entry.get('flourishing'),
            wake=journal_entry.get('wake'),
            sleep=journal_entry.get('sleep'),
        )


class Span(Document):
    """A span of text in a document."""
    type: Literal[LexicalType.SPAN] = LexicalType.SPAN.value
    start: int = Field(..., description="Character start index in the Document text")
    end: int = Field(..., description="Character end index (exclusive)")
    text: str = Field(..., description="The exact substring from the entry text")


class Chunk(Document):
    """A chunk of text in a document."""
    type: Literal[LexicalType.CHUNK] = LexicalType.CHUNK.value

    def __init__(self, text: str, uuid: str = None, **kwargs) -> None:
        super().__init__(uuid=uuid if uuid else str(uuid4()), text=text, **kwargs)
