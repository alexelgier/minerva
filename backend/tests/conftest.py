import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from uuid import uuid4
from datetime import datetime, date

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import (
    Person, Feeling, Event, Project, Concept, Consumable, Content, Emotion, ProjectStatus, ResourceType, ResourceStatus
)
from minerva_backend.graph.models.relations import Relation
from minerva_backend.graph.repositories import (
    PersonRepository, FeelingRepository, EventRepository, ProjectRepository,
    ConceptRepository, ContentRepository, ConsumableRepository,
    EmotionRepository, JournalEntryRepository
)
from minerva_backend.processing.models import EntitySpanMapping, RelationSpanContextMapping


@pytest.fixture(scope="session")
def test_db_connection():
    """
    Provides a Neo4j connection specifically for testing.
    Uses a separate test database to avoid interfering with production data.
    """
    # Use environment variables or default test database settings
    test_uri = os.getenv("NEO4J_TEST_URI", "bolt://localhost:7687")
    test_username = os.getenv("NEO4J_TEST_USERNAME", "neo4j")
    test_password = os.getenv("NEO4J_TEST_PASSWORD", "Alxe342!")
    test_database = os.getenv("NEO4J_TEST_DATABASE", "testdb")  # Separate test database

    connection = Neo4jConnection(
        uri=test_uri,
        user=test_username,
        password=test_password,
        database=test_database
    )

    yield connection

    # Clean up connection after all tests
    connection.close()


@pytest.fixture(scope="function")
def db_connection(test_db_connection):
    """
    Function-scoped fixture that provides a clean database for each test.
    Clears the test database before and after each test.
    """
    # Clean database before test
    _clear_test_database(test_db_connection)

    yield test_db_connection

    # Clean database after test
    _clear_test_database(test_db_connection)


def _clear_test_database(connection: Neo4jConnection):
    """
    Safely clears all data from the test database.
    Only use this on test databases!
    """
    with connection.session() as session:
        # Remove all relationships first
        session.run("MATCH ()-[r]->() DELETE r")
        # Then remove all nodes
        session.run("MATCH (n) DELETE n")
        # Clear any indexes or constraints if needed
        # session.run("DROP INDEX index_name IF EXISTS")


@pytest.fixture
def person_repo(db_connection):
    return PersonRepository(db_connection)


@pytest.fixture
def feeling_repo(db_connection):
    return FeelingRepository(db_connection)


@pytest.fixture
def event_repo(db_connection):
    return EventRepository(db_connection)


@pytest.fixture
def project_repo(db_connection):
    return ProjectRepository(db_connection)


@pytest.fixture
def concept_repo(db_connection):
    return ConceptRepository(db_connection)


@pytest.fixture
def content_repo(db_connection):
    return ContentRepository(db_connection)


@pytest.fixture
def consumable_repo(db_connection):
    return ConsumableRepository(db_connection)


@pytest.fixture
def emotion_repo(db_connection):
    return EmotionRepository(db_connection)


@pytest.fixture
def journal_entry_repo(db_connection):
    return JournalEntryRepository(db_connection)


@pytest.fixture
def sample_person():
    """Sample Person entity for testing."""
    return Person(
        name="Test User " + str(uuid4()),  # Add UUID to ensure uniqueness
        summary_short="A test user.",
        summary="A test user for software testing purposes.",
        occupation="Software Tester"
    )


@pytest.fixture
def sample_feeling():
    """Sample Feeling entity for testing."""
    return Feeling(
        name="Joy " + str(uuid4()),
        summary_short="A feeling of joy.",
        summary="A feeling of joy experienced upon test completion.",
        timestamp=datetime.now(),
        intensity=7
    )


@pytest.fixture
def sample_emotion():
    """Sample Emotion entity for testing."""
    return Emotion(
        name="Happiness " + str(uuid4()),
        summary_short="The emotion of happiness.",
        summary="A positive emotion, the state of being happy."
    )


@pytest.fixture
def sample_event():
    """Sample Event entity for testing."""
    return Event(
        name="Test Event " + str(uuid4()),
        summary_short="A test event.",
        summary="An event created for testing purposes.",
        category="work",
        date=datetime.now(),
        location="Test Location"
    )


