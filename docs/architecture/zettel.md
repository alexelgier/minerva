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

**Purpose**: Extract atomic concepts from quotes using vector search and LLM analysis

**Workflow**:
```
ensure_indices → load_content_and_quotes → [attribute_quotes | form_concept_from_seed] → end
```

**Nodes**:
1. **ensure_indices**: Creates vector indexes if needed
2. **load_content_and_quotes**: Loads content and initializes state
3. **attribute_quotes_to_existing_concepts**: Attributes quotes to existing concepts
4. **form_concept_from_seed**: Creates new concepts from quote clusters
5. **Conditional Loop**: Continues until all quotes processed

**Input**:
```python
{
    "content_uuid": str
}
```

**Output**: Quote attributions and concept proposals

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

### Phase 1: Attribution to Existing Concepts
1. Get unprocessed quotes
2. Vector search for similar concepts
3. LLM analyzes if quote supports concept
4. Attribute if confidence > threshold

### Phase 2: New Concept Formation
1. Pick seed quote (unprocessed)
2. Vector search for similar quotes
3. Cluster quotes by similarity
4. LLM generates concept proposal
5. Store proposal for later validation

### Phase 3: Iteration
- Continues until all quotes processed
- Max 100 iterations to prevent infinite loops
- Tracks processed quotes by UUID

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
- **Google Gemini 2.5 Flash Lite**: Concept extraction and analysis
- **Temperature**: 0.3 (some creativity for analysis)

### Structured Outputs
- **QuoteAnalysisResult**: Should attribute, concept UUID, reasoning, confidence
- **ConceptProposal**: Name, title, concept, analysis, source quotes

### Prompts
- **Zettelkasten Expert**: Specialized prompts for atomic concept extraction
- **Spanish Output**: All concept outputs in Spanish
- **Atomic Principle**: One clear idea per concept

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
    "processed_quote_uuids": Set[str],
    "quote_attributions": List[QuoteAttribution],
    "concept_proposals": List[ConceptProposal],
    "analysis_complete": bool,
    "iteration_count": int
}
```

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
│       └── __init__.py
├── langgraph.json                    # Graph configuration
└── pyproject.toml                    # Dependencies
```

### Running
```bash
poetry run langgraph dev
```

## Related Documentation

- [Components Overview](components.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Usage Guide](../usage/zettel.md)
- [zettel README](../../backend/zettel/README.md)

