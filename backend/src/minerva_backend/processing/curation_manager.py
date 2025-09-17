import json
from typing import List, Dict, Any, Optional
from uuid import uuid4

import aiosqlite

from minerva_backend.graph.models.documents import Span
from minerva_backend.graph.models.entities import (
    Concept,
    Consumable,
    Emotion,
    EntityType,
    Event,
    Feeling,
    Person,
    Place,
    Project,
    Content,
)
from minerva_backend.graph.models.relations import Relation
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_relationships import RelationshipContext

ENTITY_TYPE_MAP = {
    EntityType.PERSON.value: Person,
    EntityType.EMOTION.value: Emotion,
    EntityType.FEELING.value: Feeling,
    EntityType.EVENT.value: Event,
    EntityType.PROJECT.value: Project,
    EntityType.CONCEPT.value: Concept,
    EntityType.CONTENT.value: Content,
    EntityType.CONSUMABLE.value: Consumable,
    EntityType.PLACE.value: Place,
}


class CurationManager:
    """Manages the human-in-the-loop curation queue using SQLite"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def initialize(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS journal_curation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    overall_status TEXT DEFAULT 'PENDING_ENTITIES'
                    -- PENDING_ENTITIES, ENTITIES_DONE, PENDING_RELATIONS, COMPLETED
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS entity_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_id TEXT,
                    entity_type TEXT,
                    original_data_json TEXT,  -- NULL for user-added entities
                    curated_data_json TEXT,   -- Always present for ACCEPTED
                    status TEXT DEFAULT 'PENDING',  -- PENDING, ACCEPTED, REJECTED
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_added BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS relationship_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_id TEXT,
                    relationship_type TEXT,
                    original_data_json TEXT,  -- NULL for user-added
                    curated_data_json TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_added BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS span_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_id TEXT,
                    owner_uuid TEXT, -- entity_curation_items.uuid or relationship_curation_items.uuid
                    span_data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid)
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS relationship_context_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_id TEXT,
                    relationship_uuid TEXT,
                    entity_uuid TEXT,
                    sub_type_json TEXT, -- JSON array of strings
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid),
                    FOREIGN KEY (relationship_uuid) REFERENCES relationship_curation_items (uuid)
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

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_span_items_owner
                ON span_curation_items (owner_uuid)
            """)

            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_relationship_context_items_relationship_uuid
                ON relationship_context_items (relationship_uuid)
            """)

            await db.commit()

    # ===== JOURNAL MANAGEMENT =====

    async def create_journal_for_curation(self, journal_uuid: str, journal_text: str) -> None:
        """Create a new journal entry for curation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO journal_curation 
                (uuid, journal_text, overall_status) 
                VALUES (?, ?, 'PENDING_ENTITIES')
            """, (journal_uuid, journal_text))
            await db.commit()

    async def get_journal_status(self, journal_uuid: str) -> Optional[str]:
        """Get the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT overall_status 
                FROM journal_curation 
                WHERE uuid = ?
            """, (journal_uuid,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def update_journal_status(self, journal_uuid: str, status: str) -> None:
        """Update the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE journal_curation 
                SET overall_status = ? 
                WHERE uuid = ?
            """, (status, journal_uuid))
            await db.commit()

    # ===== ENTITY CURATION =====

    async def queue_entities_for_curation(self, journal_uuid: str, journal_text: str,
                                          entities: List[EntitySpanMapping]) -> None:
        """Add entities to curation queue"""
        # First ensure journal exists
        await self.create_journal_for_curation(journal_uuid, journal_text)

        async with aiosqlite.connect(self.db_path) as db:
            for entity_spans in entities:
                entity = entity_spans.entity
                await db.execute("""
                    INSERT INTO entity_curation_items 
                    (uuid, journal_id, entity_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'PENDING', FALSE)
                """, (str(entity.uuid), journal_uuid, entity.type, entity.model_dump_json()))
                for span in entity_spans.spans:
                    await db.execute("""
                        INSERT INTO span_curation_items
                        (uuid, journal_id, owner_uuid, span_data_json)
                        VALUES (?, ?, ?, ?)
                    """, (str(span.uuid), journal_uuid, str(entity.uuid), span.model_dump_json()))
            await db.commit()

    async def accept_entity(self, journal_uuid: str, entity_uuid: str, curated_data: Dict[str, Any],
                            is_user_added: bool = False) -> str:
        """Accept an entity with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            if is_user_added:
                new_uuid = str(uuid4())
                await db.execute("""
                    INSERT INTO entity_curation_items 
                    (uuid, journal_id, entity_type, curated_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'ACCEPTED', TRUE)
                """, (new_uuid, journal_uuid, curated_data.get('type', 'UNKNOWN'), json.dumps(curated_data)))
                await db.commit()
                return new_uuid
            else:
                cursor = await db.execute("""
                    UPDATE entity_curation_items 
                    SET curated_data_json = ?, status = 'ACCEPTED'
                    WHERE uuid = ? AND journal_id = ? AND status = 'PENDING'
                """, (json.dumps(curated_data), entity_uuid, journal_uuid))
                await db.commit()
                return entity_uuid if cursor.rowcount > 0 else ""

    async def reject_entity(self, journal_uuid: str, entity_uuid: str) -> bool:
        """Reject an entity"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE entity_curation_items 
                SET status = 'REJECTED'
                WHERE uuid = ? AND journal_id = ? AND status = 'PENDING'
            """, (entity_uuid, journal_uuid))
            await db.commit()
            return cursor.rowcount > 0

    async def get_accepted_entities_with_spans(self, journal_uuid: str) -> List[EntitySpanMapping]:
        """Get all accepted entities for a journal with their spans"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT uuid, curated_data_json
                FROM entity_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """, (journal_uuid,)) as cursor:
                entity_rows = await cursor.fetchall()

            results = []
            for entity_uuid, entity_json in entity_rows:
                entity_data = json.loads(entity_json)
                entity_type = entity_data.get('type')
                EntityClass = ENTITY_TYPE_MAP.get(entity_type)

                if not EntityClass:
                    # skipping unknown entity type
                    continue

                entity = EntityClass.model_validate(entity_data)

                async with db.execute("""
                    SELECT span_data_json
                    FROM span_curation_items
                    WHERE owner_uuid = ?
                """, (entity_uuid,)) as span_cursor:
                    span_rows = await span_cursor.fetchall()
                    spans = {Span.model_validate(json.loads(row[0])) for row in span_rows}

                results.append(EntitySpanMapping(entity, spans))

            return results

    async def complete_entity_phase(self, journal_uuid: str) -> None:
        """Mark entity curation phase as complete and move to relationship phase"""
        await self.update_journal_status(journal_uuid, 'ENTITIES_DONE')

    # ===== RELATIONSHIP CURATION =====

    async def queue_relationships_for_curation(self, journal_uuid: str,
                                               relationships: List[RelationSpanContextMapping]) -> None:
        """Add relationships to curation queue"""
        await self.update_journal_status(journal_uuid, 'PENDING_RELATIONS')

        async with aiosqlite.connect(self.db_path) as db:
            for r in relationships:
                relationship = r.relation
                spans = r.spans
                contexts = r.context
                await db.execute("""
                    INSERT INTO relationship_curation_items 
                    (uuid, journal_id, relationship_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'PENDING', FALSE)
                """, (str(relationship.uuid), journal_uuid, relationship.type, relationship.model_dump_json()))

                for span in spans:
                    await db.execute("""
                        INSERT INTO span_curation_items
                        (uuid, journal_id, owner_uuid, span_data_json)
                        VALUES (?, ?, ?, ?)
                    """, (str(span.uuid), journal_uuid, str(relationship.uuid), span.model_dump_json()))
                if contexts:
                    for context in contexts:
                        await db.execute("""
                            INSERT INTO relationship_context_items
                            (journal_id, relationship_uuid, entity_uuid, sub_type_json)
                            VALUES (?, ?, ?, ?)
                        """, (journal_uuid, str(relationship.uuid), context.entity_uuid,
                              json.dumps(context.sub_type)))
            await db.commit()

    async def accept_relationship(self, journal_uuid: str, relationship_uuid: str, curated_data: Dict[str, Any],
                                  is_user_added: bool = False) -> str:
        """Accept a relationship with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            if is_user_added:
                new_uuid = str(uuid4())
                await db.execute("""
                    INSERT INTO relationship_curation_items 
                    (uuid, journal_id, relationship_type, curated_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'ACCEPTED', TRUE)
                """, (new_uuid, journal_uuid, curated_data.get('type', 'UNKNOWN'), json.dumps(curated_data)))
                await db.commit()
                return new_uuid
            else:
                cursor = await db.execute("""
                    UPDATE relationship_curation_items 
                    SET curated_data_json = ?, status = 'ACCEPTED'
                    WHERE uuid = ? AND journal_id = ? AND status = 'PENDING'
                """, (json.dumps(curated_data), relationship_uuid, journal_uuid))
                await db.commit()
                return relationship_uuid if cursor.rowcount > 0 else ""

    async def reject_relationship(self, journal_uuid: str, relationship_uuid: str) -> bool:
        """Reject a relationship"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                UPDATE relationship_curation_items 
                SET status = 'REJECTED'
                WHERE uuid = ? AND journal_id = ? AND status = 'PENDING'
            """, (relationship_uuid, journal_uuid))
            await db.commit()
            return cursor.rowcount > 0

    async def get_accepted_relationships_with_spans(self, journal_uuid: str) -> List[RelationSpanContextMapping]:
        """Get all accepted relationships for a journal with their spans"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT uuid, curated_data_json
                FROM relationship_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """, (journal_uuid,)) as cursor:
                relationship_rows = await cursor.fetchall()

            results = []
            for rel_uuid, rel_json in relationship_rows:
                relation = Relation.model_validate(json.loads(rel_json))

                async with db.execute("""
                    SELECT span_data_json
                    FROM span_curation_items
                    WHERE owner_uuid = ?
                """, (rel_uuid,)) as span_cursor:
                    span_rows = await span_cursor.fetchall()
                    spans = {Span.model_validate(json.loads(row[0])) for row in span_rows}

                async with db.execute("""
                    SELECT entity_uuid, sub_type_json
                    FROM relationship_context_items
                    WHERE relationship_uuid = ?
                """, (rel_uuid,)) as context_cursor:
                    context_rows = await context_cursor.fetchall()
                    contexts = {
                        RelationshipContext(entity_uuid=row[0], sub_type=json.loads(row[1]))
                        for row in context_rows
                    } if context_rows else None

                results.append(RelationSpanContextMapping(relation, spans, contexts))
            return results

    async def complete_relationship_phase(self, journal_uuid: str) -> None:
        """Mark relationship curation phase as complete"""
        await self.update_journal_status(journal_uuid, 'COMPLETED')

    # ===== DASHBOARD API HELPERS =====

    async def get_journals_pending_entity_curation(self) -> List[Dict[str, Any]]:
        """Get journals that need entity curation with detailed pending entities"""
        async with aiosqlite.connect(self.db_path) as db:
            # First get the journal list with counts
            async with db.execute("""
                SELECT j.uuid, j.journal_text, j.created_at,
                       COUNT(e.uuid) as pending_entities_count
                FROM journal_curation j
                LEFT JOIN entity_curation_items e ON j.uuid = e.journal_id AND e.status = 'PENDING'
                WHERE j.overall_status = 'PENDING_ENTITIES'
                GROUP BY j.uuid, j.journal_text, j.created_at
                ORDER BY j.created_at ASC
            """) as cursor:
                journal_rows = await cursor.fetchall()

            # Now get the detailed entities for each journal
            journals_with_entities = []
            for row in journal_rows:
                journal_uuid = row[0]

                # Get the detailed pending entities for this journal
                async with db.execute("""
                    SELECT uuid, entity_type, original_data_json, status
                    FROM entity_curation_items 
                    WHERE journal_id = ? AND status = 'PENDING'
                    ORDER BY created_at ASC
                """, (journal_uuid,)) as entity_cursor:
                    entity_rows = await entity_cursor.fetchall()

                pending_entities = [
                    {
                        "id": entity_row[0],  # uuid
                        "entity_type": entity_row[1],
                        "status": entity_row[3],
                        **json.loads(entity_row[2])
                    }
                    for entity_row in entity_rows
                ]

                journals_with_entities.append({
                    "journal_id": row[0],  # uuid
                    "journal_text": row[1],
                    "created_at": row[2],
                    "pending_entities_count": row[3],
                    "pending_entities": pending_entities,
                    "phase": "entities"
                })

            return journals_with_entities

    async def get_journals_pending_relationship_curation(self) -> List[Dict[str, Any]]:
        """Get journals that need relationship curation with detailed pending relationships"""
        async with aiosqlite.connect(self.db_path) as db:
            # First get the journal list with counts
            async with db.execute("""
                SELECT j.uuid, j.journal_text, j.created_at,
                       COUNT(r.uuid) as pending_relationships_count
                FROM journal_curation j
                LEFT JOIN relationship_curation_items r ON j.uuid = r.journal_id AND r.status = 'PENDING'
                WHERE j.overall_status = 'PENDING_RELATIONS'
                GROUP BY j.uuid, j.journal_text, j.created_at
                ORDER BY j.created_at ASC
            """) as cursor:
                journal_rows = await cursor.fetchall()

            # Now get the detailed relationships for each journal
            journals_with_relationships = []
            for row in journal_rows:
                journal_uuid = row[0]

                # Get the detailed pending relationships for this journal
                async with db.execute("""
                    SELECT uuid, relationship_type, original_data_json, status
                    FROM relationship_curation_items 
                    WHERE journal_id = ? AND status = 'PENDING'
                    ORDER BY created_at ASC
                """, (journal_uuid,)) as rel_cursor:
                    rel_rows = await rel_cursor.fetchall()

                pending_relationships = [
                    {
                        "id": rel_row[0],  # uuid
                        "relationship_type": rel_row[1],
                        "status": rel_row[3],
                        **json.loads(rel_row[2])
                    }
                    for rel_row in rel_rows
                ]

                journals_with_relationships.append({
                    "journal_id": row[0],  # uuid
                    "journal_text": row[1],
                    "created_at": row[2],
                    "pending_relationships_count": row[3],
                    "pending_relationships": pending_relationships,
                    "phase": "relationships"
                })

            return journals_with_relationships

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
