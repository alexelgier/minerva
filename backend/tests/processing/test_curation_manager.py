import json
import os
import tempfile
from datetime import date
from unittest.mock import patch

import aiosqlite
import pytest
import pytest_asyncio

from minerva_backend.graph.models.documents import Span, JournalEntry
from minerva_backend.graph.models.entities import Person, EntityType
from minerva_backend.graph.models.relations import Relation, RelationshipType
from minerva_backend.processing.curation_manager import CurationManager
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_relationships import RelationshipContext


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
    return EntitySpanMapping(entity=sample_person_entity, spans={sample_span})


@pytest_asyncio.fixture
def sample_relation():
    return Relation(
        uuid="relation-xyz",
        source="person-abc",
        target="person-def",
        proposed_types=["KNOWS", "WORKS_WITH"],
        summary_short="A test relationship between two people",
        summary="A comprehensive test relationship used for validating the curation system's relationship handling capabilities"
    )


@pytest_asyncio.fixture
def sample_relationship_context():
    return RelationshipContext(entity_uuid="person-abc", sub_type=["subject"])


@pytest_asyncio.fixture
def sample_relation_span_context_mapping(sample_relation, sample_span, sample_relationship_context):
    return RelationSpanContextMapping(
        relation=sample_relation,
        spans={sample_span},
        context={sample_relationship_context}
    )


@pytest.mark.asyncio
async def test_initialize(curation_manager_db: CurationManager):
    # The fixture already calls initialize, so we just need to verify tables exist
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
    assert result_entity_mapping.spans == {sample_span}

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
    assert result_relation_mapping.spans == {sample_span}
    assert result_relation_mapping.context == {sample_relationship_context}

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
async def test_get_journals_pending_entity_curation(curation_manager_db: CurationManager, sample_journal_entry,
                                                    sample_entity_span_mapping, sample_person_entity):
    journal_uuid = sample_journal_entry.uuid
    entity_uuid = sample_entity_span_mapping.entity.uuid

    await curation_manager_db.queue_entities_for_curation(
        journal_uuid, sample_journal_entry.text, [sample_entity_span_mapping]
    )

    pending_journals = await curation_manager_db.get_journals_pending_entity_curation()
    assert len(pending_journals) == 1
    journal_data = pending_journals[0]
    assert journal_data["journal_id"] == journal_uuid
    assert journal_data["journal_text"] == sample_journal_entry.text
    assert journal_data["pending_entities_count"] == 1
    assert journal_data["phase"] == "entities"
    assert len(journal_data["pending_entities"]) == 1
    pending_entity = journal_data["pending_entities"][0]
    assert pending_entity["id"] == entity_uuid
    assert pending_entity["entity_type"] == sample_person_entity.type
    assert pending_entity["status"] == "PENDING"
    assert pending_entity["name"] == sample_person_entity.name

    # Complete entity phase, should no longer be pending
    await curation_manager_db.complete_entity_phase(journal_uuid)
    pending_journals_after_complete = await curation_manager_db.get_journals_pending_entity_curation()
    assert len(pending_journals_after_complete) == 0


@pytest.mark.asyncio
async def test_get_journals_pending_relationship_curation(curation_manager_db: CurationManager, sample_journal_entry,
                                                          sample_relation_span_context_mapping, sample_relation):
    journal_uuid = sample_journal_entry.uuid
    relation_uuid = sample_relation_span_context_mapping.relation.uuid

    await curation_manager_db.create_journal_for_curation(journal_uuid, sample_journal_entry.text)
    await curation_manager_db.update_journal_status(journal_uuid, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid, [sample_relation_span_context_mapping]
    )

    pending_journals = await curation_manager_db.get_journals_pending_relationship_curation()
    assert len(pending_journals) == 1
    journal_data = pending_journals[0]
    assert journal_data["journal_id"] == journal_uuid
    assert journal_data["journal_text"] == sample_journal_entry.text
    assert journal_data["pending_relationships_count"] == 1
    assert journal_data["phase"] == "relationships"
    assert len(journal_data["pending_relationships"]) == 1
    pending_relationship = journal_data["pending_relationships"][0]
    assert pending_relationship["id"] == relation_uuid
    assert pending_relationship["relationship_type"] == sample_relation.type
    assert pending_relationship["status"] == "PENDING"
    assert pending_relationship["source"] == sample_relation.source
    assert pending_relationship["target"] == sample_relation.target

    # Complete relationship phase, should no longer be pending
    await curation_manager_db.complete_relationship_phase(journal_uuid)
    pending_journals_after_complete = await curation_manager_db.get_journals_pending_relationship_curation()
    assert len(pending_journals_after_complete) == 0


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

    assert all_tasks["total_pending_journals"] == 2
    assert len(all_tasks["entity_journals"]) == 1
    assert all_tasks["entity_journals"][0]["journal_id"] == journal_uuid_e
    assert len(all_tasks["relationship_journals"]) == 1
    assert all_tasks["relationship_journals"][0]["journal_id"] == journal_uuid_r


