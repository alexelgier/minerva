import json
import os
import tempfile
from datetime import date
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio

from minerva_backend.graph.models.documents import Span, JournalEntry
from minerva_backend.graph.models.entities import Person
from minerva_backend.graph.models.relations import Relation
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.models import EntityMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_relationships import RelationshipContext
from uuid import uuid4


def create_person(name: str, uuid_str: str = None) -> Person:
    return Person(
        uuid=uuid_str if uuid_str else str(uuid4()),
        name=name,
        summary_short=f"A person named {name}",
        summary=f"Details for {name}",
        occupation="Tester"
    )


def create_span(text: str, owner_uuid: str, start: int = 0, end: int = 0, uuid_str: str = None) -> Span:
    return Span(uuid=uuid_str if uuid_str else str(uuid4()), text=text, start=start, end=end, document_uuid=owner_uuid)


def create_relation(source_uuid: str, target_uuid: str, rel_type: str, uuid_str: str = None) -> Relation:
    return Relation(
        uuid=uuid_str if uuid_str else str(uuid4()),
        source=source_uuid,
        target=target_uuid,
        proposed_types=[rel_type],
        summary_short=f"{source_uuid} {rel_type} {target_uuid}",
        summary=f"Relationship details for {source_uuid} {rel_type} {target_uuid}"
    )


@pytest_asyncio.fixture
async def curation_manager_db():
    # Create a temporary file for the database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)  # Close the file descriptor, we just need the path
    try:
        manager = CurationManager(db_path)
        await manager.initialize()
        yield manager
    finally:
        # Clean up: delete the temporary database file
        if os.path.exists(db_path):
            os.remove(db_path)


@pytest_asyncio.fixture
def sample_journal_entry():
    return JournalEntry(uuid="journal-123", date=date(2023, 1, 1), text="This is a test journal entry.")


@pytest_asyncio.fixture
def sample_person_entity():
    return Person(
        uuid="person-abc",
        name="John Doe",
        summary_short="A test person for unit tests",
        summary="A test person entity used for comprehensive unit testing of the curation system",
        occupation="Software Engineer"
    )


@pytest_asyncio.fixture
def sample_span():
    return Span(uuid="span-1", text="John Doe", start=10, end=18)


@pytest_asyncio.fixture
def sample_entity_span_mapping(sample_person_entity, sample_span):
    return EntityMapping(entity=sample_person_entity, spans=[sample_span])


@pytest_asyncio.fixture
def sample_relation():
    return Relation(
        uuid="relation-xyz",
        source="person-abc",
        target="person-def",
        proposed_types=["KNOWS", "WORKS_WITH"],
        summary_short="A test relationship between two people",
        summary="A comprehensive test relationship used for validating the curation system's relationship "
                "handling capabilities"
    )


@pytest_asyncio.fixture
def sample_relationship_context():
    return RelationshipContext(entity_uuid="person-abc", sub_type=["subject"])


@pytest_asyncio.fixture
def sample_relation_span_context_mapping(sample_relation, sample_span, sample_relationship_context):
    return RelationSpanContextMapping(
        relation=sample_relation,
        spans=[sample_span],
        context=[sample_relationship_context]
    )


@pytest.mark.asyncio
async def test_initialize(curation_manager_db: CurationManager):
    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in await cursor.fetchall()]
        assert "journal_curation" in tables
        assert "entity_curation_items" in tables
        assert "relationship_curation_items" in tables
        assert "span_curation_items" in tables
        assert "relationship_context_items" in tables


@pytest.mark.asyncio
async def test_create_get_update_journal_for_curation(curation_manager_db: CurationManager, sample_journal_entry):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)

    status = await curation_manager_db.get_journal_status(sample_journal_entry.uuid)
    assert status == "PENDING_ENTITIES"

    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, "COMPLETED")
    status = await curation_manager_db.get_journal_status(sample_journal_entry.uuid)
    assert status == "COMPLETED"

    assert await curation_manager_db.get_journal_status("non-existent-journal") is None


