from datetime import date

from minerva_backend.graph.models.documents import JournalEntry
from minerva_backend.graph.models.entities import Person


def test_person_crud(person_repo, sample_person):
    """Test CRUD operations for PersonRepository."""
    # Create
    person_uuid = person_repo.create(sample_person)
    assert person_uuid is not None

    # Read
    retrieved = person_repo.find_by_uuid(person_uuid)
    assert retrieved is not None
    assert retrieved.name == sample_person.name
    assert retrieved.occupation == sample_person.occupation

    # Delete
    assert person_repo.delete(person_uuid)
    assert person_repo.find_by_uuid(person_uuid) is None


def test_feeling_crud(feeling_repo, sample_feeling):
    """Test CRUD operations for FeelingRepository."""
    # Create
    feeling_uuid = feeling_repo.create(sample_feeling)
    assert feeling_uuid is not None

    # Read
    retrieved = feeling_repo.find_by_uuid(feeling_uuid)
    assert retrieved.intensity == sample_feeling.intensity

    # Delete
    assert feeling_repo.delete(feeling_uuid)


def test_event_crud(event_repo, sample_event):
    """Test CRUD operations for EventRepository."""
    # Create
    event_uuid = event_repo.create(sample_event)
    assert event_uuid is not None

    # Read
    retrieved = event_repo.find_by_uuid(event_uuid)
    assert retrieved.name == sample_event.name

    # Delete
    assert event_repo.delete(event_uuid)


def test_project_crud(project_repo, sample_project):
    """Test CRUD operations for ProjectRepository."""
    # Create
    project_uuid = project_repo.create(sample_project)
    assert project_uuid is not None

    # Read
    retrieved = project_repo.find_by_uuid(project_uuid)
    assert retrieved.name == sample_project.name

    # Delete
    assert project_repo.delete(project_uuid)


def test_concept_crud(concept_repo, sample_concept):
    """Test CRUD operations for ConceptRepository."""
    # Create
    concept_uuid = concept_repo.create(sample_concept)
    assert concept_uuid is not None

    # Read
    retrieved = concept_repo.find_by_uuid(concept_uuid)
    assert retrieved.name == sample_concept.name

    # Delete
    assert concept_repo.delete(concept_uuid)


def test_content_crud(content_repo, sample_content):
    """Test CRUD operations for ContentRepository."""
    # Create
    content_uuid = content_repo.create(sample_content)
    assert content_uuid is not None

    # Read
    retrieved = content_repo.find_by_uuid(content_uuid)
    assert retrieved.name == sample_content.name

    # Delete
    assert content_repo.delete(content_uuid)


def test_journal_entry_crud(journal_entry_repo, sample_journal_entry):
    """Test CRUD operations for JournalEntryRepository."""
    # Create
    entry_uuid = journal_entry_repo.create(sample_journal_entry)
    assert entry_uuid is not None

    # Read
    retrieved = journal_entry_repo.find_by_uuid(entry_uuid)
    assert retrieved.text == sample_journal_entry.text

    # Delete
    assert journal_entry_repo.delete(entry_uuid)


def test_person_repository_specialized_queries(person_repo):
    """Test specialized query methods for PersonRepository."""
    # Setup: Create a few sample persons
    p1_data = Person(name="Alice Smith", occupation="Engineer", birth_date=date(1990, 5, 15))
    p2_data = Person(name="Bob Johnson", occupation="Engineer", birth_date=date(1985, 8, 20))
    p3_data = Person(name="Charlie Brown", occupation="Artist", birth_date=date(1990, 1, 10))
    p1_uuid = person_repo.create(p1_data)
    p2_uuid = person_repo.create(p2_data)
    p3_uuid = person_repo.create(p3_data)

    try:
        # Test find_by_occupation
        engineers = person_repo.find_by_occupation("Engineer")
        assert len(engineers) == 2
        assert {p.name for p in engineers} == {"Alice Smith", "Bob Johnson"}

        # Test find_by_birth_year
        born_1990 = person_repo.find_by_birth_year(1990)
        assert len(born_1990) == 2
        assert {p.name for p in born_1990} == {"Alice Smith", "Charlie Brown"}

        # Test search_by_name_partial
        smiths = person_repo.search_by_name_partial("smith")
        assert len(smiths) == 1
        assert smiths[0].name == "Alice Smith"

        # Test get_statistics (basic check)
        stats = person_repo.get_statistics()
        assert "total_persons" in stats
        assert stats["total_persons"] >= 3

    finally:
        # Teardown
        person_repo.delete(p1_uuid)
        person_repo.delete(p2_uuid)
        person_repo.delete(p3_uuid)


def test_get_persons_with_recent_mentions(person_repo, journal_entry_repo, db_connection):
    """Test retrieving persons with recent mentions."""
    # Setup
    p_mentioned_data = Person(name="Mentioned Person")
    j_recent_data = JournalEntry(text="Recent entry", date=date.today())

    p_mentioned_uuid = person_repo.create(p_mentioned_data)
    j_recent_uuid = journal_entry_repo.create(j_recent_data)

    # Manually create relationship
    query = """
    MATCH (p:Person {uuid: $p_uuid}), (j:JournalEntry {uuid: $j_uuid})
    CREATE (p)-[:MENTIONED_IN]->(j)
    """
    with db_connection.session() as session:
        session.run(query, p_uuid=p_mentioned_uuid, j_uuid=j_recent_uuid)

    try:
        # Test get_persons_with_recent_mentions (default 30 days)
        recent_mentions = person_repo.get_persons_with_recent_mentions()
        assert len(recent_mentions) == 1
        assert recent_mentions[0].uuid == p_mentioned_uuid

    finally:
        # Teardown
        person_repo.delete(p_mentioned_uuid)
        journal_entry_repo.delete(j_recent_uuid)


def test_journal_entry_repository_specialized_queries(journal_entry_repo):
    """Test specialized query methods for JournalEntryRepository."""
    # Setup
    d1 = date(2023, 1, 15)
    d2 = date(2023, 1, 20)
    d3 = date(2023, 2, 1)

    j1_data = JournalEntry(text="Entry 1", date=d1)
    j2_data = JournalEntry(text="Entry 2", date=d2)
    j3_data = JournalEntry(text="Entry 3", date=d3)

    j1_uuid = journal_entry_repo.create(j1_data)
    j2_uuid = journal_entry_repo.create(j2_data)
    j3_uuid = journal_entry_repo.create(j3_data)

    try:
        # Test find_by_date
        entry = journal_entry_repo.find_by_date(d1)
        assert entry is not None
        assert entry.uuid == j1_uuid

        # Test find_by_date_range
        entries_in_jan = journal_entry_repo.find_by_date_range(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31)
        )
        assert len(entries_in_jan) == 2
        assert {e.uuid for e in entries_in_jan} == {j1_uuid, j2_uuid}

        # Test get_statistics (basic check)
        stats = journal_entry_repo.get_statistics()
        assert "total_entries" in stats
        assert stats["total_entries"] >= 3
        assert stats["oldest_entry_date"] <= d1
        assert stats["newest_entry_date"] >= d3

    finally:
        # Teardown
        journal_entry_repo.delete(j1_uuid)
        journal_entry_repo.delete(j2_uuid)
        journal_entry_repo.delete(j3_uuid)
