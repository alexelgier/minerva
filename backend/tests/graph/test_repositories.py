def test_person_crud(person_repo, sample_person):
    """Test CRUD operations for PersonRepository."""
    # Create
    person_uuid = person_repo.create(sample_person)
    assert person_uuid is not None

    # Read
    retrieved = person_repo.find_by_id(person_uuid)
    assert retrieved is not None
    assert retrieved.name == sample_person.name
    assert retrieved.occupation == sample_person.occupation

    # Delete
    assert person_repo.delete(person_uuid)
    assert person_repo.find_by_id(person_uuid) is None


def test_feeling_crud(feeling_repo, sample_feeling):
    """Test CRUD operations for FeelingRepository."""
    # Create
    feeling_uuid = feeling_repo.create(sample_feeling)
    assert feeling_uuid is not None

    # Read
    retrieved = feeling_repo.find_by_id(feeling_uuid)
    assert retrieved.intensity == sample_feeling.intensity

    # Delete
    assert feeling_repo.delete(feeling_uuid)


def test_event_crud(event_repo, sample_event):
    """Test CRUD operations for EventRepository."""
    # Create
    event_uuid = event_repo.create(sample_event)
    assert event_uuid is not None

    # Read
    retrieved = event_repo.find_by_id(event_uuid)
    assert retrieved.name == sample_event.name

    # Delete
    assert event_repo.delete(event_uuid)


def test_project_crud(project_repo, sample_project):
    """Test CRUD operations for ProjectRepository."""
    # Create
    project_uuid = project_repo.create(sample_project)
    assert project_uuid is not None

    # Read
    retrieved = project_repo.find_by_id(project_uuid)
    assert retrieved.name == sample_project.name

    # Delete
    assert project_repo.delete(project_uuid)


def test_concept_crud(concept_repo, sample_concept):
    """Test CRUD operations for ConceptRepository."""
    # Create
    concept_uuid = concept_repo.create(sample_concept)
    assert concept_uuid is not None

    # Read
    retrieved = concept_repo.find_by_id(concept_uuid)
    assert retrieved.name == sample_concept.name

    # Delete
    assert concept_repo.delete(concept_uuid)


def test_content_crud(content_repo, sample_content):
    """Test CRUD operations for ContentRepository."""
    # Create
    content_uuid = content_repo.create(sample_content)
    assert content_uuid is not None

    # Read
    retrieved = content_repo.find_by_id(content_uuid)
    assert retrieved.name == sample_content.name

    # Delete
    assert content_repo.delete(content_uuid)


def test_journal_entry_crud(journal_entry_repo, sample_journal_entry):
    """Test CRUD operations for JournalEntryRepository."""
    # Create
    entry_uuid = journal_entry_repo.create(sample_journal_entry)
    assert entry_uuid is not None

    # Read
    retrieved = journal_entry_repo.find_by_id(entry_uuid)
    assert retrieved.text == sample_journal_entry.text

    # Delete
    assert journal_entry_repo.delete(entry_uuid)
