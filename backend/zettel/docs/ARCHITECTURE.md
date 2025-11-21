# Architecture Documentation

Deep technical architecture documentation for the zettel_agent module.

## Table of Contents

- [System Architecture](#system-architecture)
- [State Management](#state-management)
- [Graph Structure](#graph-structure)
- [Vector Search Implementation](#vector-search-implementation)
- [LLM Integration](#llm-integration)
- [Database Schema](#database-schema)
- [Error Handling](#error-handling)
- [Performance Considerations](#performance-considerations)

---

## System Architecture

### High-Level Overview

The zettel_agent module is built on LangGraph, providing a stateful workflow orchestration system for processing book quotes and extracting atomic concepts.

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph Server                          │
│  - State Management                                    │
│  - Checkpointing                                       │
│  - Human-in-the-Loop Support                          │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐      ┌──────────────────┐
│ quote_parse  │      │ concept_extract  │
│    graph     │      │      graph       │
│              │      │                  │
│ - read_file  │      │ - Phase 1:       │
│ - make_      │      │   Extraction     │
│   summary    │      │ - Phase 2:       │
│ - parse_     │      │   Human Review   │
│   quotes     │      │ - Phase 3:       │
│ - ensure_    │      │   Commit         │
│   author     │      │                  │
│ - write_to_  │      │                  │
│   db         │      │                  │
└──────┬───────┘      └────────┬─────────┘
       │                       │
       ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│              Neo4j Database                            │
│  - Content Nodes                                        │
│  - Quote Nodes (with embeddings)                      │
│  - Concept Nodes (with embeddings)                     │
│  - Vector Indexes                                       │
│  - Relationships                                        │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
   Ollama (Embeddings)    Google Gemini (LLM)
   mxbai-embed-large      gemini-2.5-pro/flash
```

### Component Responsibilities

**LangGraph Server:**
- Orchestrates workflow execution
- Manages state transitions
- Handles checkpointing for HITL
- Provides API endpoints

**Quote Parse Graph:**
- Processes markdown files
- Extracts quotes with metadata
- Creates database entities
- Generates embeddings

**Concept Extraction Graph:**
- Extracts atomic concepts
- Performs duplicate detection
- Discovers relations
- Validates quality
- Supports human review
- Commits to database

**Neo4j Database:**
- Stores all entities (Content, Quote, Concept, Person)
- Maintains relationships
- Provides vector search via indexes
- Ensures data consistency

**Ollama:**
- Generates embeddings for quotes and concepts
- Uses mxbai-embed-large model (1024 dimensions)
- Provides local, fast embedding generation

**Google Gemini:**
- Extracts concepts from quotes
- Performs duplicate detection
- Generates relations
- Self-critiques extraction quality
- Incorporates human feedback

---

## State Management

### State Schema Design

The module uses `TypedDict` for type-safe state management with LangGraph's reducer pattern for accumulating lists.

#### Quote Parse Graph State

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

**Characteristics:**
- Simple dataclass-based state
- Linear workflow (no loops)
- State accumulates as workflow progresses

#### Concept Extraction Graph State

```python
class ConceptExtractionState(TypedDict):
    # Input
    content_uuid: str
    content: Optional[Content]
    quotes: List[Quote]
    
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

**Key Design Decisions:**

1. **Annotated Types with Reducers:**
   - Lists that accumulate use `Annotated[List[Dict], operator.add]`
   - Prevents overwriting previous values
   - Allows parallel nodes to contribute independently

2. **Phase Tracking:**
   - `phase` field tracks current workflow phase
   - Separate iteration counters for each phase
   - Enables conditional routing

3. **Error Accumulation:**
   - Errors and warnings accumulate across nodes
   - Allows graceful degradation
   - Enables comprehensive error reporting

### State Updates

**Pattern:**
- Nodes return partial state updates (only changed fields)
- LangGraph merges updates automatically
- Reducers handle list accumulation

**Example:**
```python
async def extract_candidate_concepts(state: ConceptExtractionState) -> Dict[str, Any]:
    # ... processing ...
    return {
        "candidate_concepts": candidate_concepts_dicts,
        "warnings": response.unattributed_quotes if response.unattributed_quotes else []
    }
```

### Checkpointing

**Automatic Checkpointing:**
- LangGraph API handles checkpointing automatically
- State saved at every superstep
- Enables workflow resumption after interruption

**Human-in-the-Loop:**
- `interrupt()` pauses execution
- State checkpointed before interrupt
- Human provides feedback via API
- Workflow resumes from checkpoint

---

## Graph Structure

### Quote Parse Graph

**Linear Workflow:**
```
__start__ → read_file → make_summary → parse_quotes → get_or_create_author → write_to_db → __end__
```

**Node Details:**
1. **read_file**: Reads markdown file from filesystem
2. **make_summary**: LLM generates book summaries
3. **parse_quotes**: Extracts quotes from "# Citas" section
4. **get_or_create_author**: Gets existing author or creates new one with web search enrichment
5. **write_to_db**: Stores all entities and relationships

**No Loops:**
- Simple linear execution
- No conditional routing
- Error handling via exceptions

### Concept Extraction Graph

**Three-Phase Workflow:**

```
Phase 1: LLM Self-Improvement Loop
┌─────────────────────────────────────────────────────────┐
│ check_content_processed → load_content_quotes          │
│   → extract_candidate_concepts                         │
│   → detect_duplicates_all                              │
│   → generate_relation_queries                          │
│   → search_relation_candidates                         │
│   → create_relations_all                               │
│   → self_critique                                      │
│   → [refine_extraction → self_critique] (loop)         │
│   → present_for_review                                 │
└─────────────────────────────────────────────────────────┘

Phase 2: Human Review Loop
┌─────────────────────────────────────────────────────────┐
│ present_for_review (interrupt)                         │
│   → [incorporate_feedback → present_for_review] (loop) │
│   → create_concepts_db                                 │
└─────────────────────────────────────────────────────────┘

Phase 3: Commit to Database
┌─────────────────────────────────────────────────────────┐
│ create_concepts_db → create_relations_db               │
│   → create_supports_relations                          │
│   → create_obsidian_files                              │
│   → update_processed_date → __end__                    │
└─────────────────────────────────────────────────────────┘
```

**Conditional Routing:**

**Phase 1 Loop Control:**
```python
def should_continue_phase1(state) -> Literal["refine", "human_review", "end"]:
    if errors:
        return "end"
    if phase_1_iteration >= 10:
        return "human_review"
    if quality_assessment.overall_passes:
        return "human_review"
    return "refine"
```

**Phase 2 Loop Control:**
```python
def should_continue_phase2(state) -> Literal["incorporate", "commit", "end"]:
    if errors:
        return "end"
    if phase_2_iteration >= 20:
        return "end"
    if human_approved:
        return "commit"
    return "incorporate"
```

**Parallel Execution (Future):**
- Duplicate detection can be parallelized
- Relation creation can be parallelized
- Currently sequential for simplicity

---

## Vector Search Implementation

### Embedding Model

**Model:** mxbai-embed-large (via Ollama)
- **Dimensions:** 1024
- **Similarity:** Cosine similarity
- **Language:** Optimized for multilingual (including Spanish)

### Vector Indexes

**Quote Embeddings Index:**
```cypher
CREATE VECTOR INDEX quote_embeddings_index IF NOT EXISTS
FOR (n:Quote) ON (n.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};
```

**Concept Embeddings Index:**
```cypher
CREATE VECTOR INDEX concept_embeddings_index IF NOT EXISTS
FOR (n:Concept) ON (n.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};
```

### Search Process

**1. Generate Embedding:**
```python
embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
query_embedding = await embeddings.aembed_query(query_text)
```

**2. Vector Search:**
```python
concepts = await vector_search_concepts(
    session,
    query_embedding,
    limit=50,
    threshold=0.7
)
```

**3. Cypher Query:**
```cypher
CALL db.index.vector.queryNodes('concept_embeddings_index', $limit, $query_embedding)
YIELD node, score
WHERE score >= $threshold
RETURN node, score
ORDER BY score DESC
```

### Use Cases

**Duplicate Detection:**
- Generate embedding for candidate concept
- Search for similar existing concepts
- LLM validates if duplicate

**Relation Discovery:**
- Generate search queries for relation types
- Search for concepts matching queries
- LLM determines actual relations

---

## LLM Integration

### Models Used

**Google Gemini 2.5 Pro:**
- Complex reasoning tasks
- Concept extraction
- Duplicate detection
- Relation creation
- Self-critique
- Feedback incorporation

**Google Gemini 2.5 Flash:**
- Simpler tasks
- Relation query generation
- Summary generation

**Temperature:** 0 (deterministic outputs)

### Structured Outputs

**Pydantic Models:**
- All LLM calls use structured outputs
- Ensures consistent response format
- Type-safe parsing

**Example:**
```python
llm_structured = llm.with_structured_output(
    CandidateConceptsResponse,
    method="json_schema"
)
response = await llm_structured.ainvoke([...])
```

### Prompt Engineering

**System Prompts:**
- Define role (Zettelkasten expert)
- Specify language (Spanish)
- Provide guidelines (atomicity, distinctness)

**User Prompts:**
- Include context (quotes, existing concepts)
- Provide examples
- Specify output format

**Quality Checklist:**
- Atomicity
- Distinctness
- Quote coverage
- Relation accuracy
- Language
- Edge cases

---

## Database Schema

### Node Types

**Content:**
- `uuid`: Unique identifier
- `name`: Display name
- `title`: Book title
- `author`: Author name
- `summary`: Detailed summary (100 words)
- `summary_short`: Short summary (30 words)
- `category`: ResourceType (BOOK)
- `status`: ResourceStatus
- `processed_date`: Timestamp when concept extraction completed

**Quote:**
- `uuid`: Unique identifier
- `text`: Quote text
- `section`: Section name from markdown
- `page_reference`: Page number(s)
- `embedding`: Vector embedding (1024 dimensions)
- `created_at`: Creation timestamp
- `partition`: PartitionType (LEXICAL)

**Concept:**
- `uuid`: Unique identifier
- `name`: Concept name (same as title)
- `title`: Concept title
- `concept`: Core concept description
- `analysis`: Personal analysis
- `summary`: Detailed summary (100 words)
- `summary_short`: Short summary (30 words)
- `embedding`: Vector embedding (1024 dimensions)
- `source`: Source reference
- `partition`: PartitionType (DOMAIN)

**Person:**
- `uuid`: Unique identifier
- `name`: Person name
- `occupation`: Occupation (e.g., "Author")
- `summary`: Summary
- `summary_short`: Short summary

### Relationships

**QUOTED_IN:**
- `(Quote)-[:QUOTED_IN]->(Content)`
- Links quotes to their source content

**AUTHORED_BY:**
- `(Person)-[:AUTHORED_BY]->(Content)`
- Links authors to their content

**SUPPORTS:**
- `(Quote)-[:SUPPORTS]->(Concept)`
- Optional properties: `reasoning`, `confidence`
- Links quotes to concepts they support

**Concept Relations:**
- `(Concept)-[:GENERALIZES]->(Concept)`
- `(Concept)-[:SPECIFIC_OF]->(Concept)`
- `(Concept)-[:PART_OF]->(Concept)`
- `(Concept)-[:HAS_PART]->(Concept)`
- `(Concept)-[:OPPOSES]->(Concept)`
- `(Concept)-[:SIMILAR_TO]->(Concept)`
- `(Concept)-[:RELATES_TO]->(Concept)`
- `(Concept)-[:SUPPORTS]->(Concept)`
- `(Concept)-[:SUPPORTED_BY]->(Concept)`

**Bidirectional Creation:**
- Asymmetric relations create both directions automatically
- Symmetric relations use same type in both directions

---

## Error Handling

### Error Types

**1. Transient Errors:**
- Network issues
- Rate limits
- Timeouts
- **Handling:** Automatic retry (via LangChain)

**2. LLM Errors:**
- Parsing failures
- Invalid responses
- **Handling:** Store in state, route back to LLM

**3. Database Errors:**
- Connection failures
- Query errors
- **Handling:** Exception handling, state updates

**4. User-Fixable Errors:**
- Missing information
- Invalid input
- **Handling:** Interrupt for human input

### Error Accumulation

**State Fields:**
- `errors: Annotated[List[str], operator.add]`
- `warnings: Annotated[List[str], operator.add]`

**Pattern:**
```python
try:
    # ... operation ...
except Exception as e:
    return {
        "errors": [f"Operation failed: {str(e)}"]
    }
```

### Recovery Strategies

**Checkpointing:**
- State saved at every superstep
- Can resume from last checkpoint
- Successful nodes cached

**Graceful Degradation:**
- Continue processing if possible
- Accumulate errors for reporting
- Provide partial results

---

## Performance Considerations

### Optimization Strategies

**1. Lazy Initialization:**
- LLM and embeddings initialized on first use
- Reduces startup time
- Saves resources

**2. Embedding Reuse:**
- Embeddings stored in Neo4j
- Reuse existing embeddings
- Only generate for new content

**3. Batch Processing:**
- Process quotes in batches
- Reduce database round trips
- Improve throughput

**4. Vector Search:**
- Use indexes for fast similarity search
- Limit results to top-K
- Apply similarity threshold

**5. Parallel Execution (Future):**
- Parallelize duplicate detection
- Parallelize relation creation
- Use LangGraph's parallel node execution

### Performance Metrics

**Typical Processing Times:**
- Quote parsing: ~1-5 seconds per book
- Concept extraction: ~30-120 seconds per content
- Vector search: ~100-500ms per query
- LLM calls: ~2-10 seconds per call

**Scaling Considerations:**
- Neo4j performance with large graphs
- LLM API rate limits
- Embedding generation time
- Database connection pooling

### Resource Usage

**Memory:**
- State kept in memory during execution
- Embeddings can be large (1024 floats)
- Consider batch size limits

**CPU:**
- Embedding generation (Ollama)
- LLM processing (remote API)
- Database queries

**Network:**
- LLM API calls
- Database queries
- Embedding generation (if remote)

---

## See Also

- [API Reference](API.md) - Complete API documentation
- [Developer Guide](DEVELOPER.md) - Extension and modification guide
- [Workflows Documentation](WORKFLOWS.md) - Detailed workflow documentation

