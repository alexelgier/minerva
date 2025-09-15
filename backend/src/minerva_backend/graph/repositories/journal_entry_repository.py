"""
JournalEntry Repository for Minerva
Handles all JournalEntry document database operations.
"""
from datetime import date
from typing import List, Optional

from .base import BaseRepository
from ..models.documents import JournalEntry
from ..models.enums import LexicalType


class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for JournalEntry documents with specialized operations."""

    @property
    def entity_label(self) -> str:
        return LexicalType.JOURNAL_ENTRY.value

    @property
    def entity_class(self) -> type[JournalEntry]:
        return JournalEntry

    def find_by_date(self, entry_date: date) -> Optional[JournalEntry]:
        """
        Find a journal entry by its exact date.

        Args:
            entry_date: The date of the journal entry.

        Returns:
            A JournalEntry document if found, otherwise None.
        """
        query = """
        MATCH (j:JournalEntry {date: $entry_date})
        RETURN j
        LIMIT 1
        """
        with self.connection.session() as session:
            result = session.run(query, entry_date=entry_date)
            record = result.single()
            if record:
                properties = dict(record["j"])
                return self._properties_to_entity(properties)
            return None

    def find_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        """
        Find all journal entries within a specific date range.

        Args:
            start_date: The start of the date range.
            end_date: The end of the date range.

        Returns:
            A list of JournalEntry documents within the date range.
        """
        query = """
        MATCH (j:JournalEntry)
        WHERE j.date >= $start_date AND j.date <= $end_date
        RETURN j
        ORDER BY j.date ASC
        """
        with self.connection.session() as session:
            result = session.run(query, start_date=start_date, end_date=end_date)
            entries = []
            for record in result:
                properties = dict(record["j"])
                entries.append(self._properties_to_entity(properties))
            return entries

    def get_statistics(self) -> dict:
        """
        Get statistics about journal entries in the database.

        Returns:
            Dictionary with journal entry statistics.
        """
        query = """
        MATCH (j:JournalEntry)
        RETURN
            count(j) as total_entries,
            min(j.date) as oldest_entry_date,
            max(j.date) as newest_entry_date
        """
        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record and record["total_entries"] > 0:
                oldest_date = record["oldest_entry_date"]
                newest_date = record["newest_entry_date"]
                return {
                    "total_entries": record["total_entries"],
                    "oldest_entry_date": date(oldest_date.year, oldest_date.month, oldest_date.day) if oldest_date else None,
                    "newest_entry_date": date(newest_date.year, newest_date.month, newest_date.day) if newest_date else None,
                }

            return {
                "total_entries": 0,
                "oldest_entry_date": None,
                "newest_entry_date": None,
            }
