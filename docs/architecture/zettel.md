# Zettel Agent Architecture

Zettel Agent is a LangGraph-based system for processing book quotes and extracting atomic concepts (Zettels) using Zettelkasten methodology.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph Server                          │
│  - Two Graph Workflows                                 │
│  - State Management                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌──────────────┐      ┌──────────────────┐
│ quote_parse  │      │ concept_extract  │
│    graph     │      │      graph       │
└──────┬───────┘      └────────┬─────────┘
       │                       │
       ▼                       ▼
┌─────────────────────────────────────────────────────────┐
│              Neo4j Database                            │
│  - Content Nodes                                        │
│  - Quote Nodes (with embeddings)                      │
│  - Concept Nodes (with embeddings)                     │
│  - Vector Indexes                                       │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
            Ollama (Embeddings)
            Google Gemini (LLM)
```

## Technology Stack

- **LangGraph**: Workflow orchestration
- **Neo4j**: Graph database with vector search
- **Ollama**: Local embeddings (mxbai-embed-large)
- **Google Gemini**: LLM for concept extraction
- **Python 3.12+**: Runtime environment

## Graph Workflows

### Quote Parse Graph

**Purpose**: Extract quotes from markdown book notes and store in Neo4j

**Workflow**:
```
read_file → make_summary → parse_quotes → ensure_author_exists → write_to_db
```

**Nodes**:
1. **read_file**: Reads markdown file from filesystem
2. **make_summary**: Generates book summary using LLM
3. **parse_quotes**: Extracts quotes from "# Citas" section
4. **ensure_author_exists**: Creates Person entity if needed
5. **write_to_db**: Stores book, quotes, and relationships

**Input**:
```python
{
    "file_path": str,
    "author": str,
    "title": str
}
```

**Output**: Content UUID and stored quotes

### Concept Extraction Graph

**Purpose**: Extract atomic concepts from quotes using a sophisticated 3-phase workflow with LLM self-improvement and human review.

**Workflow Overview**:
The graph implements a 3-phase workflow:
- **Phase 1**: LLM Self-Improvement Loop - Autonomous extraction, duplicate detection, relation discovery, and quality validation
- **Phase 2**: Human Review Loop (HITL) - Human-guided refinement with feedback incorporation
- **Phase 3**: Commit to Database - Persistence to Neo4j and Obsidian file generation

**Input**:
```python
{
    "content_uuid": str,
    "user_suggestions": Optional[str]  # Optional freeform text to guide extraction
}
```

**Output**: 
- New Concept nodes created
- Relations between concepts created
- Quote-to-concept SUPPORTS relations created
- Obsidian zettel files generated
- Content marked as processed

**Note**: For detailed workflow documentation, see [Module Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md).

## Vector Search Architecture

### Embedding Model
- **Model**: mxbai-embed-large (via Ollama)
- **Dimensions**: 1024
- **Similarity**: Cosine similarity

### Vector Indexes
- **quote_embeddings_index**: For Quote nodes
- **concept_embeddings_index**: For Concept nodes

### Search Process
1. Generate embeddings for quotes (stored in Neo4j)
2. Use existing embeddings for similarity search
3. Filter by similarity threshold (0.7)
4. LLM validates matches

## Concept Extraction Process

The concept extraction process uses a sophisticated 3-phase workflow:

### Phase 1: LLM Self-Improvement Loop
1. Extract candidate concepts from quotes
2. Detect duplicates via semantic search and LLM validation
3. Generate relation search queries
4. Find relation candidates via vector search
5. Create relations between concepts
6. Self-critique against quality checklist
7. Refine extraction iteratively until quality passes (max 10 iterations)

### Phase 2: Human Review Loop
1. Present comprehensive extraction report
2. Wait for human feedback or approval
3. Incorporate feedback into extraction
4. Iterate until approval or max iterations (max 20)

### Phase 3: Commit to Database
1. Create Concept nodes in Neo4j
2. Create bidirectional concept relations
3. Create SUPPORTS relations from quotes to concepts
4. Generate Obsidian zettel files
5. Mark content as processed

**User Suggestions**: Optional freeform text input can be provided to guide the extraction process. Suggestions are considered during concept extraction, self-critique, and refinement phases.

**Note**: For detailed step-by-step workflow documentation, see [Module Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md).

## Database Schema

### Nodes
- **Content**: Book metadata (title, author, summary)
- **Quote**: Quote text, section, page reference, embedding
- **Concept**: Atomic concept (name, title, concept, analysis)
- **Person**: Author information

### Relationships
- **QUOTED_IN**: Quote → Content
- **AUTHORED_BY**: Person → Content
- **SUPPORTS**: Quote → Concept (via concept extraction)

### Vector Indexes
- Quote embeddings for similarity search
- Concept embeddings for matching

## LLM Integration

### Models Used
- **Google Gemini 2.5 Pro**: Complex reasoning tasks (concept extraction, duplicate detection, relation creation, self-critique, feedback incorporation)
- **Google Gemini 2.5 Flash**: Simpler tasks (relation query generation, summary generation)
- **Google Gemini 2.5 Flash Lite**: Quote parsing (summary generation)
- **Temperature**: 0 (deterministic outputs)

### Structured Outputs
- **CandidateConceptsResponse**: Candidate concepts with source quotes
- **DuplicateDetection**: Duplicate detection results
- **ConceptRelationsResponse**: Relations between concepts
- **SelfCritiqueResponse**: Quality assessment and critique
- **RefinementResponse**: Refined extraction
- **FeedbackIncorporationResponse**: Revised extraction with feedback

### Prompts
- **Zettelkasten Expert**: Specialized prompts for atomic concept extraction
- **Spanish Output**: All concept outputs in Spanish
- **Atomic Principle**: One clear idea per concept
- **User Suggestions**: Optional guidance incorporated into extraction, critique, and refinement prompts

## State Management

### Quote Parse Graph State
```python
{
    "file_path": str,
    "author": str,
    "title": str,
    "file_content": str,
    "book": Content,
    "parsed_author": Person,
    "quotes": List[Quote],
    "sections": List[str],
    "summary": str,
    "summary_short": str
}
```

### Concept Extraction Graph State
```python
{
    "content_uuid": str,
    "content": Content,
    "quotes": List[Quote],
    "user_suggestions": Optional[str],  # Optional freeform text to guide extraction
    "phase": Literal["extraction", "human_review", "commit", "end"],
    "iteration_count": int,
    "phase_1_iteration": int,
    "phase_2_iteration": int,
    "candidate_concepts": List[Dict],
    "novel_concepts": List[Dict],
    "existing_concepts_with_quotes": List[Dict],
    "relations": List[Dict],
    "quality_assessment": Optional[Dict],
    "human_feedback": Optional[str],
    "human_approved": bool,
    "errors": List[str],
    "warnings": List[str]
}
```

**Note**: For complete state schema documentation, see [Module API Reference](../../backend/zettel/docs/API.md).

## Performance Optimizations

- **Lazy Initialization**: LLM and vector stores initialized on first use
- **Batch Processing**: Process quotes in batches (50 at a time)
- **Embedding Reuse**: Use existing embeddings from Neo4j
- **Vector Search**: Direct Cypher queries for efficiency
- **Iteration Limits**: Max 100 iterations to prevent infinite loops

## Error Handling

- **Missing Embeddings**: Fallback to text-based search
- **LLM Errors**: Graceful degradation with error messages
- **Database Errors**: Transaction rollback and error reporting
- **Index Creation**: Handles existing indexes gracefully

## Configuration

### Environment Variables
```env
GOOGLE_API_KEY=your-api-key
```

### Neo4j Connection
Configured in `db.py`:
- URI: `bolt://localhost:7687`
- Database: `neo4j`
- Credentials: Set in connection manager

