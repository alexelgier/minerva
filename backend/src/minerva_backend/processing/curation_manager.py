# pipeline/curation_manager.py
import asyncio
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
import aiosqlite

from minerva_backend.graph.models.entities import Entity
from minerva_backend.graph.models.enums import EntityType
from minerva_backend.graph.models.relations import Relation


class CurationManager:
    """Manages the human-in-the-loop curation queue using SQLite"""

    def __init__(self, db_path: str = "curation.db"):
        self.db_path = db_path

    async def initialize(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS entity_curation (
                    journal_id TEXT,
                    journal_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    entities_json TEXT,
                    curated_entities_json TEXT NULL,
                    status TEXT DEFAULT 'PENDING',  -- PENDING, IN_PROGRESS, COMPLETED
                    PRIMARY KEY (journal_id)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS relationship_curation (
                    journal_id TEXT,
                    journal_text TEXT,
                    entities_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    relationships_json TEXT,
                    curated_relationships_json TEXT NULL,
                    status TEXT DEFAULT 'PENDING',
                    PRIMARY KEY (journal_id)
                )
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_entity_curation_status_date 
                ON entity_curation (status, created_at)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationship_curation_status_date 
                ON relationship_curation (status, created_at)
            """)

            await db.commit()

    # ===== ENTITY CURATION =====

    async def queue_entity_curation(self, journal_id: str, journal_text: str, entities: List[Entity]) -> None:
        """Add entities to curation queue"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO entity_curation 
                (journal_id, journal_text, entities_json, status) 
                VALUES (?, ?, ?, 'PENDING')
            """, (journal_id, journal_text, json.dumps(entities)))
            await db.commit()

    async def get_entity_curation_result(self, journal_id: str) -> List[Entity] | None:
        """Check if entity curation is complete, return curated entities if done"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT curated_entities_json, status 
                FROM entity_curation 
                WHERE journal_id = ?
            """, (journal_id,)) as cursor:
                row = await cursor.fetchone()

                if row and row[1] == 'COMPLETED':
                    return json.loads(row[0])
                return None

    async def get_pending_entity_curation(self) -> List[Dict[str, Any]]:
        """Get all pending entity curation tasks, oldest first"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT journal_id, journal_text, entities_json, created_at, status
                FROM entity_curation 
                WHERE status IN ('PENDING', 'IN_PROGRESS')
                ORDER BY created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()

                return [
                    {
                        "journal_id": row[0],
                        "journal_text": row[1],
                        "entities": json.loads(row[2]),
                        "created_at": row[3],
                        "status": row[4]
                    }
                    for row in rows
                ]

    async def mark_entity_curation_in_progress(self, journal_id: str) -> bool:
        """Mark entity curation as being worked on"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE entity_curation 
                SET status = 'IN_PROGRESS' 
                WHERE journal_id = ? AND status = 'PENDING'
            """, (journal_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def complete_entity_curation(self, journal_id: str, curated_entities: List[Dict[str, Any]]) -> None:
        """Mark entity curation as complete with results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE entity_curation 
                SET curated_entities_json = ?, status = 'COMPLETED'
                WHERE journal_id = ?
            """, (json.dumps(curated_entities), journal_id))
            await db.commit()

    # ===== RELATIONSHIP CURATION =====

    async def queue_relationship_curation(self, journal_id: str, journal_text: str, entities: List[Entity],
                                          relationships: List[Relation]) -> None:
        """Add relationships to curation queue"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO relationship_curation 
                (journal_id, journal_text, entities_json, relationships_json, status) 
                VALUES (?, ?, ?, ?, 'PENDING')
            """, (journal_id, journal_text, json.dumps(entities), json.dumps(relationships)))
            await db.commit()

    async def get_relationship_curation_result(self, journal_id: str) -> List[Relation] | None:
        """Check if relationship curation is complete, return curated relationships if done"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT curated_relationships_json, status 
                FROM relationship_curation 
                WHERE journal_id = ?
            """, (journal_id,)) as cursor:
                row = await cursor.fetchone()

                if row and row[1] == 'COMPLETED':
                    return json.loads(row[0])
                return None

    async def get_pending_relationship_curation(self) -> List[Dict[str, Any]]:
        """Get all pending relationship curation tasks, oldest first"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT journal_id, journal_text, entities_json, relationships_json, created_at, status
                FROM relationship_curation 
                WHERE status IN ('PENDING', 'IN_PROGRESS')
                ORDER BY created_at ASC
            """) as cursor:
                rows = await cursor.fetchall()

                return [
                    {
                        "journal_id": row[0],
                        "journal_text": row[1],
                        "entities": json.loads(row[2]),
                        "relationships": json.loads(row[3]),
                        "created_at": row[4],
                        "status": row[5]
                    }
                    for row in rows
                ]

    async def complete_relationship_curation(self, journal_id: str,
                                             curated_relationships: List[Dict[str, Any]]) -> None:
        """Mark relationship curation as complete with results"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE relationship_curation 
                SET curated_relationships_json = ?, status = 'COMPLETED'
                WHERE journal_id = ?
            """, (json.dumps(curated_relationships), journal_id))
            await db.commit()

    # ===== DASHBOARD API HELPERS =====

    async def get_all_pending_curation_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all pending curation tasks for the dashboard"""
        entity_tasks = await self.get_pending_entity_curation()
        relationship_tasks = await self.get_pending_relationship_curation()

        return {
            "entities": entity_tasks,
            "relationships": relationship_tasks,
            "total_pending": len(entity_tasks) + len(relationship_tasks)
        }

    async def get_curation_stats(self) -> Dict[str, int]:
        """Get curation statistics for dashboard"""
        async with aiosqlite.connect(self.db_path) as db:
            # Entity stats
            async with db.execute("""
                SELECT status, COUNT(*) 
                FROM entity_curation 
                GROUP BY status
            """) as cursor:
                entity_stats = dict(await cursor.fetchall())

            # Relationship stats
            async with db.execute("""
                SELECT status, COUNT(*) 
                FROM relationship_curation 
                GROUP BY status
            """) as cursor:
                relationship_stats = dict(await cursor.fetchall())

            return {
                "entities_pending": entity_stats.get("PENDING", 0),
                "entities_in_progress": entity_stats.get("IN_PROGRESS", 0),
                "entities_completed": entity_stats.get("COMPLETED", 0),
                "relationships_pending": relationship_stats.get("PENDING", 0),
                "relationships_in_progress": relationship_stats.get("IN_PROGRESS", 0),
                "relationships_completed": relationship_stats.get("COMPLETED", 0)
            }