@pytest.mark.asyncio
async def test_queue_entities_for_curation(curation_manager_db: CurationManager, sample_journal_entry,
                                           sample_entity_span_mapping):
    await curation_manager_db.queue_entities_for_curation(
        sample_journal_entry.uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute("SELECT uuid, journal_id, entity_type, status FROM entity_curation_items")
        entity_item = await cursor.fetchone()
        assert entity_item is not None
        assert entity_item[0] == sample_entity_span_mapping.entity.uuid
        assert entity_item[1] == sample_journal_entry.uuid
        assert entity_item[2] == sample_entity_span_mapping.entity.type
        assert entity_item[3] == "PENDING"

        cursor = await db.execute("SELECT uuid, owner_uuid, span_data_json FROM span_curation_items")
        span_item = await cursor.fetchone()
        assert span_item is not None
        assert span_item[0] == list(sample_entity_span_mapping.spans)[0].uuid
        assert span_item[1] == sample_entity_span_mapping.entity.uuid
        assert json.loads(span_item[2]) == list(sample_entity_span_mapping.spans)[0].model_dump(mode='json')


@pytest.mark.asyncio
@patch('minerva_backend.processing.curation_manager.uuid4', side_effect=['new-uuid-1'])
async def test_accept_entity(mock_uuid4, curation_manager_db: CurationManager, sample_journal_entry,
                             sample_entity_span_mapping, sample_person_entity):
    await curation_manager_db.queue_entities_for_curation(
        sample_journal_entry.uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )

    curated_data = sample_person_entity.model_dump(mode='json')
    accepted_uuid = await curation_manager_db.accept_entity(
        sample_journal_entry.uuid, sample_person_entity.uuid, curated_data
    )
    assert accepted_uuid == sample_person_entity.uuid

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status, curated_data_json FROM entity_curation_items WHERE uuid = ?",
            (sample_person_entity.uuid,)
        )
        status, data_json = await cursor.fetchone()
        assert status == "ACCEPTED"
        assert json.loads(data_json) == curated_data

    # Test user-added entity
    user_added_data = {
        "name": "Jane Doe",
        "type": "PERSON",
        "summary_short": "User created person",
        "summary": "A person entity that was created by the user during curation"
    }
    user_added_uuid = await curation_manager_db.accept_entity(
        sample_journal_entry.uuid, "any-uuid", user_added_data, is_user_added=True
    )
    assert user_added_uuid == "new-uuid-1"

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status, curated_data_json, is_user_added FROM entity_curation_items WHERE uuid = ?",
            ("new-uuid-1",)
        )
        status, data_json, is_user_added = await cursor.fetchone()
        assert status == "ACCEPTED"
        assert json.loads(data_json) == user_added_data
        assert is_user_added == 1


@pytest.mark.asyncio
async def test_reject_entity(curation_manager_db: CurationManager, sample_journal_entry, sample_entity_span_mapping):
    await curation_manager_db.queue_entities_for_curation(
        sample_journal_entry.uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )

    rejected = await curation_manager_db.reject_entity(sample_journal_entry.uuid,
                                                       sample_entity_span_mapping.entity.uuid)
    assert rejected is True

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status FROM entity_curation_items WHERE uuid = ?",
            (sample_entity_span_mapping.entity.uuid,)
        )
        status = (await cursor.fetchone())[0]
        assert status == "REJECTED"

    rejected_non_existent = await curation_manager_db.reject_entity(sample_journal_entry.uuid, "non-existent")
    assert rejected_non_existent is False


@pytest.mark.asyncio
async def test_get_accepted_entities_with_spans(curation_manager_db: CurationManager, sample_journal_entry,
                                                sample_entity_span_mapping, sample_person_entity, sample_span):
    await curation_manager_db.queue_entities_for_curation(
        sample_journal_entry.uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )
    await curation_manager_db.accept_entity(
        sample_journal_entry.uuid, sample_person_entity.uuid, sample_person_entity.model_dump()
    )

    accepted_entities = await curation_manager_db.get_accepted_entities_with_spans(sample_journal_entry.uuid)
    assert len(accepted_entities) == 1
    result_entity_mapping = accepted_entities[0]
    assert result_entity_mapping.entity.uuid == sample_person_entity.uuid
    assert result_entity_mapping.entity.name == sample_person_entity.name
    assert result_entity_mapping.spans == [sample_span]

    # Test with no accepted entities
    await curation_manager_db.reject_entity(sample_journal_entry.uuid, sample_person_entity.uuid)
    no_accepted = await curation_manager_db.get_accepted_entities_with_spans(sample_journal_entry.uuid)
    assert len(no_accepted) == 0