## Development

### Project Structure
```
zettel/
├── src/
│   └── zettel_agent/
│       ├── quote_parse_graph.py      # Quote parsing
│       ├── concept_extraction_graph.py # Concept extraction
│       ├── db.py                      # Neo4j operations
│       ├── obsidian_utils.py         # Obsidian file generation
│       ├── CONCEPT_EXTRACTION_DESIGN.md # Design document
│       └── __init__.py
├── docs/                              # Comprehensive module documentation
│   ├── README.md                      # Documentation index
│   ├── API.md                         # API reference
│   ├── ARCHITECTURE.md                # Technical architecture
│   ├── DEVELOPER.md                   # Developer guide
│   └── WORKFLOWS.md                   # Workflow documentation
├── langgraph.json                    # Graph configuration
└── pyproject.toml                    # Dependencies
```

### Running
```bash
poetry run langgraph dev
```

## Related Documentation

### Comprehensive Module Documentation

The zettel module has comprehensive documentation in `backend/zettel/docs/`:

- **[API Reference](../../backend/zettel/docs/API.md)** - Complete API reference
- **[Architecture Documentation](../../backend/zettel/docs/ARCHITECTURE.md)** - Deep technical architecture
- **[Developer Guide](../../backend/zettel/docs/DEVELOPER.md)** - Extension and modification guide
- **[Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md)** - Detailed workflow documentation

### Project-Level Documentation

- [Components Overview](components.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Usage Guide](../usage/zettel.md)
- [Module README](../../backend/zettel/README.md)

