import uuid
from unittest.mock import Mock, AsyncMock

import pytest

from minerva_backend.graph.models.documents import JournalEntry, Span
from minerva_backend.graph.models.entities import Person
from minerva_backend.processing.extraction_service import ExtractionService
from minerva_backend.processing.models import EntityMapping, RelationSpanContextMapping
from minerva_backend.prompt.extract_people import People
from minerva_backend.prompt.extract_people import Person as ExtractedPerson


# Move these fixtures to module level so all test classes can use them
@pytest.fixture
def mock_connection():
    return Mock()


@pytest.fixture
def mock_llm_service():
    return Mock()


@pytest.fixture
def mock_obsidian_service():
    return Mock()


@pytest.fixture
def extraction_service(mock_connection, mock_llm_service, mock_obsidian_service):
    return ExtractionService(mock_connection, mock_llm_service, mock_obsidian_service)


@pytest.fixture
def sample_journal_entry():
    return JournalEntry(
        uuid=str(uuid.uuid4()),
        title="Test Entry",
        text="""[[2025]] [[2025-09]]  Monday

12:30, Desperté, [[Ana Sorin|Ana]] se estaba yendo y me ayudo a despertar amorosamente.

[[Sady Antonia Baez|Sady]] esta limpiando, está triste porque se fue [[Marcelo]]. Hablamos un rato, también le conté del conflicto sostenido con [[Ana Sorin|Ana]], de lo triste y asustado que estoy. Sady piensa que [[Ana Sorin|Ana]] ya no me quiere mas, o muy poquito, y que seguramente nos terminemos separando.

[[Minerva]] funcionó mal a la noche, está tardando como 1h por request.

Mañana es el [[cumpleaños]]  de [[Martin Alvarez Heymann|Martin]].

16:21, [[journaling|Escribir ésto]]. Debo dos dias anteriores de [[Diario]] que no llené. Mi [[Proyectos|Proyecto]] [[Minerva]] me esta quitando mucho tiempo, estoy muy enganchado. Elegí modelos mas reducidos: 8b y 1.7b. Saque [[LM Studio]] y ahora el embedding lo hice funcionar con [[Ollama]], hice mi propio cliente también, así no tengo que patchear tanto el código de librería. De hecho tengo varios patch hechos y tengo que ver como hago para no perderlos si hay un update de [[Graphiti]].

140s tardó Qwen3-8m (16384ctx) en el primer prompt (Entities). Quiero ver como le va con el de extraer Edges.


02:42 [[journaling|Escribir ésto]]. 
[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la charla de hoy 


---

- Imagen, Detalle:
- Momento, Secuencia:   

- 🌡️ Estado emocional predominante:  
- 🧍‍♂️ Sensaciones en el cuerpo:

---

clima: 
actividad_principal: 
lugar_principal: 
personas: 
proyectos: 
tags: []

---
## Sleep
Wake time: 
Bedtime: 
## Morning
[ ] Got sunlight within 1 hour of waking  
[ ] Did light movement (walk, stretch, etc)
## Food
[ ] First real meal within 2 hours of waking  
[ ] Second real meal (before 11 PM)

---
# 📝 Daily Wellbeing Check-in

## PANAS
Rate each 1–5 (1 = very slightly, 5 = extremely)

**Positive Affect**
- Interested:: 0
- Excited:: 0
- Strong:: 0
- Enthusiastic:: 0
- Proud:: 0
- Alert:: 0
- Inspired:: 0
- Determined:: 0
- Attentive:: 0
- Active:: 0

**Negative Affect**
- Distressed:: 0
- Upset:: 0
- Guilty:: 0
- Scared:: 0
- Hostile:: 0
- Irritable:: 0
- Ashamed:: 0
- Nervous:: 0
- Jittery:: 0
- Afraid:: 0

---

## ## BPNS (Basic Psychological Needs)
Rate each 1–7 

**Autonomy**
- I feel like I can make choices about the things I do:: 0
- I feel free to decide how I do my daily tasks:: 0

**Competence**
- I feel capable at the things I do:: 0
- I can successfully complete challenging tasks:: 0

**Relatedness**
- I feel close and connected with the people around me:: 0
- I get along well with the people I interact with daily:: 0
- I feel supported by others in my life:: 0

---

## Flourishing Scale
Rate each 1–7 (1 = strongly disagree, 7 = strongly agree)

- I lead a purposeful and meaningful life:: 0
- My social relationships are supportive and rewarding:: 0
- I am engaged and interested in my daily activities:: 0
- I actively contribute to the happiness and well-being of others:: 0
- I am competent and capable in the activities that are important to me:: 0
- I am a good person and live a good life:: 0
- I am optimistic about my future:: 0
- People respect me:: 0

---
## 📊 Scores
```dataviewjs
// Helper to get list item value
function getValue(text) {
    let line = dv.current().file.lists.find(l => l.text.startsWith(text + "::"));
    return line ? Number(line.text.split("::")[1]) : 0;
}

// PANAS Positive
let panasPosItems = ["Interested","Excited","Strong","Enthusiastic","Proud","Alert","Inspired","Determined","Attentive","Active"];
let panasPos = panasPosItems.map(getValue).reduce((a,b)=>a+b,0);
let panasPosScaled = (panasPos - 10) / (50 - 10) * 100;

// PANAS Negative
let panasNegItems = ["Distressed","Upset","Guilty","Scared","Hostile","Irritable","Ashamed","Nervous","Jittery","Afraid"];
let panasNeg = panasNegItems.map(getValue).reduce((a,b)=>a+b,0);
let panasNegScaled = (panasNeg - 10) / (50 - 10) * 100;
// BPNS
let autonomyItems = ["I feel like I can make choices about the things I do","I feel free to decide how I do my daily tasks"];
let competenceItems = ["I feel capable at the things I do","I can successfully complete challenging tasks"];
let relatednessItems = ["I feel close and connected with the people around me","I get along well with the people I interact with daily","I feel supported by others in my life"];

let autonomy = autonomyItems.map(getValue).reduce((a,b)=>a+b,0);
let competence = competenceItems.map(getValue).reduce((a,b)=>a+b,0);
let relatedness = relatednessItems.map(getValue).reduce((a,b)=>a+b,0);

// Scale each individually
let autonomyScaled = (autonomy - 2)/(14 - 2)*100; // 2 items, min 1 per item
let competenceScaled = (competence - 2)/(14 - 2)*100;
let relatednessScaled = (relatedness - 3)/(21 - 3)*100;

let bpnsTotal = autonomy + competence + relatedness;
let bpnsScaled = (bpnsTotal - 7)/(49 - 7)*100;

// Flourishing
let flourItems = [
  "I lead a purposeful and meaningful life",
  "My social relationships are supportive and rewarding",
  "I am engaged and interested in my daily activities",
  "I actively contribute to the happiness and well-being of others",
  "I am competent and capable in the activities that are important to me",
  "I am a good person and live a good life",
  "I am optimistic about my future",
  "People respect me"
];
let flourTotal = flourItems.map(getValue).reduce((a,b)=>a+b,0);
let flourScaled = (flourTotal - 8) / (56 - 8) * 100;

// OUTPUT
dv.paragraph(`**PANAS Positive:** ${panasPosScaled.toFixed(0)}%  
**PANAS Negative:** ${panasNegScaled.toFixed(0)}%  

**BPNS Total:** ${bpnsScaled.toFixed(0)}%  (A:${autonomyScaled.toFixed(0)}% - C:${competenceScaled.toFixed(0)}% -  R:${relatednessScaled.toFixed(0)}%) 

**Flourishing Total:** ${flourScaled.toFixed(0)}%`);
```
---

Lo que no dije (sin filtro):
""", entry_text="""[[2025]] [[2025-09]]  Monday

12:30, Desperté, [[Ana Sorin|Ana]] se estaba yendo y me ayudo a despertar amorosamente.

[[Sady Antonia Baez|Sady]] esta limpiando, está triste porque se fue [[Marcelo]]. Hablamos un rato, también le conté del conflicto sostenido con [[Ana Sorin|Ana]], de lo triste y asustado que estoy. Sady piensa que [[Ana Sorin|Ana]] ya no me quiere mas, o muy poquito, y que seguramente nos terminemos separando.

[[Minerva]] funcionó mal a la noche, está tardando como 1h por request.

Mañana es el [[cumpleaños]]  de [[Martin Alvarez Heymann|Martin]].

16:21, [[journaling|Escribir ésto]]. Debo dos dias anteriores de [[Diario]] que no llené. Mi [[Proyectos|Proyecto]] [[Minerva]] me esta quitando mucho tiempo, estoy muy enganchado. Elegí modelos mas reducidos: 8b y 1.7b. Saque [[LM Studio]] y ahora el embedding lo hice funcionar con [[Ollama]], hice mi propio cliente también, así no tengo que patchear tanto el código de librería. De hecho tengo varios patch hechos y tengo que ver como hago para no perderlos si hay un update de [[Graphiti]].

140s tardó Qwen3-8m (16384ctx) en el primer prompt (Entities). Quiero ver como le va con el de extraer Edges.


02:42 [[journaling|Escribir ésto]]. 
[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la charla de hoy 
""",
        date="2023-10-01"
    )


