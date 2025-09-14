from __future__ import annotations

from datetime import date, datetime
from typing import List, Literal

from pydantic import Field

from .base import Document
from .enums import DocumentType


class JournalEntry(Document):
    date: date = Field(..., description="Fecha de la entrada del diario")
    type: Literal[DocumentType.JOURNAL_ENTRY] = Field(DocumentType.JOURNAL_ENTRY.value,
                                                      description="Tipo de documento (siempre JOURNAL_ENTRY)")
    entry_text: str | None = Field(default=None, description="El texto principal de la entrada del diario")
    panas_pos: List[float] | None = Field(default=None, description="Puntuaciones positivas PANAS")
    panas_neg: List[float] | None = Field(default=None, description="Puntuaciones negativas PANAS")
    bpns: List[float] | None = Field(default=None, description="Puntuaciones BPNS")
    flourishing: List[float] | None = Field(default=None, description="Puntuaciones de florecimiento")
    wake: datetime | None = Field(default=None, description="Fecha y hora de despertar")
    sleep: datetime | None = Field(default=None, description="Fecha y hora de dormir")
