def ensure_day_in_time_tree(self, tx: Transaction, target_date: date) -> str:
    """
        Ensure a day exists in the time tree hierarchy: Year -> Month -> Day
        Creates Year, Month, and Day nodes if they don't exist and establishes relationships.
        All time nodes are created in the TEMPORAL partition.

        Args:
            tx: Neo4j transaction
            target_date: The date to ensure exists in the tree

        Returns:
            str: UUID of the Day node
        """
    year = target_date.year
    month = target_date.month
    day = target_date.day
    month_name = target_date.strftime('%B')  # e.g., "September"

    result = tx.run("""
            // Create or get Year node
            MERGE (y:Year {year: $year, partition: 'TEMPORAL'})
            ON CREATE SET 
                y.uuid = randomUUID(),
                y.created_at = datetime()

            // Create or get Month node and link to Year
            MERGE (y)-[:HAS_MONTH]->(m:Month {
                year: $year, 
                month: $month, 
                partition: 'TEMPORAL'
            })
            ON CREATE SET 
                m.uuid = randomUUID(),
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
                d.uuid = randomUUID(),
                d.created_at = datetime()

            RETURN d.uuid as day_uuid
        """,
                    year=year,
                    month=month,
                    day=day,
                    month_name=month_name,
                    date_str=target_date.isoformat()
                    )

    return result.single()["day_uuid"]