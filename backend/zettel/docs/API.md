# API Reference

Complete API reference for the zettel_agent module. This document covers all public functions, classes, and modules.

## Table of Contents

- [Database Module (`db.py`)](#database-module-dbpy)
- [Concept Extraction Graph (`concept_extraction_graph.py`)](#concept-extraction-graph-concept_extraction_graphpy)
- [Quote Parse Graph (`quote_parse_graph.py`)](#quote-parse-graph-quote_parse_graphpy)
- [Obsidian Utilities (`obsidian_utils.py`)](#obsidian-utilities-obsidian_utilspy)

---

## Database Module (`db.py`)

The database module provides Neo4j connection management and query functions for all database operations.

### Classes

#### `Neo4jConnectionManager`

Simple Neo4j connection manager following Neo4j driver best practices. One driver instance for app lifetime, with session context management.

```python
class Neo4jConnectionManager:
    def __init__(self, uri: str, user: str, password: str)
    async def initialize(self) -> None
    async def session(self, database: str | None = None) -> AsyncContextManager[AsyncSession]
    async def close(self) -> None
```

**Methods:**

- **`__init__(uri, user, password)`**
  - Initialize connection parameters. Driver created on first use.
  - **Parameters:**
    - `uri` (str): Neo4j connection URI (e.g., "bolt://localhost:7687")
    - `user` (str): Neo4j username
    - `password` (str): Neo4j password
  - **Example:**
    ```python
    manager = Neo4jConnectionManager(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    ```

- **`initialize()`**
  - Create the async driver (lazy initialization pattern).
  - **Returns:** None
  - **Example:**
    ```python
    await manager.initialize()
    ```

- **`session(database=None)`**
  - Async context manager for sessions (recommended pattern).
  - **Parameters:**
    - `database` (str | None): Database name (defaults to "neo4j")
  - **Returns:** AsyncContextManager[AsyncSession]
  - **Example:**
    ```python
    async with manager.session() as session:
        result = await session.run("MATCH (n) RETURN count(n)")
    ```

- **`close()`**
  - Close the driver and cleanup (call at app shutdown).
  - **Returns:** None
  - **Example:**
    ```python
    await manager.close()
    ```

### Functions

#### `serialize_model(model: BaseModel) -> Dict[str, Any]`

Convert Pydantic model to Neo4j-compatible dict. Converts datetime objects to ISO strings for Neo4j storage.

**Parameters:**
- `model` (BaseModel): Pydantic model to serialize

**Returns:**
- `Dict[str, Any]`: Dictionary with datetime objects converted to ISO strings

**Example:**
```python
from minerva_models import Content

content = Content(title="Test", author="Author")
properties = serialize_model(content)
# properties is now a dict with ISO-formatted datetime strings
```

#### `deserialize_to_model(data: Dict[str, Any], model_class: Type[T]) -> T`

Convert Neo4j result dict to Pydantic model. Handles Neo4j time objects and ISO datetime strings.

**Parameters:**
- `data` (Dict[str, Any]): Dictionary from Neo4j result
- `model_class` (Type[T]): Pydantic model class to deserialize to

**Returns:**
- `T`: Instance of the model class

**Example:**
```python
from minerva_models import Content

record = {"uuid": "123", "title": "Test", "created_at": "2024-01-01T00:00:00"}
content = deserialize_to_model(record, Content)
```

#### `search_person_by_name(session: AsyncSession, partial_name: str) -> List[Person]`

Search persons by partial name match (case-insensitive).

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `partial_name` (str): Partial name to search for

**Returns:**
- `List[Person]`: List of matching Person objects, ordered by name

**Example:**
```python
async with connection_manager.session() as session:
    persons = await search_person_by_name(session, "Lenin")
    # Returns all persons with "Lenin" in their name
```

#### `create_person(session: AsyncSession, person: Person) -> str`

Create Person node in Neo4j, return UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `person` (Person): Person object to create

**Returns:**
- `str`: UUID of the created Person node

**Raises:**
- `Exception`: If creation fails

**Example:**
```python
person = Person(name="Vladimir Lenin", occupation="Author")
async with connection_manager.session() as session:
    uuid = await create_person(session, person)
```

#### `create_content(session: AsyncSession, content: Content) -> str`

Create Content node in Neo4j, return UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content` (Content): Content object to create

**Returns:**
- `str`: UUID of the created Content node

**Raises:**
- `Exception`: If creation fails

**Example:**
```python
content = Content(title="Book Title", author="Author")
async with connection_manager.session() as session:
    uuid = await create_content(session, content)
```

#### `create_authored_by_relationship(session: AsyncSession, author_uuid: str, content_uuid: str) -> None`

Create AUTHORED_BY relationship between Person and Content.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `author_uuid` (str): UUID of the Person (author)
- `content_uuid` (str): UUID of the Content

**Returns:**
- None

**Example:**
```python
async with connection_manager.session() as session:
    await create_authored_by_relationship(session, author_uuid, content_uuid)
```

#### `create_quotes_for_content(session: AsyncSession, quotes: List[Quote], content_uuid: str) -> List[str]`

Create Quote nodes and QUOTED_IN relationships, return list of UUIDs.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `quotes` (List[Quote]): List of Quote objects to create
- `content_uuid` (str): UUID of the Content

**Returns:**
- `List[str]`: List of created quote UUIDs, ordered by created_at DESC

**Example:**
```python
quotes = [Quote(text="Quote 1"), Quote(text="Quote 2")]
async with connection_manager.session() as session:
    uuids = await create_quotes_for_content(session, quotes, content_uuid)
```

#### `find_content_by_uuid(session: AsyncSession, content_uuid: str) -> Content | None`

Find Content node by UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content_uuid` (str): UUID of the Content

**Returns:**
- `Content | None`: Content object if found, None otherwise

**Example:**
```python
async with connection_manager.session() as session:
    content = await find_content_by_uuid(session, content_uuid)
    if content:
        print(content.title)
```

#### `find_quotes_by_content(session: AsyncSession, content_uuid: str) -> List[Quote]`

Find all quotes linked to a specific content.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content_uuid` (str): UUID of the Content

**Returns:**
- `List[Quote]`: List of Quote objects, ordered by created_at DESC (embeddings excluded)

**Example:**
```python
async with connection_manager.session() as session:
    quotes = await find_quotes_by_content(session, content_uuid)
    for quote in quotes:
        print(quote.text)
```

#### `find_quote_by_uuid(session: AsyncSession, quote_uuid: str) -> Quote | None`

Find Quote node by UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `quote_uuid` (str): UUID of the Quote

**Returns:**
- `Quote | None`: Quote object if found, None otherwise (embedding excluded)

**Example:**
```python
async with connection_manager.session() as session:
    quote = await find_quote_by_uuid(session, quote_uuid)
```

#### `get_unprocessed_quotes(session: AsyncSession, content_uuid: str, processed_uuids: List[str], limit: int | None = None) -> List[Quote]`

Get quotes for content that haven't been processed yet.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content_uuid` (str): UUID of the content
- `processed_uuids` (List[str]): List of quote UUIDs that have already been processed
- `limit` (int | None): Optional limit on number of quotes to return

**Returns:**
- `List[Quote]`: List of unprocessed Quote objects

**Example:**
```python
processed = ["uuid1", "uuid2"]
async with connection_manager.session() as session:
    unprocessed = await get_unprocessed_quotes(
        session, content_uuid, processed, limit=50
    )
```

#### `find_concept_by_uuid(session: AsyncSession, concept_uuid: str) -> Concept | None`

Find Concept node by UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `concept_uuid` (str): UUID of the Concept

**Returns:**
- `Concept | None`: Concept object if found, None otherwise

**Example:**
```python
async with connection_manager.session() as session:
    concept = await find_concept_by_uuid(session, concept_uuid)
```

#### `vector_search_concepts(session: AsyncSession, query_embedding: List[float], limit: int = 10, threshold: float = 0.7) -> List[Concept]`

Vector search for Concepts using embedding similarity.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `query_embedding` (List[float]): Query embedding vector (1024 dimensions)
- `limit` (int): Maximum number of results (default: 10)
- `threshold` (float): Minimum similarity threshold 0.0-1.0 (default: 0.7)

**Returns:**
- `List[Concept]`: List of Concept objects ordered by similarity (descending)

**Example:**
```python
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
query_embedding = await embeddings.aembed_query("concept text")

async with connection_manager.session() as session:
    concepts = await vector_search_concepts(
        session, query_embedding, limit=50, threshold=0.7
    )
```

#### `create_concept(session: AsyncSession, concept: Concept) -> str`

Create Concept node in Neo4j, return UUID.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `concept` (Concept): Concept object to create

**Returns:**
- `str`: UUID of the created Concept node

**Raises:**
- `Exception`: If creation fails

**Example:**
```python
concept = Concept(
    title="Concept Title",
    concept="Concept description",
    analysis="Personal analysis"
)
async with connection_manager.session() as session:
    uuid = await create_concept(session, concept)
```

#### `create_concept_relation(session: AsyncSession, source_uuid: str, target_uuid: str, relation_type: str) -> None`

Create bidirectional concept relation using RELATION_MAP. Automatically creates both forward and reverse relations.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `source_uuid` (str): UUID of source concept
- `target_uuid` (str): UUID of target concept
- `relation_type` (str): Forward relation type (e.g., "GENERALIZES", "PART_OF", "OPPOSES")

**Returns:**
- None

**Raises:**
- `ValueError`: If relation_type is invalid

**Example:**
```python
async with connection_manager.session() as session:
    # Creates GENERALIZES and SPECIFIC_OF relations
    await create_concept_relation(
        session, source_uuid, target_uuid, "GENERALIZES"
    )
```

**Note:** This function automatically creates bidirectional relations:
- Asymmetric relations: Creates both forward and reverse (e.g., GENERALIZES → SPECIFIC_OF)
- Symmetric relations: Creates same type in both directions (e.g., OPPOSES → OPPOSES)

#### `create_supports_relation(session: AsyncSession, quote_uuid: str, concept_uuid: str, reasoning: str | None = None, confidence: float | None = None) -> None`

Create (Quote)-[:SUPPORTS]->(Concept) relationship.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `quote_uuid` (str): UUID of the quote
- `concept_uuid` (str): UUID of the concept
- `reasoning` (str | None): Optional reasoning for the support
- `confidence` (float | None): Optional confidence score (0.0-1.0)

**Returns:**
- None

**Example:**
```python
async with connection_manager.session() as session:
    await create_supports_relation(
        session,
        quote_uuid,
        concept_uuid,
        reasoning="Quote supports this concept because...",
        confidence=0.95
    )
```

#### `update_content_processed_date(session: AsyncSession, content_uuid: str, processed_date: datetime | None = None) -> None`

Set processed_date on Content node.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content_uuid` (str): UUID of the content
- `processed_date` (datetime | None): Timestamp to set (defaults to current time)

**Returns:**
- None

**Example:**
```python
from datetime import datetime

async with connection_manager.session() as session:
    await update_content_processed_date(
        session, content_uuid, datetime.now()
    )
```

#### `get_unprocessed_quotes_by_supports(session: AsyncSession, content_uuid: str) -> List[Quote]`

Get quotes for content that don't have any SUPPORTS relations to concepts.

**Parameters:**
- `session` (AsyncSession): Neo4j session
- `content_uuid` (str): UUID of the content

**Returns:**
- `List[Quote]`: List of unprocessed Quote objects (quotes without SUPPORTS relations)

**Example:**
```python
async with connection_manager.session() as session:
    unprocessed = await get_unprocessed_quotes_by_supports(
        session, content_uuid
    )
```

#### `get_neo4j_connection_manager() -> Neo4jConnectionManager`

Factory function to create configured connection manager.

**Returns:**
- `Neo4jConnectionManager`: Configured connection manager instance

**Example:**
```python
connection_manager = get_neo4j_connection_manager()
async with connection_manager.session() as session:
    # Use session
    pass
```

**Note:** Connection parameters are currently hardcoded in this function. Modify the function to change connection settings.

---

## Concept Extraction Graph (`concept_extraction_graph.py`)

The concept extraction graph implements a 3-phase workflow for extracting atomic concepts from quotes.

### State Schema

#### `ConceptExtractionState`

TypedDict defining the state for concept extraction workflow.

```python
class ConceptExtractionState(TypedDict):
    # Input
    content_uuid: str
    content: Optional[Content]
    quotes: List[Quote]
    user_suggestions: Optional[str]  # Freeform text suggestions for the extraction process
    
    # Processing state
    phase: Literal["extraction", "human_review", "commit", "end"]
    iteration_count: int
    phase_1_iteration: int
    phase_2_iteration: int
    
    # Extraction results (using Annotated with operator.add for accumulation)
    candidate_concepts: Annotated[List[Dict], operator.add]
    duplicate_detections: Annotated[List[Dict], operator.add]
    novel_concepts: Annotated[List[Dict], operator.add]
    existing_concepts_with_quotes: Annotated[List[Dict], operator.add]
    relations: Annotated[List[Dict], operator.add]
    
    # Quality assessment
    quality_assessment: Optional[Dict]
    critique_log: Annotated[List[Dict], operator.add]
    
    # Human review
    human_feedback: Optional[str]
    human_approved: bool
    
    # Errors and warnings
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
```

### Pydantic Models

#### `CandidateConcept`

A candidate concept extracted from quotes.

```python
class CandidateConcept(BaseModel):
    concept_id: str  # Temporary ID for tracking
    title: str  # Título del concepto en español
    concept: str  # Contenido del concepto
    analysis: str  # Análisis personal
    source_quote_ids: List[str]  # Quotes that formed this concept
    rationale: str  # Why this concept was extracted
```

#### `DuplicateDetection`

Result of duplicate detection for a candidate concept.

```python
class DuplicateDetection(BaseModel):
    candidate_concept_id: str
    is_duplicate: bool
    existing_concept_uuid: Optional[str]
    existing_concept_name: Optional[str]
    confidence: float  # 0.0-1.0
    reasoning: str
    quote_ids_to_transfer: List[str]
```

#### `ConceptRelation`

A relation between concepts.

```python
class ConceptRelation(BaseModel):
    target_concept_id: str  # Temp ID or UUID
    target_is_novel: bool
    relation_type: str  # Forward relation type
    explanation: str
    confidence: float  # 0.0-1.0
```

#### `QualityAssessment`

Quality assessment from self-critique.

```python
class QualityAssessment(BaseModel):
    atomicity: QualityCriterion
    distinctness: QualityCriterion
    quote_coverage: QualityCriterion
    relation_accuracy: QualityCriterion
    language: QualityCriterion
    edge_cases: QualityCriterion
```

### Graph Nodes

#### Phase 1: LLM Self-Improvement Loop

**`check_content_processed(state: ConceptExtractionState) -> Dict[str, Any]`**

Check if content is already processed and exit early if so.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with content or error/warning

**Example:**
```python
# Called automatically by graph
```

**`load_content_quotes(state: ConceptExtractionState) -> Dict[str, Any]`**

Load quotes for the content.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with quotes list

**`extract_candidate_concepts(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 1.1a: Extract candidate concepts with source quotes.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with candidate_concepts list

**`detect_duplicates_all(state: ConceptExtractionState) -> Dict[str, Any]`**

Detect duplicates for all candidate concepts.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with novel_concepts and existing_concepts_with_quotes

**`generate_relation_queries(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 1.1c: Generate relation search queries for novel concepts.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with relation_queries

**`search_relation_candidates(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 1.1d: Semantic search for relation candidates (vector search, not LLM).

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with relation_candidates

**`create_relations_all(state: ConceptExtractionState) -> Dict[str, Any]`**

Create relations for all novel concepts.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with relations list

**`self_critique(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 1.2: Self-critique against quality checklist.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with quality_assessment and critique_log

**`refine_extraction(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 1.3: Refine extraction based on self-critique.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with refined novel_concepts, relations, etc.

#### Phase 2: Human Review Loop

**`present_for_review(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 2.1: Present comprehensive report and interrupt for human review.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: Empty dict (execution paused at interrupt)

**Note:** This function uses `interrupt()` to pause execution. Human must provide feedback via LangGraph API to resume.

**`incorporate_feedback(state: ConceptExtractionState) -> Dict[str, Any]`**

Call 2.3: Incorporate human feedback.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state (must include human_feedback)

**Returns:**
- `Dict[str, Any]`: State update with revised extraction

#### Phase 3: Commit to Database

**`create_concepts_db(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 3.1: Create Concept nodes in database.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with created_concept_uuids (mapping temp_id to UUID)

**`create_relations_db(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 3.2: Create bidirectional concept relations.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: Empty dict

**`create_supports_relations(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 3.3: Create SUPPORTS relations from quotes to concepts.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: Empty dict

**`create_obsidian_files(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 3.4: Create Obsidian zettel files.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with created_files list

**`update_processed_date(state: ConceptExtractionState) -> Dict[str, Any]`**

Step 3.5: Update Content processed_date.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with phase="end"

### Routing Functions

**`should_continue_phase1(state: ConceptExtractionState) -> Literal["refine", "human_review", "end"]`**

Decide whether to continue Phase 1 loop or move to Phase 2.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `"refine"`: Continue refinement loop
- `"human_review"`: Move to Phase 2
- `"end"`: End workflow (errors or max iterations)

**`should_continue_phase2(state: ConceptExtractionState) -> Literal["incorporate", "commit", "end"]`**

Decide whether to continue Phase 2 loop or move to Phase 3.

**Parameters:**
- `state` (ConceptExtractionState): Current workflow state

**Returns:**
- `"incorporate"`: Continue feedback incorporation loop
- `"commit"`: Move to Phase 3 (human approved)
- `"end"`: End workflow (errors or max iterations)

### Graph Export

**`graph`**

Compiled LangGraph StateGraph instance. Use this to invoke the workflow.

**Example:**
```python
from zettel_agent.concept_extraction_graph import graph

result = await graph.ainvoke({
    "content_uuid": "uuid-here"
})
```

---

## Quote Parse Graph (`quote_parse_graph.py`)

The quote parse graph processes markdown book notes and extracts quotes.

### State Schema

#### `State`

Dataclass defining the state for quote parsing workflow.

```python
@dataclass
class State:
    file_path: str
    author: str
    title: str
    file_content: str = None
    book: Content = None
    parsed_author: Person = None
    quotes: List[Quote] = None
    sections: List[str] = None
    summary: str = None
    summary_short: str = None
```

### Graph Nodes

**`read_file(state: State) -> Dict[str, Any]`**

Read the file content into state.

**Parameters:**
- `state` (State): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with file_content

**`make_summary(state: State) -> Dict[str, Any]`**

Generate summary and short summary for the book using LLM.

**Parameters:**
- `state` (State): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with summary and summary_short

**`parse_quotes(state: State) -> Dict[str, Any]`**

Parse quotes from the file and create book entity.

**Parameters:**
- `state` (State): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with book, quotes, and sections

**`get_or_create_author(state: State) -> Dict[str, Any]`**

Get existing author or create new one with web search enrichment. If author exists, returns it immediately. If author doesn't exist, enriches with web search first, then creates with enriched data.

**Parameters:**
- `state` (State): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with parsed_author

**Note:** Web search enrichment only happens for newly created authors. Existing authors are assumed to be well-formed and are returned without modification.

**`write_to_db(state: State) -> Dict[str, Any]`**

Write book, author relationship, and quotes to database.

**Parameters:**
- `state` (State): Current workflow state

**Returns:**
- `Dict[str, Any]`: State update with book and content_uuid

### Helper Functions

**`_parse_quotes_from_content(content: str) -> List[Quote]`**

Parse quotes from markdown content. Internal helper function.

**Parameters:**
- `content` (str): Markdown file content

**Returns:**
- `List[Quote]`: List of parsed Quote objects

**Note:** This function expects markdown with `# Citas` section and `## Section Name` headers.

### Graph Export

**`graph`**

Compiled LangGraph StateGraph instance. Use this to invoke the workflow.

**Example:**
```python
from zettel_agent.quote_parse_graph import graph

result = await graph.ainvoke({
    "file_path": "/path/to/book.md",
    "author": "Author Name",
    "title": "Book Title"
})
```

---

## Obsidian Utilities (`obsidian_utils.py`)

Utilities for creating Obsidian zettel files from concepts.

### Functions

#### `get_zettel_directory(vault_path: str = "D:\\yo") -> str`

Get the path to the Zettels directory.

**Parameters:**
- `vault_path` (str): Path to Obsidian vault (default: "D:\\yo")

**Returns:**
- `str`: Path to "08 - Ideas" directory

**Example:**
```python
zettel_dir = get_zettel_directory("D:\\my_vault")
# Returns: "D:\\my_vault\\08 - Ideas"
```

#### `format_zettel_frontmatter(concept_uuid: str, summary_short: str, summary: str, concept_relations: Dict[str, List[str]]) -> str`

Generate YAML frontmatter for Obsidian zettel file.

**Parameters:**
- `concept_uuid` (str): UUID of the concept
- `summary_short` (str): Short summary (30 words max)
- `summary` (str): Detailed summary (100 words max)
- `concept_relations` (Dict[str, List[str]]): Dict mapping relation types to lists of target concept UUIDs

**Returns:**
- `str`: YAML frontmatter string

**Example:**
```python
frontmatter = format_zettel_frontmatter(
    concept_uuid="uuid-123",
    summary_short="Short summary",
    summary="Detailed summary",
    concept_relations={
        "GENERALIZES": ["uuid-1", "uuid-2"],
        "PART_OF": ["uuid-3"]
    }
)
```

#### `format_zettel_content(title: str, concept: str, analysis: str, concept_relations: Dict[str, List[str]], concept_names: Dict[str, str], source: str | None = None) -> str`

Generate markdown content for Obsidian zettel file.

**Parameters:**
- `title` (str): Concept title
- `concept` (str): Core concept description
- `analysis` (str): Personal analysis
- `concept_relations` (Dict[str, List[str]]): Dict mapping relation types to lists of target concept UUIDs
- `concept_names` (Dict[str, str]): Dict mapping concept UUIDs to concept names
- `source` (str | None): Optional source reference

**Returns:**
- `str`: Markdown content string

**Example:**
```python
content = format_zettel_content(
    title="Concept Title",
    concept="Concept description",
    analysis="Personal analysis",
    concept_relations={"GENERALIZES": ["uuid-1"]},
    concept_names={"uuid-1": "Related Concept"},
    source="Book Title"
)
```

#### `resolve_concept_names(concept_uuids: List[str]) -> Dict[str, str]`

Resolve concept UUIDs to concept names.

**Parameters:**
- `concept_uuids` (List[str]): List of concept UUIDs

**Returns:**
- `Dict[str, str]`: Dict mapping UUIDs to concept names

**Example:**
```python
concept_names = await resolve_concept_names(["uuid-1", "uuid-2"])
# Returns: {"uuid-1": "Concept Name 1", "uuid-2": "Concept Name 2"}
```

#### `create_zettel_file(concept_uuid: str, title: str, concept: str, analysis: str, summary_short: str, summary: str, concept_relations: Dict[str, List[str]], source: str | None = None, vault_path: str = "D:\\yo") -> str`

Create an Obsidian zettel file for a concept.

**Parameters:**
- `concept_uuid` (str): UUID of the concept
- `title` (str): Concept title
- `concept` (str): Core concept description
- `analysis` (str): Personal analysis
- `summary_short` (str): Short summary
- `summary` (str): Detailed summary
- `concept_relations` (Dict[str, List[str]]): Dict mapping relation types to lists of target concept UUIDs
- `source` (str | None): Optional source reference
- `vault_path` (str): Path to Obsidian vault

**Returns:**
- `str`: Path to the created file

**Example:**
```python
file_path = await create_zettel_file(
    concept_uuid="uuid-123",
    title="Concept Title",
    concept="Concept description",
    analysis="Personal analysis",
    summary_short="Short summary",
    summary="Detailed summary",
    concept_relations={"GENERALIZES": ["uuid-1"]},
    source="Book Title",
    vault_path="D:\\my_vault"
)
```

---

## Module Exports (`__init__.py`)

The module exports the two main graphs:

```python
from zettel_agent import quote_parse_graph, concept_extraction_graph
```

**Exports:**
- `quote_parse_graph`: Quote parsing workflow graph
- `concept_extraction_graph`: Concept extraction workflow graph

**Example:**
```python
from zettel_agent import quote_parse_graph, concept_extraction_graph

# Parse quotes
quote_result = await quote_parse_graph.ainvoke({
    "file_path": "/path/to/book.md",
    "author": "Author",
    "title": "Title"
})

# Extract concepts
concept_result = await concept_extraction_graph.ainvoke({
    "content_uuid": quote_result["content_uuid"]
})
```

---

## See Also

- [Architecture Documentation](ARCHITECTURE.md) - Technical architecture details
- [Developer Guide](DEVELOPER.md) - Guide for extending the module
- [Workflows Documentation](WORKFLOWS.md) - Detailed workflow documentation

