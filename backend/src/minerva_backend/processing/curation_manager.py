import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiosqlite

from minerva_models import (
    Span,
    Concept,
    Consumable,
    Content,
    Emotion,
    EntityType,
    Event,
    FeelingConcept,
    FeelingEmotion,
    Person,
    Place,
    Project,
)
from minerva_models import Relation
from minerva_backend.processing.models import (
    CuratableMapping,
    CurationEntityStats,
    CurationRelationshipStats,
    CurationStats,
    CurationTask,
    EntityMapping,
    JournalEntryCuration,
)
from minerva_backend.prompt.extract_relationships import RelationshipContext

ENTITY_TYPE_MAP = {
    EntityType.PERSON.value: Person,
    EntityType.EMOTION.value: Emotion,
    EntityType.FEELING_EMOTION.value: FeelingEmotion,
    EntityType.FEELING_CONCEPT.value: FeelingConcept,
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
        self.ENTITY_TYPE_MAP = ENTITY_TYPE_MAP

    async def initialize(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS journal_curation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    overall_status TEXT DEFAULT 'PENDING_ENTITIES'
                    -- PENDING_ENTITIES, ENTITIES_DONE, PENDING_RELATIONS, COMPLETED
                )
            """
            )

            await db.execute(
                """
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
            """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS relationship_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_id TEXT,
                    kind TEXT NOT NULL DEFAULT 'relation',
                    relationship_type TEXT,
                    original_data_json TEXT,  -- NULL for user-added
                    curated_data_json TEXT,
                    status TEXT DEFAULT 'PENDING',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_user_added BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid)
                )
            """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS span_curation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT,
                    journal_id TEXT,
                    owner_uuid TEXT, -- entity_curation_items.uuid or relationship_curation_items.uuid
                    span_data_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (journal_id) REFERENCES journal_curation (uuid)
                )
            """
            )

            await db.execute(
                """
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
            """
            )

            # Indexes
            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_journal_curation_status_date 
                ON journal_curation (overall_status, created_at)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_entity_items_journal_status 
                ON entity_curation_items (journal_id, status)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_relationship_items_journal_status 
                ON relationship_curation_items (journal_id, status)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_span_items_owner
                ON span_curation_items (owner_uuid)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_relationship_context_items_relationship_uuid
                ON relationship_context_items (relationship_uuid)
            """
            )

            await db.commit()

    # ===== JOURNAL MANAGEMENT =====

    async def create_journal_for_curation(
        self, journal_uuid: str, journal_text: str
    ) -> None:
        """Create a new journal entry for curation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO journal_curation 
                (uuid, journal_text, overall_status) 
                VALUES (?, ?, 'PENDING_ENTITIES')
            """,
                (journal_uuid, journal_text),
            )
            await db.commit()

    async def get_journal_status(self, journal_uuid: str) -> Optional[str]:
        """Get the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT overall_status 
                FROM journal_curation 
                WHERE uuid = ?
            """,
                (journal_uuid,),
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def update_journal_status(self, journal_uuid: str, status: str) -> None:
        """Update the overall status of a journal"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE journal_curation 
                SET overall_status = ? 
                WHERE uuid = ?
            """,
                (status, journal_uuid),
            )
            await db.commit()

    # ===== ENTITY CURATION =====

    async def queue_entities_for_curation(
        self, journal_uuid: str, journal_text: str, entities: List[EntityMapping]
    ) -> None:
        """Add entities to curation queue"""
        # First ensure journal exists
        await self.create_journal_for_curation(journal_uuid, journal_text)

        async with aiosqlite.connect(self.db_path) as db:
            for entity_spans in entities:
                entity = entity_spans.entity

                # Entity should always be a proper domain entity with uuid
                # If it doesn't have uuid, that's a serious error that should be caught earlier

                await db.execute(
                    """
                    INSERT INTO entity_curation_items 
                    (uuid, journal_id, entity_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'PENDING', FALSE)
                """,
                    (
                        str(entity.uuid),
                        journal_uuid,
                        entity.type,
                        entity.model_dump_json(),
                    ),
                )
                for span in entity_spans.spans:
                    await db.execute(
                        """
                        INSERT INTO span_curation_items
                        (uuid, journal_id, owner_uuid, span_data_json)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            str(span.uuid),
                            journal_uuid,
                            str(entity.uuid),
                            span.model_dump_json(),
                        ),
                    )
            await db.commit()

    async def accept_entity(
        self,
        journal_uuid: str,
        entity_uuid: str,
        curated_data: Dict[str, Any],
        is_user_added: bool = False,
    ) -> str:
        """Accept an entity with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            if is_user_added:
                new_uuid = str(uuid4())
                await db.execute(
                    """
                    INSERT INTO entity_curation_items 
                    (uuid, journal_id, entity_type, curated_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'ACCEPTED', TRUE)
                """,
                    (
                        new_uuid,
                        journal_uuid,
                        curated_data.get("type", "UNKNOWN"),
                        json.dumps(curated_data),
                    ),
                )
                await db.commit()
                return new_uuid
            else:
                curated_data["uuid"] = entity_uuid
                cursor = await db.execute(
                    """
                    UPDATE entity_curation_items 
                    SET curated_data_json = ?, status = 'ACCEPTED'
                    WHERE uuid = ? AND journal_id = ?
                """,
                    (
                        json.dumps(curated_data, default=lambda o: o.isoformat()),
                        entity_uuid,
                        journal_uuid,
                    ),
                )
                await db.commit()
                return entity_uuid if cursor.rowcount > 0 else ""

    async def reject_entity(self, journal_uuid: str, entity_uuid: str) -> bool:
        """Reject an entity"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE entity_curation_items 
                SET status = 'REJECTED'
                WHERE uuid = ? AND journal_id = ?
            """,
                (entity_uuid, journal_uuid),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_accepted_entities_with_spans(
        self, journal_uuid: str
    ) -> List[EntityMapping]:
        """Get all accepted entities for a journal with their spans"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT uuid, curated_data_json
                FROM entity_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """,
                (journal_uuid,),
            ) as cursor:
                entity_rows = await cursor.fetchall()

            results = []
            for entity_uuid, entity_json in entity_rows:
                entity_data = json.loads(entity_json)
                entity_type = entity_data.get("type")
                EntityClass = ENTITY_TYPE_MAP.get(entity_type)
                if not EntityClass:
                    # skipping unknown entity type
                    continue

                entity = EntityClass.model_validate(entity_data)  # type: ignore[attr-defined]

                async with db.execute(
                    """
                    SELECT span_data_json
                    FROM span_curation_items
                    WHERE owner_uuid = ?
                """,
                    (entity_uuid,),
                ) as span_cursor:
                    span_rows = await span_cursor.fetchall()
                    spans = [
                        Span.model_validate(json.loads(row[0])) for row in span_rows
                    ]

                results.append(EntityMapping(entity, spans))

            return results

    async def complete_entity_phase(self, journal_uuid: str) -> None:
        """Mark entity curation phase as complete and move to relationship phase"""
        await self.update_journal_status(journal_uuid, "ENTITIES_DONE")

    # ===== RELATIONSHIP CURATION =====

    async def queue_relationships_for_curation(
        self, journal_uuid: str, items: List[CuratableMapping]
    ) -> None:
        """Add relationships and feelings to curation queue"""
        await self.update_journal_status(journal_uuid, "PENDING_RELATIONS")

        async with aiosqlite.connect(self.db_path) as db:
            for item in items:
                data = item.data
                spans = item.spans
                contexts = item.context

                # Determine relationship_type based on kind
                if item.kind in ["relation", "concept_relation"]:
                    relationship_type = data.type
                else:  # feeling_emotion, feeling_concept
                    relationship_type = item.kind

                await db.execute(
                    """
                    INSERT INTO relationship_curation_items 
                    (uuid, journal_id, kind, relationship_type, original_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, ?, 'PENDING', FALSE)
                """,
                    (
                        str(data.uuid),
                        journal_uuid,
                        item.kind,
                        relationship_type,
                        data.model_dump_json(),
                    ),
                )

                for span in spans:
                    await db.execute(
                        """
                        INSERT INTO span_curation_items
                        (uuid, journal_id, owner_uuid, span_data_json)
                        VALUES (?, ?, ?, ?)
                    """,
                        (
                            str(span.uuid),
                            journal_uuid,
                            str(data.uuid),
                            span.model_dump_json(),
                        ),
                    )
                if contexts and item.kind in ["relation", "concept_relation"]:
                    for context in contexts:
                        await db.execute(
                            """
                            INSERT INTO relationship_context_items
                            (journal_id, relationship_uuid, entity_uuid, sub_type_json)
                            VALUES (?, ?, ?, ?)
                        """,
                            (
                                journal_uuid,
                                str(data.uuid),
                                context.entity_uuid,
                                json.dumps(context.sub_type),
                            ),
                        )
            await db.commit()

    async def accept_relationship(
        self,
        journal_uuid: str,
        relationship_uuid: str,
        curated_data: Dict[str, Any],
        is_user_added: bool = False,
    ) -> str:
        """Accept a relationship with optional modifications"""
        async with aiosqlite.connect(self.db_path) as db:
            if is_user_added:
                new_uuid = str(uuid4())
                await db.execute(
                    """
                    INSERT INTO relationship_curation_items 
                    (uuid, journal_id, relationship_type, curated_data_json, status, is_user_added) 
                    VALUES (?, ?, ?, ?, 'ACCEPTED', TRUE)
                """,
                    (
                        new_uuid,
                        journal_uuid,
                        curated_data.get("type", "UNKNOWN"),
                        json.dumps(curated_data),
                    ),
                )
                await db.commit()
                return new_uuid
            else:
                curated_data["uuid"] = relationship_uuid
                cursor = await db.execute(
                    """
                    UPDATE relationship_curation_items 
                    SET curated_data_json = ?, status = 'ACCEPTED'
                    WHERE uuid = ? AND journal_id = ?
                """,
                    (json.dumps(curated_data), relationship_uuid, journal_uuid),
                )
                await db.commit()
                return relationship_uuid if cursor.rowcount > 0 else ""

    async def reject_relationship(
        self, journal_uuid: str, relationship_uuid: str
    ) -> bool:
        """Reject a relationship"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE relationship_curation_items 
                SET status = 'REJECTED'
                WHERE uuid = ? AND journal_id = ?
            """,
                (relationship_uuid, journal_uuid),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_accepted_relationships_with_spans(
        self, journal_uuid: str
    ) -> List[CuratableMapping]:
        """Get all accepted relationships and feelings for a journal with their spans"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT uuid, kind, curated_data_json
                FROM relationship_curation_items 
                WHERE journal_id = ? AND status = 'ACCEPTED'
            """,
                (journal_uuid,),
            ) as cursor:
                item_rows = await cursor.fetchall()

            results = []
            for item_uuid, kind, data_json in item_rows:
                # Deserialize based on kind
                data_dict = json.loads(data_json)
                if kind == "relation":
                    data = Relation.model_validate(data_dict)
                elif kind == "concept_relation":
                    from minerva_models import ConceptRelation

                    data = ConceptRelation.model_validate(data_dict)
                elif kind == "feeling_emotion":
                    data = FeelingEmotion.model_validate(data_dict)
                elif kind == "feeling_concept":
                    data = FeelingConcept.model_validate(data_dict)
                else:
                    continue  # Skip unknown kinds

                async with db.execute(
                    """
                    SELECT span_data_json
                    FROM span_curation_items
                    WHERE owner_uuid = ?
                """,
                    (item_uuid,),
                ) as span_cursor:
                    span_rows = await span_cursor.fetchall()
                    spans = [
                        Span.model_validate(json.loads(row[0])) for row in span_rows
                    ]

                # Only add context for relation kinds
                contexts = None
                if kind in ["relation", "concept_relation"]:
                    async with db.execute(
                        """
                        SELECT entity_uuid, sub_type_json
                        FROM relationship_context_items
                        WHERE relationship_uuid = ?
                    """,
                        (item_uuid,),
                    ) as context_cursor:
                        context_rows = await context_cursor.fetchall()
                        contexts = (
                            [
                                RelationshipContext(
                                    entity_uuid=row[0], sub_type=json.loads(row[1])
                                )
                                for row in context_rows
                            ]
                            if context_rows
                            else None
                        )

                results.append(
                    CuratableMapping(
                        kind=kind, data=data, spans=spans, context=contexts
                    )
                )
            return results

    async def complete_relationship_phase(self, journal_uuid: str) -> None:
        """Mark relationship curation phase as complete"""
        await self.update_journal_status(journal_uuid, "COMPLETED")

    # ===== DASHBOARD API HELPERS =====

    async def get_all_pending_curation_tasks(self) -> Dict[str, JournalEntryCuration]:
        """Get all pending curation tasks for the dashboard, grouped by journalentry"""
        async with aiosqlite.connect(self.db_path) as db:
            # Fetch journal entries
            journal_curations = await self._fetch_journal_entries(db)
            if not journal_curations:
                return {}

            journal_ids = tuple(journal_curations.keys())

            # Process entity tasks
            entity_tasks = await self._fetch_entity_tasks(db, journal_ids)
            if entity_tasks:
                await self._enrich_entity_tasks_with_spans(db, entity_tasks)
                self._add_tasks_to_journal_curations(journal_curations, entity_tasks)

            # Process relationship tasks
            relationship_tasks = await self._fetch_relationship_tasks(db, journal_ids)
            if relationship_tasks:
                await self._enrich_relationship_tasks_with_data(db, relationship_tasks)
                self._add_tasks_to_journal_curations(
                    journal_curations, relationship_tasks
                )

            return journal_curations

    async def _fetch_journal_entries(self, db) -> Dict[str, JournalEntryCuration]:
        """Fetch journal entries from database."""
        async with db.execute(
            """
            SELECT uuid, journal_text, created_at, overall_status FROM journal_curation
            WHERE overall_status != 'COMPLETED' ORDER BY created_at DESC
        """
        ) as cursor:
            journal_rows = await cursor.fetchall()

        if not journal_rows:
            return {}

        return {
            row[0]: JournalEntryCuration(
                journal_id=row[0],
                date=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S").date(),
                entry_text=row[1],
                phase=(
                    "relationships" if row[3] == "PENDING_RELATIONS" else "entities"
                ),
            )
            for row in journal_rows
        }

    async def _fetch_entity_tasks(
        self, db, journal_ids: tuple
    ) -> Dict[str, CurationTask]:
        """Fetch entity tasks from database."""
        async with db.execute(
            f"""
            SELECT uuid, journal_id, created_at, original_data_json
            FROM entity_curation_items
            WHERE journal_id IN ({','.join('?' for _ in journal_ids)}) AND status = 'PENDING'
        """,
            journal_ids,
        ) as cursor:
            entity_rows = await cursor.fetchall()

        tasks = {}
        for row in entity_rows:
            entity_data = json.loads(row[3])
            entity_type = entity_data.get("type")
            EntityClass = ENTITY_TYPE_MAP.get(entity_type)

            if not EntityClass:
                # Skip unknown entity types
                continue

            # Deserialize to proper entity type
            entity = EntityClass.model_validate(entity_data)

            tasks[row[0]] = CurationTask(
                id=row[0],
                journal_id=row[1],
                type="entity",
                status="pending",
                created_at=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                data=entity.model_dump(),  # Use the properly deserialized entity
            )

        return tasks

    async def _fetch_relationship_tasks(
        self, db, journal_ids: tuple
    ) -> Dict[str, CurationTask]:
        """Fetch relationship tasks from database."""
        async with db.execute(
            f"""
            SELECT uuid, journal_id, created_at, original_data_json
            FROM relationship_curation_items
            WHERE journal_id IN ({','.join('?' for _ in journal_ids)}) AND status = 'PENDING'
        """,
            journal_ids,
        ) as cursor:
            relationship_rows = await cursor.fetchall()

        return {
            row[0]: CurationTask(
                id=row[0],
                journal_id=row[1],
                type="relationship",
                status="pending",
                created_at=datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                data=json.loads(row[3]),
            )
            for row in relationship_rows
        }

    async def _enrich_entity_tasks_with_spans(
        self, db, entity_tasks: Dict[str, CurationTask]
    ):
        """Add span data to entity tasks."""
        entity_uuids = tuple(entity_tasks.keys())
        async with db.execute(
            f"""
            SELECT owner_uuid, span_data_json FROM span_curation_items
            WHERE owner_uuid IN ({','.join('?' for _ in entity_uuids)})
        """,
            entity_uuids,
        ) as cursor:
            for owner_uuid, span_json in await cursor.fetchall():
                if "spans" not in entity_tasks[owner_uuid].data:
                    entity_tasks[owner_uuid].data["spans"] = []
                entity_tasks[owner_uuid].data["spans"].append(json.loads(span_json))

    async def _enrich_relationship_tasks_with_data(
        self, db, relationship_tasks: Dict[str, CurationTask]
    ):
        """Add span and context data to relationship tasks."""
        rel_uuids = tuple(relationship_tasks.keys())

        # Add spans
        await self._add_spans_to_tasks(db, relationship_tasks, rel_uuids)

        # Add context
        await self._add_context_to_relationship_tasks(db, relationship_tasks, rel_uuids)

    async def _add_spans_to_tasks(
        self, db, tasks: Dict[str, CurationTask], uuids: tuple
    ):
        """Add span data to tasks."""
        async with db.execute(
            f"""
            SELECT owner_uuid, span_data_json FROM span_curation_items
            WHERE owner_uuid IN ({','.join('?' for _ in uuids)})
        """,
            uuids,
        ) as cursor:
            for owner_uuid, span_json in await cursor.fetchall():
                if "spans" not in tasks[owner_uuid].data:
                    tasks[owner_uuid].data["spans"] = []
                tasks[owner_uuid].data["spans"].append(json.loads(span_json))

    async def _add_context_to_relationship_tasks(
        self, db, relationship_tasks: Dict[str, CurationTask], rel_uuids: tuple
    ):
        """Add context data to relationship tasks."""
        async with db.execute(
            f"""
            SELECT relationship_uuid, entity_uuid, sub_type_json
            FROM relationship_context_items
            WHERE relationship_uuid IN ({','.join('?' for _ in rel_uuids)})
        """,
            rel_uuids,
        ) as cursor:
            for rel_uuid, entity_uuid, sub_type_json in await cursor.fetchall():
                if "context" not in relationship_tasks[rel_uuid].data:
                    relationship_tasks[rel_uuid].data["context"] = []
                relationship_tasks[rel_uuid].data["context"].append(
                    {
                        "entity_uuid": entity_uuid,
                        "sub_type": json.loads(sub_type_json),
                    }
                )

    def _add_tasks_to_journal_curations(
        self,
        journal_curations: Dict[str, JournalEntryCuration],
        tasks: Dict[str, CurationTask],
    ):
        """Add tasks to their respective journal curations."""
        for task in tasks.values():
            journal_curations[task.journal_id].tasks[task.id] = task

    async def get_curation_stats(self) -> CurationStats:
        """Get overall curation statistics for the dashboard"""
        async with aiosqlite.connect(self.db_path) as db:
            # Journal stats
            async with db.execute(
                """
                SELECT overall_status, COUNT(*)
                FROM journal_curation
                GROUP BY overall_status
            """
            ) as cursor:
                journal_rows = await cursor.fetchall()
            journal_counts: Dict[str, int] = dict(tuple(row) for row in journal_rows)

            total_journals = sum(journal_counts.values())
            pending_entities_journals = journal_counts.get("PENDING_ENTITIES", 0)
            pending_relations_journals = journal_counts.get(
                "PENDING_RELATIONS", 0
            ) + journal_counts.get("ENTITIES_DONE", 0)
            completed_journals = journal_counts.get("COMPLETED", 0)

            # Entity stats
            async with db.execute(
                """
                SELECT status, COUNT(*)
                FROM entity_curation_items
                GROUP BY status
            """
            ) as cursor:
                entity_rows = await cursor.fetchall()
            entity_counts: Dict[str, int] = dict(tuple(row) for row in entity_rows)

            entities_accepted = entity_counts.get("ACCEPTED", 0)
            entities_rejected = entity_counts.get("REJECTED", 0)
            entities_pending = entity_counts.get("PENDING", 0)
            total_entities = entities_accepted + entities_rejected + entities_pending
            entity_acceptance_rate = (
                (entities_accepted / (entities_accepted + entities_rejected))
                if (entities_accepted + entities_rejected) > 0
                else 0.0
            )

            entity_stats = CurationEntityStats(
                total_extracted=total_entities,
                accepted=entities_accepted,
                rejected=entities_rejected,
                pending=entities_pending,
                acceptance_rate=entity_acceptance_rate,
            )

            # Relationship stats
            async with db.execute(
                """
                SELECT status, COUNT(*)
                FROM relationship_curation_items
                GROUP BY status
            """
            ) as cursor:
                rel_rows = await cursor.fetchall()
            rel_counts: Dict[str, int] = dict(tuple(row) for row in rel_rows)

            rels_accepted = rel_counts.get("ACCEPTED", 0)
            rels_rejected = rel_counts.get("REJECTED", 0)
            rels_pending = rel_counts.get("PENDING", 0)
            total_rels = rels_accepted + rels_rejected + rels_pending
            rel_acceptance_rate = (
                (rels_accepted / (rels_accepted + rels_rejected))
                if (rels_accepted + rels_rejected) > 0
                else 0.0
            )

            relationship_stats = CurationRelationshipStats(
                total_extracted=total_rels,
                accepted=rels_accepted,
                rejected=rels_rejected,
                pending=rels_pending,
                acceptance_rate=rel_acceptance_rate,
            )

            return CurationStats(
                total_journals=total_journals,
                pending_entities=pending_entities_journals,
                pending_relationships=pending_relations_journals,
                completed=completed_journals,
                entity_stats=entity_stats,
                relationship_stats=relationship_stats,
            )

    async def clear_all(self):
        """Wipe all rows from every table."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM relationship_context_items")
            await db.execute("DELETE FROM span_curation_items")
            await db.execute("DELETE FROM relationship_curation_items")
            await db.execute("DELETE FROM entity_curation_items")
            await db.execute("DELETE FROM journal_curation")
            await db.commit()