@pytest.fixture
def sample_project():
    """Sample Project entity for testing."""
    return Project(
        name="Test Project " + str(uuid4()),
        summary_short="A test project.",
        summary="A project for testing purposes",
        status=ProjectStatus.ACTIVE,
        start_date=datetime.now()
    )


@pytest.fixture
def sample_concept():
    """Sample Concept entity for testing."""
    return Concept(
        name="Test Concept " + str(uuid4()),
        summary_short="A test concept.",
        summary="A concept for testing purposes.",
        title="Test Concept Title",
        analysis="A concept used for testing"
    )


@pytest.fixture
def sample_content():
    """Sample Content entity for testing."""
    return Content(
        name="Test Content " + str(uuid4()),
        summary_short="Test content.",
        summary="Content for testing purposes.",
        title="Test Content Title",
        category=ResourceType.MISC,
        author="Test Author",
        status=ResourceStatus.COMPLETED
    )


@pytest.fixture
def sample_consumable():
    """Sample Consumable entity for testing."""
    return Consumable(
        name="Test Consumable " + str(uuid4()),
        summary_short="A test consumable.",
        summary="A consumable item for testing purposes.",
        category="article"
    )


@pytest.fixture
def sample_journal_entry():
    """Sample JournalEntry document for testing."""
    return JournalEntry(
        uuid=str(uuid4()),
        date=date(2025, 9, 10),  # Wednesday, September 10, 2025
        text="""[[2025]] [[2025-09]] [[2025-09-10]]  Wednesday
    
    12:30, desperté, sin alarma. [[Ana Sorin|Ana]] me ayudo a despertarme, muy suave y amorosa. 
    
    Dejé mi celular anoche en lo de [[Federico Demarchi|Fede]].
    
    12:45, tomar [[Mate]] y ver [[Al Jazeera]]. [[Ana Sorin|Ana]] tiene que dar un seminario por [[remoto]], lo va hacer arriba en la habitación. 
    
    Charlé poco con [[Sady Antonia Baez|Sady]]. Estuve con [[Minerva]].
    
    15:00, vino [[Ana Sorin|Ana]], bastante molesta, angustiada, en el curso habían unas mujeres irrespetuosas que la dejaron desanimada. En todo caso le fue bien de todas formas a pesar de eso. 
    
    Estuvimos un rato charlando del curso, de [[Minerva]], leímos [[Vowels]] de [[Christian Bök]]. Pasamos un ratito lindo. Después estuvimos en el [[patio]] leyendo, yo [[Lenin]] [[Tomo IV]], [[Ana Sorin|Ana]] trabajando. 
    
    Limpié las [[piedritas]] de [[los gatos]].
    
    [[Ana Sorin|Ana]] se fué a [[terapia]] (tuvo [[remoto]], caminando por la calle). Yo me quedé trabajando en [[Minerva]].
    
    19:30, llegó ana, amorosa. Me invitó a [[Sexo|Jugar]], fue lindo. Le dije que primero tenía que hacer algunas cosas, pero que con mucho gusto en un rato podíamos.
    
    Me fui a lo de [[Federico Demarchi|Fede]], a buscar el celular que olvidé ahi anoche, y [[Cannabis|Porro]]. A la vuelta pasé por el [[Chino]] y compré para la [[Cena]]. 
    
    Puse a cocer [[Boniato]] y [[Remolacha]], y la invite a [[Ana Sorin|Ana]] a la habitación.
    
    Tuvimos muy lindo [[Sexo]]. [[Ana Sorin|Ana]] esta muy sexy, la disfruté enormemente. 
    
    Cenamos [[Ensalada de Remolacha y Huevo]], [[Puré de Boniato]], [[Ensalada]], y [[Milanesa de Soja|Suelas]]. Vimos un capítulo de [[One Piece]]. 
    
    [[Ana Sorin|Ana]] se quedo durmiendo en el sillón, y yo trabajando en [[Minerva]]. 
    
    05:45, trabajé muchas horas en [[Minerva]]. Estoy haciendo [[Graph RAG]] aún. Me hice un fork de [[Graphiti]] y estoy haciendo mi propio flujo de ingesta de entradas de diario. Dejé de hacer tantas pruebas con el [[LLM]] (que es costoso y tarda) y me puse a programar mejor. Que quede una primera version funcional antes de correrlo. Le hice una UI para curaduría. 
    
    Creo que va quedar muy bueno [[Minerva]].
    
    06:00, es tarde, tengo que dormir.
    
    ---
    ## Sleep
    Wake time: 12:30
    Bedtime: 06:30
    
    ---
    # 📝 Daily Wellbeing Check-in
    
    ## PANAS
    Rate each 1–5 (1 = very slightly, 5 = extremely)
    
    **Positive Affect**
    - Interested:: 5
    - Excited:: 4
    - Strong:: 3
    - Enthusiastic:: 4
    - Proud:: 3
    - Alert:: 2
    - Inspired:: 2
    - Determined:: 3
    - Attentive:: 3
    - Active:: 3
    
    **Negative Affect**
    - Distressed:: 1
    - Upset:: 2
    - Guilty:: 2
    - Scared:: 1
    - Hostile:: 1
    - Irritable:: 1
    - Ashamed:: 2
    - Nervous:: 2
    - Jittery:: 1
    - Afraid:: 2
    
    ---
    
    ## ## BPNS (Basic Psychological Needs)
    Rate each 1–7 
    
    **Autonomy**
    - I feel like I can make choices about the things I do:: 5
    - I feel free to decide how I do my daily tasks:: 5
    
    **Competence**
    - I feel capable at the things I do:: 6
    - I can successfully complete challenging tasks:: 5
    
    **Relatedness**
    - I feel close and connected with the people around me:: 5
    - I get along well with the people I interact with daily:: 5
    - I feel supported by others in my life:: 4
    
    ---
    
    ## Flourishing Scale
    Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)
    
    - I lead a purposeful and meaningful life:: 3
    - My social relationships are supportive and rewarding:: 5
    - I am engaged and interested in my daily activities:: 7
    - I actively contribute to the happiness and well-being of others:: 4
    - I am competent and capable in the activities that are important to me:: 5
    - I am a good person and live a good life:: 4
    - I am optimistic about my future:: 3
    - People respect me:: 3
    
    ---
    ## 📊 Scores""",
        entry_text="""12:30, desperté, sin alarma. [[Ana Sorin|Ana]] me ayudo a despertarme, muy suave y amorosa. 
    
    Dejé mi celular anoche en lo de [[Federico Demarchi|Fede]].
    
    12:45, tomar [[Mate]] y ver [[Al Jazeera]]. [[Ana Sorin|Ana]] tiene que dar un seminario por [[remoto]], lo va hacer arriba en la habitación. 
    
    Charlé poco con [[Sady Antonia Baez|Sady]]. Estuve con [[Minerva]].
    
    15:00, vino [[Ana Sorin|Ana]], bastante molesta, angustiada, en el curso habían unas mujeres irrespetuosas que la dejaron desanimada. En todo caso le fue bien de todas formas a pesar de eso. 
    
    Estuvimos un rato charlando del curso, de [[Minerva]], leímos [[Vowels]] de [[Christian Bök]]. Pasamos un ratito lindo. Después estuvimos en el [[patio]] leyendo, yo [[Lenin]] [[Tomo IV]], [[Ana Sorin|Ana]] trabajando. 
    
    Limpié las [[piedritas]] de [[los gatos]].
    
    [[Ana Sorin|Ana]] se fué a [[terapia]] (tuvo [[remoto]], caminando por la calle). Yo me quedé trabajando en [[Minerva]].
    
    19:30, llegó ana, amorosa. Me invitó a [[Sexo|Jugar]], fue lindo. Le dije que primero tenía que hacer algunas cosas, pero que con mucho gusto en un rato podíamos.
    
    Me fui a lo de [[Federico Demarchi|Fede]], a buscar el celular que olvidé ahi anoche, y [[Cannabis|Porro]]. A la vuelta pasé por el [[Chino]] y compré para la [[Cena]]. 
    
    Puse a cocer [[Boniato]] y [[Remolacha]], y la invite a [[Ana Sorin|Ana]] a la habitación.
    
    Tuvimos muy lindo [[Sexo]]. [[Ana Sorin|Ana]] esta muy sexy, la disfruté enormemente. 
    
    Cenamos [[Ensalada de Remolacha y Huevo]], [[Puré de Boniato]], [[Ensalada]], y [[Milanesa de Soja|Suelas]]. Vimos un capítulo de [[One Piece]]. 
    
    [[Ana Sorin|Ana]] se quedo durmiendo en el sillón, y yo trabajando en [[Minerva]]. 
    
    05:45, trabajé muchas horas en [[Minerva]]. Estoy haciendo [[Graph RAG]] aún. Me hice un fork de [[Graphiti]] y estoy haciendo mi propio flujo de ingesta de entradas de diario. Dejé de hacer tantas pruebas con el [[LLM]] (que es costoso y tarda) y me puse a programar mejor. Que quede una primera version funcional antes de correrlo. Le hice una UI para curaduría. 
    
    Creo que va quedar muy bueno [[Minerva]].
    
    06:00, es tarde, tengo que dormir.""",
        panas_positive=[5, 4, 3, 4, 3, 2, 2, 3, 3, 3],
        panas_negative=[1, 2, 2, 1, 1, 1, 2, 2, 1, 2],
        flourishing_score=[3, 5, 7, 4, 5, 4, 3, 3],
        bpns_autonomy=[5, 5],
        bpns_competence=[6, 5],
        bpns_relatedness=[5, 5, 4],
        sleep_bedtime=datetime(2025, 9, 11, 6, 30),  # Note: 06:30 is the next day
        sleep_wake_time=datetime(2025, 9, 10, 12, 30)
    )