@pytest.mark.asyncio
async def test_get_curation_stats(curation_manager_db: CurationManager,
                                  sample_journal_entry,
                                  sample_entity_span_mapping,
                                  sample_relation_span_context_mapping,
                                  sample_person_entity,
                                  sample_relation):
    # Setup journals with different overall statuses
    journal_uuid_pe = "journal-pending-entities"
    journal_uuid_ed = "journal-entities-done"
    journal_uuid_pr = "journal-pending-relations"
    journal_uuid_comp = "journal-completed"

    await curation_manager_db.create_journal_for_curation(journal_uuid_pe, "Pending entities text")
    await curation_manager_db.create_journal_for_curation(journal_uuid_ed, "Entities done text")
    await curation_manager_db.update_journal_status(journal_uuid_ed, "ENTITIES_DONE")
    await curation_manager_db.create_journal_for_curation(journal_uuid_pr, "Pending relations text")
    await curation_manager_db.update_journal_status(journal_uuid_pr, "PENDING_RELATIONS")
    await curation_manager_db.create_journal_for_curation(journal_uuid_comp, "Completed text")
    await curation_manager_db.update_journal_status(journal_uuid_comp, "COMPLETED")

    # Setup entity curation items
    entity_uuid_pending = str(sample_person_entity.uuid)
    entity_uuid_accepted = "entity-accepted-1"
    entity_uuid_rejected = "entity-rejected-1"

    await curation_manager_db.queue_entities_for_curation(
        journal_uuid_pe, "some text", [sample_entity_span_mapping]
    )
    # Add an accepted entity to a different journal (or same, for entity counts)
    await curation_manager_db.queue_entities_for_curation(
        journal_uuid_ed, "some text", [EntitySpanMapping(entity=sample_person_entity.model_copy(update={'uuid': entity_uuid_accepted}), spans=sample_entity_span_mapping.spans)]
    )
    await curation_manager_db.accept_entity(journal_uuid_ed, entity_uuid_accepted, sample_person_entity.model_copy(update={'uuid': entity_uuid_accepted}).model_dump())

    # Add a rejected entity
    await curation_manager_db.queue_entities_for_curation(
        journal_uuid_pr, "some text", [EntitySpanMapping(entity=sample_person_entity.model_copy(update={'uuid': entity_uuid_rejected}), spans=sample_entity_span_mapping.spans)]
    )
    await curation_manager_db.reject_entity(journal_uuid_pr, entity_uuid_rejected)

    # Setup relationship curation items
    rel_uuid_pending = str(sample_relation.uuid)
    rel_uuid_accepted = "rel-accepted-1"
    rel_uuid_rejected = "rel-rejected-1"

    # Queue pending relationship for journal_uuid_pr
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid_pr, [sample_relation_span_context_mapping]
    )

    # Queue and accept a relationship
    await curation_manager_db.update_journal_status(journal_uuid_comp, 'ENTITIES_DONE') # Temporarily set to ENTITIES_DONE to queue relationships
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid_comp, [RelationSpanContextMapping(relation=sample_relation.model_copy(update={'uuid': rel_uuid_accepted}), spans=sample_relation_span_context_mapping.spans, context=sample_relation_span_context_mapping.context)]
    )
    await curation_manager_db.accept_relationship(journal_uuid_comp, rel_uuid_accepted, sample_relation.model_copy(update={'uuid': rel_uuid_accepted}).model_dump())
    await curation_manager_db.update_journal_status(journal_uuid_comp, 'COMPLETED') # Reset status

    # Queue and reject a relationship
    journal_uuid_temp_rel_rej = "journal-temp-rel-rej"
    await curation_manager_db.create_journal_for_curation(journal_uuid_temp_rel_rej, "Temp rel rej text")
    await curation_manager_db.update_journal_status(journal_uuid_temp_rel_rej, 'ENTITIES_DONE')
    await curation_manager_db.queue_relationships_for_curation(
        journal_uuid_temp_rel_rej, [RelationSpanContextMapping(relation=sample_relation.model_copy(update={'uuid': rel_uuid_rejected}), spans=sample_relation_span_context_mapping.spans, context=sample_relation_span_context_mapping.context)]
    )
    await curation_manager_db.reject_relationship(journal_uuid_temp_rel_rej, rel_uuid_rejected)


    stats = await curation_manager_db.get_curation_stats()

    assert stats["journals_pending_entities"] == 1
    assert stats["journals_entities_done"] == 1
    assert stats["journals_pending_relations"] == 1
    assert stats["journals_completed"] == 1
    assert stats["entities_pending"] == 1
    assert stats["entities_accepted"] == 1
    assert stats["entities_rejected"] == 1
    assert stats["relationships_pending"] == 1
    assert stats["relationships_accepted"] == 1
    assert stats["relationships_rejected"] == 1