@pytest.fixture
def sample_person():
    return Person(
        uuid=str(uuid.uuid4()),
        name="Alex Elgier",
        summary="A longer summary about alex elgier saying some things",
        summary_short="Some things about alex elgier"
    )


@pytest.fixture
def sample_span_texts():
    return ["12:30, Desperté, [[Ana Sorin|Ana]] se estaba yendo y me ayudo a despertar amorosamente.",
            "Debo dos dias anteriores de [[Diario]] que no llené.",
            "Mi [[Proyectos|Proyecto]] [[Minerva]] me esta quitando mucho tiempo, estoy muy enganchado. ",
            "[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la charla de hoy "]


class TestExtractionService:
    class TestHydrateSpansForText:

        def test_exact_match_found(self, extraction_service, sample_journal_entry, sample_span_texts):
            spans = extraction_service.hydrate_spans_for_text(sample_span_texts, sample_journal_entry.entry_text)
            assert len(spans) == 4
            assert spans[0].text == ("12:30, Desperté, [[Ana Sorin|Ana]] se estaba yendo y me ayudo a despertar "
                                     "amorosamente.")
            assert spans[0].start == 30
            assert spans[0].end == 117
            assert spans[1].text == "Debo dos dias anteriores de [[Diario]] que no llené."
            assert spans[1].start == 611
            assert spans[1].end == 663
            assert spans[2].text == ("Mi [[Proyectos|Proyecto]] [[Minerva]] me esta quitando mucho tiempo, estoy muy "
                                     "enganchado. ")
            assert spans[2].start == 664
            assert spans[2].end == 755
            assert spans[3].text == ("[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la "
                                     "charla de hoy ")
            assert spans[3].start == 1220
            assert spans[3].end == 1310

        def test_case_insensitive_matching(self, extraction_service, sample_journal_entry, sample_span_texts):
            spans = extraction_service.hydrate_spans_for_text([t.upper() for t in sample_span_texts],
                                                              sample_journal_entry.entry_text)
            assert len(spans) == 4
            assert spans[0].text == ("12:30, Desperté, [[Ana Sorin|Ana]] se estaba yendo y me ayudo a despertar "
                                     "amorosamente.")
            assert spans[0].start == 30
            assert spans[0].end == 117
            assert sample_journal_entry.entry_text[spans[0].start:spans[0].end] == spans[0].text
            assert spans[1].text == "Debo dos dias anteriores de [[Diario]] que no llené."
            assert spans[1].start == 611
            assert spans[1].end == 663
            assert sample_journal_entry.entry_text[spans[1].start:spans[1].end] == spans[1].text
            assert spans[2].text == ("Mi [[Proyectos|Proyecto]] [[Minerva]] me esta quitando mucho tiempo, estoy muy "
                                     "enganchado. ")
            assert spans[2].start == 664
            assert spans[2].end == 755
            assert sample_journal_entry.entry_text[spans[2].start:spans[2].end] == spans[2].text
            assert spans[3].text == ("[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la "
                                     "charla de hoy ")
            assert spans[3].start == 1220
            assert spans[3].end == 1310
            assert sample_journal_entry.entry_text[spans[3].start:spans[3].end] == spans[3].text

        def test_fuzzy_phrase_matching(self, extraction_service, sample_journal_entry):
            # The span_text is similar but not identical to the phrase in entry_text
            span_texts = ["Debo dos dias de [[Diario]] que no llené.", "02:42 [[journaling|Escribir ésto]]. "
                                                                       "[[Ana Sorin|Ana]] vino a apagar la estufa, "
                                                                       "le di un abrazo y le agradecí la charla de hoy"]
            spans = extraction_service.hydrate_spans_for_text(span_texts, sample_journal_entry.entry_text)
            assert len(spans) == 2
            assert spans[0].text == "Debo dos dias anteriores de [[Diario]] que no llené."
            assert spans[0].start == 611
            assert spans[0].end == 663
            assert sample_journal_entry.entry_text[spans[0].start:spans[0].end] == spans[0].text
            assert spans[1].text == """02:42 [[journaling|Escribir ésto]]. 
[[Ana Sorin|Ana]] vino a apagar la estufa, le di un abrazo y le agradecí la charla de hoy"""
            assert spans[1].start == 1183
            assert spans[1].end == 1309
            assert sample_journal_entry.entry_text[spans[1].start:spans[1].end] == spans[1].text

        def test_no_match_found(self, extraction_service, sample_journal_entry):
            # The span_text does not appear in entry_text, and fuzzy also fails
            span_texts = ["Nonexistent Person"]
            spans = extraction_service.hydrate_spans_for_text(span_texts, sample_journal_entry.entry_text)
            assert spans == []

        def test_empty_span_texts(self, extraction_service):
            spans = extraction_service.hydrate_spans_for_text([], "some text")
            assert spans == []

        def test_empty_entry_text(self, extraction_service):
            spans = extraction_service.hydrate_spans_for_text(["John"], "")
            assert spans == []

    class TestFindBestPhraseMatch:

        def test_good_fuzzy_match(self, extraction_service, sample_journal_entry):
            target = "funcionó mal a la noche, tardó como 1h por request"
            text = sample_journal_entry.entry_text
            # Insert a known phrase for matching
            result = extraction_service._find_best_phrase_match(target, text)
            assert result is not None
            phrase, start, end, score = result
            assert phrase == "funcionó mal a la noche, está tardando como 1h por request."
            assert start == 445
            assert end == 504
            assert score >= 75

        def test_no_good_match_below_threshold(self, extraction_service, sample_journal_entry):
            target = "Completely Different search for nothing"
            text = sample_journal_entry.entry_text
            result = extraction_service._find_best_phrase_match(target, text, min_score=75)
            assert result is None

        def test_custom_min_score_threshold(self, extraction_service, sample_journal_entry):
            target = "[[Minerva]] mucho tiempo"  # Should match "John" with lower threshold
            text = sample_journal_entry.entry_text
            result = extraction_service._find_best_phrase_match(target, text, min_score=50)
            assert result is not None
            phrase, start, end, score = result
            assert phrase == "[[Minerva]] me"
            assert score >= 50

        def test_empty_target_span(self, extraction_service, sample_journal_entry):
            text = sample_journal_entry.entry_text
            with pytest.raises(Exception, match="Target span or text is empty"):
                extraction_service._find_best_phrase_match("", text)

        def test_empty_text(self, extraction_service, sample_journal_entry):
            target = "target"
            with pytest.raises(Exception, match="Target span or text is empty"):
                extraction_service._find_best_phrase_match(target, "")

    class TestBuildObsidianEntityLookup:

        @pytest.mark.asyncio
        async def test_extract_obsidian_links(self, extraction_service, sample_journal_entry):
            sample_journal_entry.entry_text = "I met [[John Smith]] and [[Sarah Jones]]."

            extraction_service.obsidian_service.resolve_link.side_effect = [
                {
                    'entity_name': 'John Smith',
                    'entity_long_name': 'John Smith',
                    'entity_id': 'uuid-1',
                    'aliases': ['Johnny'],
                    'short_summary': 'A colleague'
                },
                {
                    'entity_name': 'Sarah Jones',
                    'entity_long_name': 'Sarah Jones',
                    'entity_id': 'uuid-2',
                    'aliases': [],
                    'short_summary': 'Another colleague'
                },
                {
                    'entity_name': 'Alex Elgier',
                    'entity_long_name': 'Alex Elgier',
                    'entity_id': 'user-uuid',
                    'aliases': [],
                    'short_summary': 'The user'
                }
            ]

            result = await extraction_service._build_obsidian_entity_lookup(sample_journal_entry)

            assert 'John Smith' in result['name_lookup']
            assert 'Johnny' in result['name_lookup']  # Alias should be included
            assert 'Sarah Jones' in result['name_lookup']
            assert 'Alex Elgier' in result['name_lookup']  # Should always include user
            assert len(result['db_entities']) == 3  # All entities have IDs
            assert 'John Smith' in result['glossary']
            assert 'Sarah Jones' in result['glossary']

        @pytest.mark.asyncio
        async def test_entities_without_db_ids(self, extraction_service, sample_journal_entry):
            sample_journal_entry.entry_text = "I visited [[Coffee Shop]]."

            extraction_service.obsidian_service.resolve_link.side_effect = [
                {
                    'entity_name': 'Coffee Shop',
                    'entity_long_name': 'Coffee Shop',
                    'entity_id': None,  # No database ID
                    'aliases': [],
                    'short_summary': 'Local coffee place'
                },
                {
                    'entity_name': 'Alex Elgier',
                    'entity_long_name': 'Alex Elgier',
                    'entity_id': 'user-uuid',
                    'aliases': [],
                    'short_summary': 'The user'
                }
            ]

            result = await extraction_service._build_obsidian_entity_lookup(sample_journal_entry)

            assert 'Coffee Shop' in result['name_lookup']
            assert len(result['db_entities']) == 1  # Only Alex has an ID
            assert result['db_entities'][0]['entity_name'] == 'Alex Elgier'

        @pytest.mark.asyncio
        async def test_duplicate_removal_by_long_name(self, extraction_service, sample_journal_entry):
            sample_journal_entry.entry_text = "I met [[John]] and [[John Smith]]."  # Same person, different links

            extraction_service.obsidian_service.resolve_link.side_effect = [
                {
                    'entity_name': 'John',
                    'entity_long_name': 'John Smith',  # Same long name
                    'entity_id': 'uuid-1',
                    'aliases': [],
                    'short_summary': 'A colleague'
                },
                {
                    'entity_name': 'John Smith',
                    'entity_long_name': 'John Smith',  # Same long name
                    'entity_id': 'uuid-1',
                    'aliases': [],
                    'short_summary': 'A colleague'
                },
                {
                    'entity_name': 'Alex Elgier',
                    'entity_long_name': 'Alex Elgier',
                    'entity_id': 'user-uuid',
                    'aliases': [],
                    'short_summary': 'The user'
                }
            ]

            result = await extraction_service._build_obsidian_entity_lookup(sample_journal_entry)

            # Should only have one entry for John Smith despite duplicate links
            john_entities = [e for e in result['db_entities'] if e['entity_long_name'] == 'John Smith']
            assert len(john_entities) == 1

        @pytest.mark.asyncio
        async def test_no_obsidian_links_only_user(self, extraction_service, sample_journal_entry):
            sample_journal_entry.entry_text = "Just plain text with no links."

            extraction_service.obsidian_service.resolve_link.return_value = {
                'entity_name': 'Alex Elgier',
                'entity_long_name': 'Alex Elgier',
                'entity_id': 'user-uuid',
                'aliases': [],
                'short_summary': 'The user'
            }

            result = await extraction_service._build_obsidian_entity_lookup(sample_journal_entry)

            # Should still include Alex Elgier
            assert 'Alex Elgier' in result['name_lookup']
            assert len(result['db_entities']) == 1
            extraction_service.obsidian_service.resolve_link.assert_called_once_with("Alex Elgier")

    class TestProcessAndDeduplicatePeople:

        @pytest.mark.asyncio
        async def test_new_person_processing(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[
                ExtractedPerson(name="New Person", spans=["New Person"])
            ])
            obsidian_entities = {'name_lookup': {}, 'db_entities': [], 'glossary': {}}

            mock_person = Person(name="New Person", summary="A new person")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_person)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 1
            assert result[0]['entity'].name == "New Person"
            assert result[0]['canonical_name'] == "New Person"
            assert result[0]['had_existing_id'] is False
            extraction_service._hydrate_person.assert_called_once_with(sample_journal_entry, "New Person")

        @pytest.mark.asyncio
        async def test_existing_person_with_id_no_db_entity(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[
                ExtractedPerson(name="John Smith", spans=["John Smith"])
            ])
            obsidian_entities = {
                'name_lookup': {
                    'John Smith': {
                        'entity_long_name': 'John Smith',
                        'entity_id': 'existing-uuid'
                    }
                }
            }

            mock_hydrated = Person(name="John Smith", summary="Updated summary")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_hydrated)
            extraction_service.entity_repositories['Person'].find_by_uuid = Mock(return_value=None)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 1
            assert result[0]['entity'].uuid == 'existing-uuid'
            assert result[0]['had_existing_id'] is True
            # Should not call merge since no DB entity was found
            assert not hasattr(extraction_service, '_merge_entity_properties') or \
                   not extraction_service._merge_entity_properties.called

        @pytest.mark.asyncio
        async def test_existing_person_with_db_entity(self, extraction_service, sample_journal_entry, sample_person):
            llm_people = People(people=[
                ExtractedPerson(name="John Smith", spans=["John Smith"])
            ])
            obsidian_entities = {
                'name_lookup': {
                    'John Smith': {
                        'entity_long_name': 'John Smith',
                        'entity_id': 'existing-uuid'
                    }
                }
            }

            mock_hydrated = Person(name="John Smith", summary="Updated summary")
            merged_person = Person(name="John Smith", summary="Merged summary")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_hydrated)
            extraction_service.entity_repositories['Person'].find_by_uuid = Mock(return_value=sample_person)
            extraction_service._merge_entity_properties = AsyncMock(return_value=merged_person)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 1
            assert result[0]['entity'] == merged_person
            extraction_service._merge_entity_properties.assert_called_once_with(
                existing_entity=sample_person,
                new_entity=mock_hydrated
            )

        @pytest.mark.asyncio
        async def test_deduplication_by_canonical_name(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[
                ExtractedPerson(name="John Smith", spans=["John Smith"]),
                ExtractedPerson(name="John Smith", spans=["John"])  # Duplicate canonical name
            ])
            obsidian_entities = {'name_lookup': {}}

            mock_person = Person(name="John Smith", summary="A person")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_person)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 1  # Should deduplicate
            extraction_service._hydrate_person.assert_called_once()  # Only called once

        @pytest.mark.asyncio
        async def test_hydration_returns_none(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[
                ExtractedPerson(name="Failed Person", spans=["Failed Person"])
            ])
            obsidian_entities = {'name_lookup': {}}

            extraction_service._hydrate_person = AsyncMock(return_value=None)  # Hydration fails

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 0  # Should filter out failed hydrations

        @pytest.mark.asyncio
        async def test_alias_matching(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[
                ExtractedPerson(name="Johnny", spans=["Johnny"])  # Using alias
            ])
            obsidian_entities = {
                'name_lookup': {
                    'Johnny': {  # Alias maps to canonical name
                        'entity_long_name': 'John Smith',
                        'entity_id': 'john-uuid'
                    }
                }
            }

            mock_person = Person(name="John Smith", summary="A person")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_person)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 1
            assert result[0]['canonical_name'] == 'John Smith'  # Should use canonical name
            extraction_service._hydrate_person.assert_called_once_with(sample_journal_entry, 'John Smith')

    class TestMergeEntityProperties:

        @pytest.mark.asyncio
        async def test_summary_merging(self, extraction_service):
            existing = Person(
                name="John",
                summary="Original summary",
                summary_short="Original short"
            )
            new = Person(
                name="John",
                summary="New summary",
                summary_short="New short"
            )

            mock_merged = {
                'summary': 'Merged long summary',
                'summary_short': 'Merged short'
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_merged)

            result = await extraction_service._merge_entity_properties(existing, new)

            assert result.summary == 'Merged long summary'
            assert result.summary_short == 'Merged short'
            assert result.name == new.name  # Other properties from new entity preserved

            # Verify LLM was called with correct parameters
            call_args = extraction_service.llm_service.generate.call_args
            user_prompt_data = call_args[1]['prompt']  # Assuming it's a keyword argument
            assert 'Original summary' in str(user_prompt_data)
            assert 'New summary' in str(user_prompt_data)

    class TestLLMInteractions:

        @pytest.mark.asyncio
        async def test_extract_people_success(self, extraction_service, sample_journal_entry):
            mock_response = {
                'people': [
                    {'name': 'John', 'spans': ['John']},
                    {'name': 'Sarah', 'spans': ['Sarah']}
                ]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service.extract_people(sample_journal_entry)

            assert isinstance(result, People)
            assert len(result.people) == 2
            assert result.people[0].name == 'John'
            assert result.people[1].name == 'Sarah'

            # Verify LLM service was called correctly
            extraction_service.llm_service.generate.assert_called_once()
            call_args = extraction_service.llm_service.generate.call_args[1]
            assert 'prompt' in call_args
            assert 'system_prompt' in call_args
            assert 'response_model' in call_args

        @pytest.mark.asyncio
        async def test_extract_people_returns_none(self, extraction_service, sample_journal_entry):
            extraction_service.llm_service.generate = AsyncMock(return_value=None)

            result = await extraction_service.extract_people(sample_journal_entry)

            assert result is None

        @pytest.mark.asyncio
        async def test_hydrate_person_success(self, extraction_service, sample_journal_entry):
            mock_response = {
                'name': 'John Smith',
                'summary': 'A detailed summary of John',
                'summary_short': 'Colleague'
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service._hydrate_person(sample_journal_entry, "John Smith")

            assert isinstance(result, Person)
            assert result.name == 'John Smith'
            assert result.summary == 'A detailed summary of John'
            assert result.summary_short == 'Colleague'

        @pytest.mark.asyncio
        async def test_hydrate_person_returns_none(self, extraction_service, sample_journal_entry):
            extraction_service.llm_service.generate = AsyncMock(return_value=None)

            result = await extraction_service._hydrate_person(sample_journal_entry, "John Smith")

            assert result is None

    class TestExtractRelationships:

        @pytest.mark.asyncio
        async def test_valid_relationship_extraction(self, extraction_service, sample_journal_entry):
            # Setup entities
            person1 = Person(uuid="uuid-1", name="John", summary="", summary_short="")
            person2 = Person(uuid="uuid-2", name="Sarah", summary="", summary_short="")
            entities = [
                EntityMapping(person1, [Span(start=0, end=4, text="John")]),
                EntityMapping(person2, [Span(start=5, end=10, text="Sarah")])
            ]

            # Mock LLM response
            mock_response = {
                "relationships": [{
                    "source": "uuid-1",
                    "target": "uuid-2",
                    "relationship_type": "WORKS_WITH",
                    "spans": ["works with"],
                    "context": None
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            # Mock span hydration
            mock_span = Span(start=20, end=30, text="works with")
            extraction_service.hydrate_spans_for_text = Mock(return_value=[mock_span])

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 1
            assert isinstance(result[0], RelationSpanContextMapping)
            assert result[0].relation.source == "uuid-1"
            assert result[0].relation.target == "uuid-2"
            assert result[0].relation.relationship_type == "WORKS_WITH"
            assert len(result[0].spans) == 1
            assert result[0].spans[0].text == "works with"

        @pytest.mark.asyncio
        async def test_relationship_with_context(self, extraction_service, sample_journal_entry):
            person1 = Person(uuid="uuid-1", name="John")
            person2 = Person(uuid="uuid-2", name="Sarah")
            person3 = Person(uuid="uuid-3", name="Mike")
            entities = [
                EntityMapping(person1, []),
                EntityMapping(person2, []),
                EntityMapping(person3, [])
            ]

            mock_context = [{"entity_uuid": "uuid-3", "context_type": "LOCATION"}]
            mock_response = {
                "relationships": [{
                    "source": "uuid-1",
                    "target": "uuid-2",
                    "relationship_type": "MET_WITH",
                    "spans": ["met with"],
                    "context": mock_context
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)
            extraction_service.hydrate_spans_for_text = Mock(return_value=[Span(start=0, end=8, text="met with")])

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 1
            assert result[0].context == mock_context

        @pytest.mark.asyncio
        async def test_invalid_source_uuid(self, extraction_service, sample_journal_entry):
            entities = [EntityMapping(Person(uuid="valid-uuid", name="John"), [])]

            mock_response = {
                "relationships": [{
                    "source": "invalid-uuid",  # This UUID doesn't exist
                    "target": "valid-uuid",
                    "relationship_type": "KNOWS",
                    "spans": ["knows"]
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 0  # Should filter out invalid relationships

        @pytest.mark.asyncio
        async def test_invalid_target_uuid(self, extraction_service, sample_journal_entry):
            entities = [EntityMapping(Person(uuid="valid-uuid", name="John"), [])]

            mock_response = {
                "relationships": [{
                    "source": "valid-uuid",
                    "target": "invalid-uuid",  # This UUID doesn't exist
                    "relationship_type": "KNOWS",
                    "spans": ["knows"]
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 0

        @pytest.mark.asyncio
        async def test_invalid_context_uuid(self, extraction_service, sample_journal_entry):
            entities = [
                EntityMapping(Person(uuid="uuid-1", name="John"), []),
                EntityMapping(Person(uuid="uuid-2", name="Sarah"), [])
            ]

            mock_context = [{"entity_uuid": "invalid-context-uuid", "context_type": "LOCATION"}]
            mock_response = {
                "relationships": [{
                    "source": "uuid-1",
                    "target": "uuid-2",
                    "relationship_type": "MET_WITH",
                    "spans": ["met with"],
                    "context": mock_context
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 0  # Should filter out due to invalid context UUID

        @pytest.mark.asyncio
        async def test_relationship_without_spans(self, extraction_service, sample_journal_entry):
            entities = [
                EntityMapping(Person(uuid="uuid-1", name="John"), []),
                EntityMapping(Person(uuid="uuid-2", name="Sarah"), [])
            ]

            mock_response = {
                "relationships": [{
                    "source": "uuid-1",
                    "target": "uuid-2",
                    "relationship_type": "KNOWS",
                    "spans": None  # No spans provided
                }]
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_response)

            result = await extraction_service.extract_relationships(sample_journal_entry, entities)

            assert len(result) == 1
            assert len(result[0].spans) == 0  # Should have empty spans list

    class TestExtractEntities:

        @pytest.mark.asyncio
        async def test_llm_returns_none_raises_exception(self, extraction_service, sample_journal_entry):
            extraction_service._build_obsidian_entity_lookup = AsyncMock(return_value={})
            extraction_service.extract_people = AsyncMock(return_value=None)

            with pytest.raises(Exception, match="LLM did not return any people data"):
                await extraction_service.extract_entities(sample_journal_entry)

        @pytest.mark.asyncio
        async def test_successful_entity_extraction(self, extraction_service, sample_journal_entry):
            # Mock dependencies
            mock_obsidian_entities = {'name_lookup': {}, 'db_entities': [], 'glossary': {}}
            extraction_service._build_obsidian_entity_lookup = AsyncMock(return_value=mock_obsidian_entities)

            mock_llm_people = People(people=[ExtractedPerson(name="John", spans=["John"])])
            extraction_service.extract_people = AsyncMock(return_value=mock_llm_people)

            mock_processed_people = [{'entity': Person(name="John"), 'spans': ["John"]}]
            extraction_service._process_and_deduplicate_people = AsyncMock(return_value=mock_processed_people)

            mock_spans = [EntityMapping(Person(name="John"), [Span(start=0, end=4, text="John")])]
            extraction_service._process_spans = Mock(return_value=mock_spans)

            result = await extraction_service.extract_entities(sample_journal_entry)

            assert len(result) == 1
            assert isinstance(result[0], EntityMapping)

            # Verify all methods were called in correct order
            extraction_service._build_obsidian_entity_lookup.assert_called_once_with(sample_journal_entry)
            extraction_service.extract_people.assert_called_once_with(sample_journal_entry)
            extraction_service._process_and_deduplicate_people.assert_called_once_with(
                mock_llm_people, mock_obsidian_entities, sample_journal_entry
            )
            extraction_service._process_spans.assert_called_once_with(mock_processed_people, sample_journal_entry)

        @pytest.mark.asyncio
        async def test_empty_processed_people_returns_empty(self, extraction_service, sample_journal_entry):
            extraction_service._build_obsidian_entity_lookup = AsyncMock(return_value={})
            extraction_service.extract_people = AsyncMock(return_value=People(people=[]))
            extraction_service._process_and_deduplicate_people = AsyncMock(return_value=[])
            extraction_service._process_spans = Mock(return_value=[])

            result = await extraction_service.extract_entities(sample_journal_entry)

            assert len(result) == 0

    class TestEdgeCases:

        def test_hydrate_spans_with_overlapping_matches(self, extraction_service):
            span_texts = ["John", "John Smith"]
            entry_text = "I met John Smith today."

            spans = extraction_service.hydrate_spans_for_text(span_texts, entry_text)

            # Should find both spans
            assert len(spans) == 2
            # First match for "John"
            assert spans[0].text == "John"
            assert spans[0].start == 6
            # Second match for "John Smith"
            assert spans[1].text == "John Smith"
            assert spans[1].start == 6

        def test_hydrate_spans_with_duplicate_span_texts(self, extraction_service):
            span_texts = ["John", "John", "Smith"]  # Duplicate "John"
            entry_text = "John called Smith and John answered."

            spans = extraction_service.hydrate_spans_for_text(span_texts, entry_text)

            # Should find all instances
            assert len(spans) == 3
            spans_text = [s.text for s in spans]
            assert spans_text.count("John") == 2
            assert spans_text.count("Smith") == 1

        def test_find_best_phrase_match_single_character(self, extraction_service):
            result = extraction_service._find_best_phrase_match("a", "a man walked")

            assert result is not None
            phrase, start, end, score = result
            assert phrase == "a"
            assert start == 0
            assert end == 1

        def test_find_best_phrase_match_exact_text_match(self, extraction_service):
            text = "Hello world"
            result = extraction_service._find_best_phrase_match(text, text)

            assert result is not None
            phrase, start, end, score = result
            assert phrase == text
            assert score == 100  # Perfect match

        @pytest.mark.asyncio
        async def test_build_obsidian_lookup_with_none_values(self, extraction_service, sample_journal_entry):
            sample_journal_entry.entry_text = "I met [[John]]."

            extraction_service.obsidian_service.resolve_link.side_effect = [
                {
                    'entity_name': None,  # None name
                    'entity_long_name': 'John Smith',
                    'entity_id': 'uuid-1',
                    'aliases': None,  # None aliases
                    'short_summary': None  # None summary
                },
                {
                    'entity_name': 'Alex Elgier',
                    'entity_long_name': 'Alex Elgier',
                    'entity_id': 'user-uuid',
                    'aliases': [],
                    'short_summary': 'The user'
                }
            ]

            result = await extraction_service._build_obsidian_entity_lookup(sample_journal_entry)

            # Should handle None values gracefully
            assert 'Alex Elgier' in result['name_lookup']
            # Entity with None name should not be in name_lookup
            assert len([k for k in result['name_lookup'].keys() if k is None]) == 0

        def test_process_spans_with_empty_entity_list(self, extraction_service, sample_journal_entry):
            result = extraction_service._process_spans([], sample_journal_entry)
            assert result == []

        @pytest.mark.asyncio
        async def test_merge_entity_properties_with_none_summaries(self, extraction_service):
            existing = Person(name="John", summary=None, summary_short=None)
            new = Person(name="John", summary="New summary", summary_short="New short")

            mock_merged = {
                'summary': 'Final summary',
                'summary_short': 'Final short'
            }
            extraction_service.llm_service.generate = AsyncMock(return_value=mock_merged)

            result = await extraction_service._merge_entity_properties(existing, new)

            assert result.summary == 'Final summary'
            assert result.summary_short == 'Final short'

        def test_hydrate_spans_case_sensitivity_edge_cases(self, extraction_service):
            # Test mixed case scenarios
            span_texts = ["JOHN smith", "Coffee SHOP"]
            entry_text = "I met john SMITH at the COFFEE shop."

            spans = extraction_service.hydrate_spans_for_text(span_texts, entry_text)

            assert len(spans) == 2
            assert spans[0].text == "john SMITH"
            assert spans[1].text == "COFFEE shop"

        def test_find_best_phrase_match_window_size_edge_cases(self, extraction_service):
            # Test with very long target span
            target = "a very long phrase that might not match well"
            text = "short text"

            result = extraction_service._find_best_phrase_match(target, text, min_score=75)

            assert result is None  # Should not match due to length mismatch

        @pytest.mark.asyncio
        async def test_extract_relationships_empty_entities_list(self, extraction_service, sample_journal_entry):
            extraction_service.llm_service.generate = AsyncMock(return_value={"relationships": []})

            result = await extraction_service.extract_relationships(sample_journal_entry, [])

            assert len(result) == 0
            # Should still call LLM even with empty entities
            extraction_service.llm_service.generate.assert_called_once()

        @pytest.mark.asyncio
        async def test_process_and_deduplicate_people_empty_llm_people(self, extraction_service, sample_journal_entry):
            empty_people = People(people=[])
            obsidian_entities = {'name_lookup': {}}

            result = await extraction_service._process_and_deduplicate_people(
                empty_people, obsidian_entities, sample_journal_entry
            )

            assert len(result) == 0

    class TestRepositoryInteractions:

        @pytest.mark.asyncio
        async def test_entity_repository_find_by_uuid_called_correctly(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[ExtractedPerson(name="John", spans=["John"])])
            obsidian_entities = {
                'name_lookup': {
                    'John': {
                        'entity_long_name': 'John Smith',
                        'entity_id': 'test-uuid'
                    }
                }
            }

            existing_person = Person(uuid='test-uuid', name="John Smith", summary="Old summary")
            mock_hydrated = Person(name="John Smith", summary="New summary")

            extraction_service._hydrate_person = AsyncMock(return_value=mock_hydrated)
            extraction_service.entity_repositories['Person'].find_by_uuid = Mock(return_value=existing_person)
            extraction_service._merge_entity_properties = AsyncMock(return_value=mock_hydrated)

            await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            # Verify repository was called with correct UUID
            extraction_service.entity_repositories['Person'].find_by_uuid.assert_called_once_with('test-uuid')

        @pytest.mark.asyncio
        async def test_entity_repository_find_returns_none(self, extraction_service, sample_journal_entry):
            llm_people = People(people=[ExtractedPerson(name="John", spans=["John"])])
            obsidian_entities = {
                'name_lookup': {
                    'John': {
                        'entity_long_name': 'John Smith',
                        'entity_id': 'nonexistent-uuid'
                    }
                }
            }

            mock_hydrated = Person(name="John Smith", summary="New summary")
            extraction_service._hydrate_person = AsyncMock(return_value=mock_hydrated)
            extraction_service.entity_repositories['Person'].find_by_uuid = Mock(return_value=None)

            result = await extraction_service._process_and_deduplicate_people(
                llm_people, obsidian_entities, sample_journal_entry
            )

            # Should still process the person even if not found in DB
            assert len(result) == 1
            assert result[0]['entity'].uuid == 'nonexistent-uuid'
            # Should not attempt to merge since no existing entity
            assert not hasattr(extraction_service, '_merge_entity_properties') or \
                   not getattr(extraction_service._merge_entity_properties, 'called', False)