@pytest.fixture
def sample_entity_span_mappings(sample_journal_entry):
    """Create sample EntitySpanMapping objects with proper structure"""
    # Create Person entity
    person = Person(
        uuid=str(uuid4()),
        name="María",
        summary_short="A person named María.",
        summary="A person named María, mentioned in the journal.",
        occupation="unknown"
    )
    person_span = Span(
        uuid=str(uuid4()),
        text="María",
        start_char=16,
        end_char=21,
        document_uuid=sample_journal_entry.uuid
    )
    person_mapping = EntitySpanMapping(
        entity=person,
        spans={person_span}
    )

    # Create Emotion entity
    emotion = Emotion(
        uuid=str(uuid4()),
        name="feliz",
        summary_short="A feeling of happiness.",
        summary="The emotion of happiness (feliz)."
    )
    emotion_span = Span(
        uuid=str(uuid4()),
        text="muy feliz",
        start_char=50,
        end_char=59,
        document_uuid=sample_journal_entry.uuid
    )
    emotion_mapping = EntitySpanMapping(
        entity=emotion,
        spans={emotion_span}
    )

    return [person_mapping, emotion_mapping]


@pytest.fixture
def sample_relation_span_mappings(sample_entity_span_mappings, sample_journal_entry):
    """Create sample RelationSpanContextMapping objects"""
    relation = Relation(
        uuid=str(uuid4()),
        source=sample_entity_span_mappings[0].entity.uuid,  # Person
        target=sample_entity_span_mappings[1].entity.uuid,  # Emotion
        proposed_types=["FEELS"],
        summary_short="Person feels an emotion.",
        summary="A relationship indicating a person is feeling a certain emotion."
    )

    relation_span = Span(
        uuid=str(uuid4()),
        text="hablé con María",
        start_char=5,
        end_char=20,
        document_uuid=sample_journal_entry.uuid
    )

    relation_mapping = RelationSpanContextMapping(
        relation=relation,
        spans={relation_span}
    )

    return [relation_mapping]


@pytest.fixture
def mock_container_for_temporal():
    """Mock container specifically for temporal tests"""
    container = MagicMock()

    # Mock extraction service
    extraction_service = AsyncMock()
    container.extraction_service.return_value = extraction_service

    # Mock curation manager
    curation_manager = AsyncMock()
    container.curation_manager.return_value = curation_manager

    # Mock knowledge graph service
    kg_service = MagicMock()
    container.kg_service.return_value = kg_service

    return container