@pytest.mark.asyncio
async def test_complete_entity_phase(curation_manager_db: CurationManager, sample_journal_entry):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.complete_entity_phase(sample_journal_entry.uuid)
    status = await curation_manager_db.get_journal_status(sample_journal_entry.uuid)
    assert status == "ENTITIES_DONE"


@pytest.mark.asyncio
async def test_queue_relationships_for_curation(curation_manager_db: CurationManager, sample_journal_entry,
                                                sample_relation_span_context_mapping):
    # Ensure journal is ready for relations
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, 'ENTITIES_DONE')

    await curation_manager_db.queue_relationships_for_curation(
        sample_journal_entry.uuid, [sample_relation_span_context_mapping]
    )

    status = await curation_manager_db.get_journal_status(sample_journal_entry.uuid)
    assert status == "PENDING_RELATIONS"

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT uuid, journal_id, relationship_type, status FROM relationship_curation_items"
        )
        rel_item = await cursor.fetchone()
        assert rel_item is not None
        assert rel_item[0] == sample_relation_span_context_mapping.relation.uuid
        assert rel_item[1] == sample_journal_entry.uuid
        assert rel_item[2] == sample_relation_span_context_mapping.relation.type
        assert rel_item[3] == "PENDING"

        cursor = await db.execute(
            "SELECT uuid, owner_uuid, span_data_json FROM span_curation_items WHERE owner_uuid = ?",
            (sample_relation_span_context_mapping.relation.uuid,)
        )
        span_item = await cursor.fetchone()
        assert span_item is not None
        assert span_item[0] == list(sample_relation_span_context_mapping.spans)[0].uuid
        assert span_item[1] == sample_relation_span_context_mapping.relation.uuid
        assert json.loads(span_item[2]) == list(sample_relation_span_context_mapping.spans)[0].model_dump(mode='json')

        cursor = await db.execute(
            "SELECT relationship_uuid, entity_uuid, sub_type_json FROM relationship_context_items"
        )
        context_item = await cursor.fetchone()
        assert context_item is not None
        assert context_item[0] == sample_relation_span_context_mapping.relation.uuid
        assert context_item[1] == list(sample_relation_span_context_mapping.context)[0].entity_uuid
        assert json.loads(context_item[2]) == list(sample_relation_span_context_mapping.context)[0].sub_type


@pytest.mark.asyncio
@patch('minerva_backend.processing.curation_manager.uuid4', side_effect=['new-rel-uuid-1'])
async def test_accept_relationship(mock_uuid4, curation_manager_db: CurationManager, sample_journal_entry,
                                   sample_relation_span_context_mapping, sample_relation):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        sample_journal_entry.uuid, [sample_relation_span_context_mapping]
    )

    curated_data = sample_relation.model_dump(mode='json')
    accepted_uuid = await curation_manager_db.accept_relationship(
        sample_journal_entry.uuid, sample_relation.uuid, curated_data
    )
    assert accepted_uuid == sample_relation.uuid

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status, curated_data_json FROM relationship_curation_items WHERE uuid = ?",
            (sample_relation.uuid,)
        )
        status, data_json = await cursor.fetchone()
        assert status == "ACCEPTED"
        assert json.loads(data_json) == curated_data

    # Test user-added relationship
    user_added_data = {
        "source": "p1",
        "target": "p2",
        "type": "RELATED_TO",
        "proposed_types": ["FRIENDS_WITH"],
        "summary_short": "User created relationship",
        "summary": "A relationship that was manually created by the user during curation"
    }
    user_added_uuid = await curation_manager_db.accept_relationship(
        sample_journal_entry.uuid, "any-uuid", user_added_data, is_user_added=True
    )
    assert user_added_uuid == "new-rel-uuid-1"

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status, curated_data_json, is_user_added FROM relationship_curation_items WHERE uuid = ?",
            ("new-rel-uuid-1",)
        )
        status, data_json, is_user_added = await cursor.fetchone()
        assert status == "ACCEPTED"
        assert json.loads(data_json) == user_added_data
        assert is_user_added is 1


@pytest.mark.asyncio
async def test_reject_relationship(curation_manager_db: CurationManager, sample_journal_entry,
                                   sample_relation_span_context_mapping):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        sample_journal_entry.uuid, [sample_relation_span_context_mapping]
    )

    rejected = await curation_manager_db.reject_relationship(
        sample_journal_entry.uuid, sample_relation_span_context_mapping.relation.uuid
    )
    assert rejected is True

    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute(
            "SELECT status FROM relationship_curation_items WHERE uuid = ?",
            (sample_relation_span_context_mapping.relation.uuid,)
        )
        status = (await cursor.fetchone())[0]
        assert status == "REJECTED"

    # Test rejecting a non-existent relationship
    rejected_non_existent = await curation_manager_db.reject_relationship(sample_journal_entry.uuid, "non-existent")
    assert rejected_non_existent is False


