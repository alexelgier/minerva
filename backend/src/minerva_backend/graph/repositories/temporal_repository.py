"""
Temporal Repository for Minerva
Handles time-based operations and the temporal hierarchy (Year -> Month -> Day).
"""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry

logger = logging.getLogger(__name__)


class TemporalRepository:
    """
    Repository for temporal operations and time tree management.
    Handles Year -> Month -> Day hierarchy and temporal relationships.
    """

    def __init__(self, connection: Neo4jConnection):
        """Initialize repository with database connection."""
        self.connection = connection

    def ensure_day_in_time_tree(self, target_date: date) -> str:
        """
        Ensure a day exists in the time tree hierarchy: Year -> Month -> Day.
        Creates Year, Month, and Day nodes if they don't exist and establishes relationships.
        All time nodes are created in the TEMPORAL partition.

        Args:
            target_date: The date to ensure exists in the tree

        Returns:
            str: UUID of the Day node
        """
        year = target_date.year
        month = target_date.month
        day = target_date.day
        month_name = target_date.strftime('%B')  # e.g., "September"

        query = """
        // Create or get Year node
        MERGE (y:Year {year: $year, partition: 'TEMPORAL'})
        ON CREATE SET 
            y.uuid = $year_uuid,
            y.name = $year,
            y.created_at = datetime()

        // Create or get Month node and link to Year
        MERGE (y)-[:HAS_MONTH]->(m:Month {
            year: $year, 
            month: $month, 
            partition: 'TEMPORAL'
        })
        ON CREATE SET 
            m.uuid = $month_uuid,
            m.created_at = datetime(),
            m.name = $month_name

        // Create or get Day node and link to Month
        MERGE (m)-[:HAS_DAY]->(d:Day {
            year: $year, 
            month: $month, 
            day: $day, 
            date: date($date_str),
            partition: 'TEMPORAL'
        })
        ON CREATE SET 
            d.uuid = $day_uuid,
            d.created_at = datetime()

        RETURN d.uuid as day_uuid
        """

        with self.connection.session() as session:
            result = session.run(
                query,
                year=year,
                month=month,
                day=day,
                month_name=month_name,
                date_str=target_date.isoformat(),
                year_uuid=str(uuid4()),
                month_uuid=str(uuid4()),
                day_uuid=str(uuid4())
            )

            record = result.single()
            day_uuid = record["day_uuid"]

            logger.info(f"Ensured day in time tree: {target_date} (UUID: {day_uuid})")
            return day_uuid

    def link_node_to_day(self, uuid: str, target_date: date) -> bool:
        """
        Link a node to day in the time tree.
        Args:
            uuid: UUID of the node
            target_date: Date to link to
        Returns:
            bool: True if link was created successfully
        """
        # First ensure the day exists
        day_uuid = self.ensure_day_in_time_tree(target_date)

        # Then create the relationship
        query = """
        MATCH (n {uuid: $uuid})
        MATCH (d:Day {uuid: $day_uuid})
        MERGE (j)-[:OCCURRED_ON]->(d)
        RETURN count(*) as linked
        """
        with self.connection.session() as session:
            try:
                result = session.run(query, uuid=uuid, day_uuid=day_uuid)
                record = result.single()
                success = record["linked"] > 0
                if success:
                    logger.info(f"Linked node {uuid} to day {target_date}")
                return success
            except Exception as e:
                logger.error(f"Error linking node to day: {e}")
                return False

    def link_nodes_to_day_batch(self, uuids: List[str], target_date: date) -> int:
        """
        Link multiple nodes to a day in the time tree in batch.

        Args:
            uuids: List of node UUIDs
            target_date: Date to link all nodes to

        Returns:
            int: Number of relationships created
        """
        if not uuids:
            return 0

        # First ensure the day exists
        day_uuid = self.ensure_day_in_time_tree(target_date)

        # Then create all relationships in batch
        query = """
        UNWIND $uuids as node_uuid
        MATCH (n {uuid: node_uuid})
        MATCH (d:Day {uuid: $day_uuid})
        MERGE (n)-[:OCCURRED_ON]->(d)
        RETURN count(*) as linked
        """

        with self.connection.session() as session:
            try:
                result = session.run(query, uuids=uuids, day_uuid=day_uuid)
                record = result.single()
                linked_count = record["linked"]

                if linked_count > 0:
                    logger.info(f"Linked {linked_count} nodes to day {target_date}")

                return linked_count

            except Exception as e:
                logger.error(f"Error linking nodes to day: {e}")
                return 0

    def get_day_uuid(self, target_date: date) -> Optional[str]:
        """
        Get the UUID of a day node if it exists.

        Args:
            target_date: Date to find

        Returns:
            UUID of day node or None if not found
        """
        query = """
        MATCH (d:Day {
            year: $year,
            month: $month, 
            day: $day,
            partition: 'TEMPORAL'
        })
        RETURN d.uuid as day_uuid
        """

        with self.connection.session() as session:
            result = session.run(
                query,
                year=target_date.year,
                month=target_date.month,
                day=target_date.day
            )

            record = result.single()
            return record["day_uuid"] if record else None

    def get_month_uuid(self, year: int, month: int) -> Optional[str]:
        """
        Get the UUID of a month node if it exists.

        Args:
            year: Year to find
            month: Month to find (1-12)

        Returns:
            UUID of month node or None if not found
        """
        query = """
        MATCH (m:Month {
            year: $year,
            month: $month,
            partition: 'TEMPORAL'
        })
        RETURN m.uuid as month_uuid
        """
        with self.connection.session() as session:
            result = session.run(
                query,
                year=year,
                month=month
            )
            record = result.single()
            return record["month_uuid"] if record else None

    def get_year_uuid(self, year: int) -> Optional[str]:
        """
        Get the UUID of a year node if it exists.

        Args:
            year: Year to find

        Returns:
            UUID of year node or None if not found
        """
        query = """
        MATCH (y:Year {
            year: $year,
            partition: 'TEMPORAL'
        })
        RETURN y.uuid as year_uuid
        """
        with self.connection.session() as session:
            result = session.run(query, year=year)
            record = result.single()
            return record["year_uuid"] if record else None

    def get_journal_entries_for_date(self, target_date: date) -> List[JournalEntry]:
        """
        Get all journal entries for a specific date.

        Args:
            target_date: Date to find entries for

        Returns:
            List of JournalEntry instances
        """
        query = """
        MATCH (j:JournalEntry)-[:OCCURRED_ON]->(d:Day {
            year: $year,
            month: $month,
            day: $day
        })
        RETURN j
        ORDER BY j.created_at ASC
        """

        with self.connection.session() as session:
            result = session.run(
                query,
                year=target_date.year,
                month=target_date.month,
                day=target_date.day
            )

            entries = []
            for record in result:
                properties = dict(record["j"])
                # Convert datetime strings back to datetime objects
                for key, value in properties.items():
                    if isinstance(value, str) and 'T' in value:
                        try:
                            properties[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            pass

                entries.append(JournalEntry(**properties))

            return entries

    def get_journal_entries_for_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        """
        Get all journal entries within a date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of JournalEntry instances
        """
        query = """
        MATCH (j:JournalEntry)-[:OCCURRED_ON]->(d:Day)
        WHERE d.date >= date($start_date) AND d.date <= date($end_date)
        RETURN j, d.date as entry_date
        ORDER BY d.date ASC, j.created_at ASC
        """

        with self.connection.session() as session:
            result = session.run(
                query,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )

            entries = []
            for record in result:
                properties = dict(record["j"])
                # Convert datetime strings back to datetime objects
                for key, value in properties.items():
                    if isinstance(value, str) and 'T' in value:
                        try:
                            properties[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except ValueError:
                            pass

                entries.append(JournalEntry(**properties))

            return entries

    def get_month_stats(self, year: int, month: int) -> Dict[str, Any]:
        """
        Get statistics for a specific month.

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Dictionary with month statistics
        """
        query = """
        MATCH (m:Month {year: $year, month: $month})-[:HAS_DAY]->(d:Day)
        OPTIONAL MATCH (j:JournalEntry)-[:OCCURRED_ON]->(d)
        RETURN 
            count(DISTINCT d) as days_in_month,
            count(DISTINCT j) as journal_entries,
            collect(DISTINCT d.date) as dates_with_days
        """

        with self.connection.session() as session:
            result = session.run(query, year=year, month=month)
            record = result.single()

            if record:
                return {
                    "year": year,
                    "month": month,
                    "days_created": record["days_in_month"],
                    "journal_entries": record["journal_entries"],
                    "dates_with_days": record["dates_with_days"]
                }

            return {
                "year": year,
                "month": month,
                "days_created": 0,
                "journal_entries": 0,
                "dates_with_days": []
            }

    def get_year_stats(self, year: int) -> Dict[str, Any]:
        """
        Get statistics for a specific year.

        Args:
            year: Year

        Returns:
            Dictionary with year statistics
        """
        query = """
        MATCH (y:Year {year: $year})-[:HAS_MONTH]->(m:Month)-[:HAS_DAY]->(d:Day)
        OPTIONAL MATCH (j:JournalEntry)-[:OCCURRED_ON]->(d)
        RETURN 
            count(DISTINCT m) as months_in_year,
            count(DISTINCT d) as days_in_year,
            count(DISTINCT j) as journal_entries,
            min(d.date) as earliest_date,
            max(d.date) as latest_date
        """

        with self.connection.session() as session:
            result = session.run(query, year=year)
            record = result.single()

            if record:
                return {
                    "year": year,
                    "months_created": record["months_in_year"],
                    "days_created": record["days_in_year"],
                    "journal_entries": record["journal_entries"],
                    "earliest_date": record["earliest_date"],
                    "latest_date": record["latest_date"]
                }

            return {
                "year": year,
                "months_created": 0,
                "days_created": 0,
                "journal_entries": 0,
                "earliest_date": None,
                "latest_date": None
            }

    def get_temporal_overview(self) -> Dict[str, Any]:
        """
        Get overview of entire temporal structure.

        Returns:
            Dictionary with temporal statistics
        """
        query = """
        MATCH (y:Year)
        OPTIONAL MATCH (y)-[:HAS_MONTH]->(m:Month)
        OPTIONAL MATCH (m)-[:HAS_DAY]->(d:Day)
        OPTIONAL MATCH (j:JournalEntry)-[:OCCURRED_ON]->(d)
        RETURN 
            count(DISTINCT y) as total_years,
            count(DISTINCT m) as total_months,
            count(DISTINCT d) as total_days,
            count(DISTINCT j) as total_journal_entries,
            min(y.year) as earliest_year,
            max(y.year) as latest_year
        """

        with self.connection.session() as session:
            result = session.run(query)
            record = result.single()

            if record:
                return {
                    "total_years": record["total_years"],
                    "total_months": record["total_months"],
                    "total_days": record["total_days"],
                    "total_journal_entries": record["total_journal_entries"],
                    "earliest_year": record["earliest_year"],
                    "latest_year": record["latest_year"]
                }

            return {
                "total_years": 0,
                "total_months": 0,
                "total_days": 0,
                "total_journal_entries": 0,
                "earliest_year": None,
                "latest_year": None
            }
