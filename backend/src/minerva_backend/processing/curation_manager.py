import json
from typing import List, Dict, Any, Optional

import aiosqlite

from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.relations import Relation


class CurationManager:
    """Manages the human-in-the-loop curation queue using SQLite"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS journal_curation (
                    journal_id TEXT PRIMARY KEY,
                    journal_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    overall_status TEXT DEFAULT 'PENDING_ENTITIES'
                    -- PENDING_ENTITIES, ENTITIES_DONE, PENDING_RELATIONS, COMPLETED
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS entity_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_id TEXT,
                    entity_type TEXT,
                    original_data_json TEXT,  -- NULL for user-added entities
                    curated_data_json TEXT,   -- Always present for ACCEPTED
                    status TEXT DEFAULT 'PENDING',  -- PENDING, ACCEPTED, REJECTED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_added BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (journal_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS relationship_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_id TEXT,
                    relationship_type TEXT,
                    original_data_json TEXT,  -- NULL for user-added
                    curated_data_json TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_added BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (journal_id)
                )
            """)

            # Indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_journal_curation_status_date 
                ON journal_curation (overall_status, created_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_items_journal_status 
                ON entity_curation_items (journal_id, status)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationship_items_journal_status 
                ON relationship_curation_items (journal_id, status)
            """)

            await db.commit()

    # ===== JOURNAL MANAGEMENT =====

    async def create_journal_for_curation(self, journal_id: str, journal_text: str) -> None:
        """Create a new journal entry for curation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO journal_curation 
                (journal_id, journal_text, overall_status) 
                VALUES (?, ?, 'PENDING_ENTITIES')
            """, (journal_id, journal_text))
            await db.commit()

    async def get_journal_status(self, journal_id: str) -> Optional[str]:
        """Get the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT overall_status 
                FROM journal_curation 
                WHERE journal_id = ?
            """, (journal_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def update_journal_status(self, journal_id: str, status: str) -> None:
        """Update the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE journal_curation 
                SET overall_status = ? 
                WHERE journal_id = ?
            """, (status, journal_id))
            await db.commit()

    # ===== ENTITY CURATION =====

    async def queue_entities_for_curation(self, journal_id: str, journal_text: str, entities: List[Entity]) -> None:
        """Add entities to curation queue"""
        # First ensure journal exists
        await self.create_journal_for_curation(journal_id, journal_text)

        async with aiosqlite.connect(self.db_path) as db:
            for entity in entities:
                await db.execute("""
                    INSERT INTO entity_curation_items 
                    (journal_id, entity_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, 'PENDING', FALSE)
                """, (journal_id, entity.get_type(), json.dumps(entity.dict())))
            await db.commit()

    async def get_entities_for_journal(self, journal_id: str) -> List[Dict[str, Any]]:
        """Get all entities for a journal (for curation interface)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, entity_type, original_data_json, curated_data_json, status, is_user_added
                FROM entity_curation_items 
                WHERE journal_id = ? 
                ORDER BY created_at ASC
            """, (journal_id,)) as cursor:
                rows = await cursor.fetchall()

                entities = []
                for row in rows:
                    entity_data = {
                        "id": row[0],
                        "entity_type": row[1],
                        "status": row[4],
                        "is_user_added": bool(row[5])
                    }

                    # Use curated data if available, otherwise original
                    if row[3]:  # curated_data_json
                        entity_data.update(json.loads(row[3]))
                    elif row[2]:  # original_data_json
                        entity_data.update(json.loads(row[2]))

                    entities.append(entity_data)

                return entities

    async def get_pending_entities_for_journal(self, journal_id: str) -> List[Dict[str, Any]]:
        """Get only pending entities for a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, entity_type, original_data_json, status
                FROM entity_curation_items 
                WHERE journal_id = ? AND status = 'PENDING'
                ORDER BY created_at ASC
            """, (journal_id,)) as cursor:
                rows = await cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "entity_type": row[1],
                        "status": row[3],
                        **json.loads(row[2])
                    }
                    for row in rows
                ]

    async def accept_entity(self, entity_id: int, curated_data: Dict[str, Any]) -> bool:
        """Accept an entity with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE entity_curation_items 
                SET curated_data_json = ?, status = 'ACCEPTED'
                WHERE id = ? AND status = 'PENDING'
            """, (json.dumps(curated_data), entity_id))
            await db.commit()
            return cursor.rowcount > 0

    async def reject_entity(self, entity_id: int) -> bool:
        """Reject an entity"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE entity_curation_items 
                SET status = 'REJECTED'
                WHERE id = ? AND status = 'PENDING'
            """, (entity_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def add_user_entity(self, journal_id: str, entity_data: Dict[str, Any]) -> int:
        """Add a new user-created entity (auto-accepted)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO entity_curation_items 
                (journal_id, entity_type, curated_data_json, status, is_user_added) 
                VALUES (?, ?, ?, 'ACCEPTED', TRUE)
            """, (journal_id, entity_data.get('type', 'UNKNOWN'), json.dumps(entity_data)))
            await db.commit()
            return cursor.lastrowid

    async def get_accepted_entities_for_journal(self, journal_id: str) -> List[Dict[str, Any]]:
        """Get all accepted entities for a journal (for relationship extraction)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT curated_data_json
                FROM entity_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """, (journal_id,)) as cursor:
                rows = await cursor.fetchall()
                return [json.loads(row[0]) for row in rows]

    async def complete_entity_phase(self, journal_id: str) -> None:
        """Mark entity curation phase as complete and move to relationship phase"""
        await self.update_journal_status(journal_id, 'ENTITIES_DONE')

    # ===== RELATIONSHIP CURATION =====

    async def queue_relationships_for_curation(self, journal_id: str, relationships: List[Relation]) -> None:
        """Add relationships to curation queue"""
        await self.update_journal_status(journal_id, 'PENDING_RELATIONS')

        async with aiosqlite.connect(self.db_path) as db:
            for relationship in relationships:
                await db.execute("""
                    INSERT INTO relationship_curation_items 
                    (journal_id, relationship_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, 'PENDING', FALSE)
                """, (journal_id, relationship.get_type(), json.dumps(relationship.dict())))
            await db.commit()

    async def get_relationships_for_journal(self, journal_id: str) -> List[Dict[str, Any]]:
        """Get all relationships for a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT id, relationship_type, original_data_json, curated_data_json, status, is_user_added
                FROM relationship_curation_items 
                WHERE journal_id = ? 
                ORDER BY created_at ASC
            """, (journal_id,)) as cursor:
                rows = await cursor.fetchall()

                relationships = []
                for row in rows:
                    rel_data = {
                        "id": row[0],
                        "relationship_type": row[1],
                        "status": row[4],
                        "is_user_added": bool(row[5])
                    }

                    # Use curated data if available, otherwise original
                    if row[3]:  # curated_data_json
                        rel_data.update(json.loads(row[3]))
                    elif row[2]:  # original_data_json
                        rel_data.update(json.loads(row[2]))

                    relationships.append(rel_data)

                return relationships

    async def accept_relationship(self, relationship_id: int, curated_data: Dict[str, Any]) -> bool:
        """Accept a relationship with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE relationship_curation_items 
                SET curated_data_json = ?, status = 'ACCEPTED'
                WHERE id = ? AND status = 'PENDING'
            """, (json.dumps(curated_data), relationship_id))
            await db.commit()
            return cursor.rowcount > 0

    async def reject_relationship(self, relationship_id: int) -> bool:
        """Reject a relationship"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE relationship_curation_items 
                SET status = 'REJECTED'
                WHERE id = ? AND status = 'PENDING'
            """, (relationship_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def add_user_relationship(self, journal_id: str, relationship_data: Dict[str, Any]) -> int:
        """Add a new user-created relationship (auto-accepted)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO relationship_curation_items 
                (journal_id, relationship_type, curated_data_json, status, is_user_added) 
                VALUES (?, ?, ?, 'ACCEPTED', TRUE)
            """, (journal_id, relationship_data.get('type', 'UNKNOWN'), json.dumps(relationship_data)))
            await db.commit()
            return cursor.lastrowid

    async def get_accepted_relationships_for_journal(self, journal_id: str) -> List[Dict[str, Any]]:
        """Get all accepted relationships for a journal (for graph integration)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT curated_data_json
                FROM relationship_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """, (journal_id,)) as cursor:
                rows = await cursor.fetchall()
                return [json.loads(row[0]) for row in rows]

    async def complete_relationship_phase(self, journal_id: str) -> None:
        """Mark relationship curation phase as complete"""
        await self.update_journal_status(journal_id, 'COMPLETED')

    # ===== DASHBOARD API HELPERS =====

    async def get_journals_pending_entity_curation(self) -> List[Dict[str, Any]]:
        """Get journals that need entity curation"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT j.journal_id, j.journal_text, j.created_at,
                       COUNT(e.id) as pending_entities
                FROM journal_curation j
                LEFT JOIN entity_curation_items e ON j.journal_id = e.journal_id AND e.status = 'PENDING'
                WHERE j.overall_status = 'PENDING_ENTITIES'
                GROUP BY j.journal_id, j.journal_text, j.created_at
                ORDER BY j.created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()

                return [
                    {
                        "journal_id": row[0],
                        "journal_text": row[1],
                        "created_at": row[2],
                        "pending_entities": row[3],
                        "phase": "entities"
                    }
                    for row in rows
                ]

    async def get_journals_pending_relationship_curation(self) -> List[Dict[str, Any]]:
        """Get journals that need relationship curation"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT j.journal_id, j.journal_text, j.created_at,
                       COUNT(r.id) as pending_relationships
                FROM journal_curation j
                LEFT JOIN relationship_curation_items r ON j.journal_id = r.journal_id AND r.status = 'PENDING'
                WHERE j.overall_status = 'PENDING_RELATIONS'
                GROUP BY j.journal_id, j.journal_text, j.created_at
                ORDER BY j.created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()

                return [
                    {
                        "journal_id": row[0],
                        "journal_text": row[1],
                        "created_at": row[2],
                        "pending_relationships": row[3],
                        "phase": "relationships"
                    }
                    for row in rows
                ]

    async def get_all_pending_curation_tasks(self) -> Dict[str, Any]:
        """Get all pending curation tasks for the dashboard"""
        entity_journals = await self.get_journals_pending_entity_curation()
        relationship_journals = await self.get_journals_pending_relationship_curation()

        return {
            "entity_journals": entity_journals,
            "relationship_journals": relationship_journals,
            "total_pending_journals": len(entity_journals) + len(relationship_journals)
        }

    async def get_curation_stats(self) -> Dict[str, int]:
        """Get comprehensive curation statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Journal stats
            async with db.execute("""
                SELECT overall_status, COUNT(*) 
                FROM journal_curation 
                GROUP BY overall_status
            """) as cursor:
                journal_stats = dict(await cursor.fetchall())

            # Entity stats
            async with db.execute("""
                SELECT status, COUNT(*) 
                FROM entity_curation_items 
                GROUP BY status
            """) as cursor:
                entity_stats = dict(await cursor.fetchall())

            # Relationship stats
            async with db.execute("""
                SELECT status, COUNT(*) 
                FROM relationship_curation_items 
                GROUP BY status
            """) as cursor:
                relationship_stats = dict(await cursor.fetchall())

            return {
                "journals_pending_entities": journal_stats.get("PENDING_ENTITIES", 0),
                "journals_entities_done": journal_stats.get("ENTITIES_DONE", 0),
                "journals_pending_relations": journal_stats.get("PENDING_RELATIONS", 0),
                "journals_completed": journal_stats.get("COMPLETED", 0),
                "entities_pending": entity_stats.get("PENDING", 0),
                "entities_accepted": entity_stats.get("ACCEPTED", 0),
                "entities_rejected": entity_stats.get("REJECTED", 0),
                "relationships_pending": relationship_stats.get("PENDING", 0),
                "relationships_accepted": relationship_stats.get("ACCEPTED", 0),
                "relationships_rejected": relationship_stats.get("REJECTED", 0)
            }