@pytest.mark.asyncio
async def test_get_accepted_relationships_with_spans(curation_manager_db: CurationManager, sample_journal_entry,
                                                     sample_relation_span_context_mapping, sample_relation,
                                                     sample_span, sample_relationship_context):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        sample_journal_entry.uuid, [sample_relation_span_context_mapping]
    )
    await curation_manager_db.accept_relationship(
        sample_journal_entry.uuid, sample_relation.uuid, sample_relation.model_dump(mode='json')
    )

    accepted_relationships = await curation_manager_db.get_accepted_relationships_with_spans(sample_journal_entry.uuid)
    assert len(accepted_relationships) == 1
    result_relation_mapping = accepted_relationships[0]
    assert result_relation_mapping.relation.uuid == sample_relation.uuid
    assert result_relation_mapping.relation.type == sample_relation.type
    assert result_relation_mapping.spans == [sample_span]
    assert result_relation_mapping.context == [sample_relationship_context]

    # Test with no accepted relationships
    await curation_manager_db.reject_relationship(sample_journal_entry.uuid, sample_relation.uuid)
    no_accepted = await curation_manager_db.get_accepted_relationships_with_spans(sample_journal_entry.uuid)
    assert len(no_accepted) == 0


@pytest.mark.asyncio
async def test_complete_relationship_phase(curation_manager_db: CurationManager, sample_journal_entry):
    await curation_manager_db.create_journal_for_curation(sample_journal_entry.uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(sample_journal_entry.uuid, 'PENDING_RELATIONS')
    await curation_manager_db.complete_relationship_phase(sample_journal_entry.uuid)
    status = await curation_manager_db.get_journal_status(sample_journal_entry.uuid)
    assert status == "COMPLETED"


@pytest.mark.asyncio
async def test_get_all_pending_curation_tasks(curation_manager_db: CurationManager, sample_journal_entry,
                                              sample_entity_span_mapping, sample_relation_span_context_mapping):
    journal_uuid_e = "journal-entity-pending"
    journal_uuid_r = "journal-relation-pending"
    journal_uuid_done = "journal-done"

    # Journal pending entities
    await curation_manager_db.queue_entities_for_curation(
        journal_uuid_e, "Entity pending text", [sample_entity_span_mapping]
    )

    # Journal pending relationships
    await curation_manager_db.create_journal_for_curation(journal_uuid_r, "Relation pending text")
    await curation_manager_db.update_journal_status(journal_uuid_r, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid_r, [sample_relation_span_context_mapping]
    )

    # Journal completed
    await curation_manager_db.create_journal_for_curation(journal_uuid_done, "Completed text")
    await curation_manager_db.update_journal_status(journal_uuid_done, 'COMPLETED')

    all_tasks = await curation_manager_db.get_all_pending_curation_tasks()

    # Filter journals by pending entity tasks
    entity_journals = [j for j in all_tasks if any(t.type == 'entity' for t in j.tasks)]
    # Filter journals by pending relationship tasks
    relationship_journals = [j for j in all_tasks if any(t.type == 'relationship' for t in j.tasks)]

    assert len(all_tasks) == 2
    assert len(entity_journals) == 1
    assert entity_journals[0].journal_id == journal_uuid_e
    assert len(relationship_journals) == 1
    assert relationship_journals[0].journal_id == journal_uuid_r


@pytest.mark.asyncio
async def test_get_curation_stats(curation_manager_db: CurationManager, sample_journal_entry,
                                  sample_entity_span_mapping, sample_relation_span_context_mapping):
    # Create multiple journals with different statuses to test all scenarios
    journal1_uuid = "journal-pending-entities"
    journal2_uuid = "journal-pending-relations"
    journal3_uuid = "journal-completed"

    # Journal 1: Pending entities with mixed entity statuses
    entity2 = create_person("Jane Smith", "entity-2")
    span2 = create_span("Jane Smith", journal1_uuid, 10, 20, "span-2")
    entity_mapping2 = EntityMapping(entity=entity2, spans=[span2])
    await curation_manager_db.queue_entities_for_curation(
        journal1_uuid, "Journal 1 text", [sample_entity_span_mapping, entity_mapping2]
    )
    await curation_manager_db.accept_entity(journal1_uuid, entity2.uuid, entity2.model_dump())

    # Journal 2: Pending relationships with mixed relationship statuses
    await curation_manager_db.create_journal_for_curation(journal2_uuid, "Journal 2 text")
    await curation_manager_db.update_journal_status(journal2_uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        journal2_uuid, [sample_relation_span_context_mapping]
    )
    # Add another relationship and reject it
    rel2 = create_relation("source-2", "target-2", "RELATED_TO", "rel-2")
    span3 = create_span("relationship text", journal2_uuid, 0, 10, "span-3")
    rel_mapping2 = RelationSpanContextMapping(relation=rel2, spans=[span3], context=[])
    await curation_manager_db.queue_relationships_for_curation(journal2_uuid, [rel_mapping2])
    await curation_manager_db.reject_relationship(journal2_uuid, rel2.uuid)

    # Journal 3: Completed
    await curation_manager_db.create_journal_for_curation(journal3_uuid, "Journal 3 text")
    await curation_manager_db.update_journal_status(journal3_uuid, 'COMPLETED')

    # Get stats
    stats = await curation_manager_db.get_curation_stats()

    # Verify basic journal counts
    assert stats.total_journals == 3
    assert stats.pending_entities == 1  # journal1_uuid
    assert stats.pending_relationships == 1  # journal2_uuid
    assert stats.completed == 1  # journal3_uuid

    # Verify entity stats
    assert stats.entity_stats.total_extracted == 2
    assert stats.entity_stats.accepted == 1
    assert stats.entity_stats.rejected == 0
    assert stats.entity_stats.pending == 1
    assert stats.entity_stats.acceptance_rate == 1.0  # 1 accepted / 1 processed

    # Verify relationship stats
    assert stats.relationship_stats.total_extracted == 2
    assert stats.relationship_stats.accepted == 0
    assert stats.relationship_stats.rejected == 1
    assert stats.relationship_stats.pending == 1
    assert stats.relationship_stats.acceptance_rate == 0.0  # 0 accepted / 1 processed


@pytest.mark.asyncio
async def test_clear_all(curation_manager_db: CurationManager, sample_journal_entry,
                         sample_entity_span_mapping, sample_relation_span_context_mapping):
    # First, populate the database with data
    journal_uuid = sample_journal_entry.uuid

    # Add entities
    await curation_manager_db.queue_entities_for_curation(
        journal_uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )

    # Add relationships
    await curation_manager_db.update_journal_status(journal_uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid, [sample_relation_span_context_mapping]
    )

    # Verify data exists before clearing
    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM journal_curation")
        journal_count = (await cursor.fetchone())[0]
        assert journal_count > 0

        cursor = await db.execute("SELECT COUNT(*) FROM entity_curation_items")
        entity_count = (await cursor.fetchone())[0]
        assert entity_count > 0

        cursor = await db.execute("SELECT COUNT(*) FROM relationship_curation_items")
        rel_count = (await cursor.fetchone())[0]
        assert rel_count > 0

        cursor = await db.execute("SELECT COUNT(*) FROM span_curation_items")
        span_count = (await cursor.fetchone())[0]
        assert span_count > 0

        cursor = await db.execute("SELECT COUNT(*) FROM relationship_context_items")
        context_count = (await cursor.fetchone())[0]
        assert context_count > 0

    # Clear all data
    await curation_manager_db.clear_all()

    # Verify all tables are empty
    async with aiosqlite.connect(curation_manager_db.db_path) as db:
        tables = ["journal_curation", "entity_curation_items", "relationship_curation_items",
                  "span_curation_items", "relationship_context_items"]

        for table in tables:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {table}")
            count = (await cursor.fetchone())[0]
            assert count == 0, f"Table {table} should be empty after clear_all()"

    # Verify get_curation_stats returns zeros after clearing
    stats = await curation_manager_db.get_curation_stats()
    assert stats.total_journals == 0
    assert stats.pending_entities == 0
    assert stats.pending_relationships == 0
    assert stats.completed == 0
    assert stats.entity_stats.total_extracted == 0
    assert stats.relationship_stats.total_extracted == 0
