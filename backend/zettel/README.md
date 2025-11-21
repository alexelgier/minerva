# Zettel Agent

A LangGraph-based agent system for processing book quotes and extracting atomic concepts (Zettels) from them. The Zettel agent implements a Zettelkasten methodology for knowledge management, processing quotes from books and organizing them into atomic, interconnected concepts.

## Overview

The Zettel Agent is a sophisticated knowledge extraction system that transforms unstructured book quotes into a structured knowledge graph. It uses a two-stage workflow:

1. **Quote Parsing**: Extracts quotes from markdown book notes with section and page references
2. **Concept Extraction**: Generates atomic concepts (Zettels) from related quotes using vector search and LLM analysis

The system follows Zettelkasten principles, ensuring each concept is:
- **Atomic**: Contains one clear, standalone idea
- **Distinct**: Semantically unique from existing concepts
- **Interconnected**: Related to other concepts through typed relationships
- **Attributed**: Linked to source quotes that support it

## Features

### Quote Parsing Graph
- **Markdown Parsing**: Extracts quotes from structured markdown files
- **Section Detection**: Preserves section headers and organization
- **Page References**: Captures page numbers and ranges
- **Author Management**: Automatically creates and links author entities
- **Summary Generation**: LLM-generated book summaries (short and detailed)
- **Web Search Enrichment**: Automatically enriches author and book summaries using Gemini's built-in Google Search tool (grounding)
- **Vector Embeddings**: Automatic embedding generation for semantic search

### Concept Extraction Graph
- **Three-Phase Workflow**:
  - **Phase 1**: LLM self-improvement loop with quality validation
  - **Phase 2**: Human-in-the-loop review and feedback incorporation
  - **Phase 3**: Database commit and Obsidian file generation
- **User Suggestions**: Optional freeform text input to guide the extraction process
- **Duplicate Detection**: Semantic similarity search to avoid duplicate concepts
- **Relation Discovery**: Automatic detection of concept relationships
- **Quality Assurance**: Self-critique against quality checklist
- **Human Review**: Interactive review process with feedback incorporation
- **Obsidian Integration**: Automatic generation of Zettel markdown files

### Technical Features
- **Vector Search**: Semantic similarity using Neo4j vector indexes
- **Neo4j Integration**: Graph database for quotes, concepts, and relationships
- **Batch Processing**: Efficient processing of large quote collections
- **Error Recovery**: Graceful error handling and state checkpointing
- **Parallel Execution**: Support for parallel processing (where applicable)

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Neo4j database (running locally or remotely)
- Google API key (for Gemini)
- Ollama (for embeddings)

### Installation

1. **Install dependencies:**
```bash
cd backend/zettel
poetry install
```

2. **Set up environment variables:**
   - Create a `.env` file in this directory
   - Add your Google API key (required for LLM and web search):
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```
     The same API key is used for both LLM and Google Search grounding (no CSE ID needed).
     See: https://ai.google.dev/gemini-api/docs/google-search
   - Ensure Neo4j is running (default: `bolt://localhost:7687`)

3. **Configure Neo4j connection:**
   - Edit `src/zettel_agent/db.py` to set your Neo4j credentials
   - Or modify `get_neo4j_connection_manager()` to read from environment variables

4. **Install Ollama embedding model:**
```bash
ollama pull mxbai-embed-large
```

5. **Ensure Neo4j vector indexes exist** (created automatically on first run)

## Running the Agent

### Development Server

Start the development server:
```bash
poetry run langgraph dev
```

This exposes two graphs:
- `quote_parse_graph`: Parse quotes from markdown files
- `concept_extraction_graph`: Extract concepts from quotes

The server runs on `http://127.0.0.1:2024` by default.

### Production Deployment

Build and deploy using LangGraph CLI:
```bash
poetry run langgraph up
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph Server                          │
│  - Two Graph Workflows                                 │
│  - State Management                                    │
│  - Checkpointing                                       │
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
        ┌──────────┴──────────┐
        ▼                     ▼
   Ollama (Embeddings)    Google Gemini (LLM)
```

### Technology Stack

- **LangGraph**: Workflow orchestration and state management
- **Neo4j**: Graph database with vector search capabilities
- **Ollama**: Local embeddings (mxbai-embed-large)
- **Google Gemini**: LLM for concept extraction and analysis
- **Python 3.12+**: Runtime environment

## Agent Graphs

### Quote Parse Graph

Processes markdown book notes and extracts quotes:

**Input:**
```python
{
    "file_path": "/path/to/book.md",
    "author": "Author Name",
    "title": "Book Title"
}
```

**Workflow:**
1. **read_file**: Reads markdown file from filesystem
2. **make_summary**: Generates book summary using LLM, then enriches it with web search information using Gemini's Google Search tool
3. **parse_quotes**: Extracts quotes from "# Citas" section with section and page references
4. **get_or_create_author**: Gets existing author or creates new one with web search enrichment (only enriches newly created authors)
5. **write_to_db**: Stores book, quotes, and relationships in Neo4j with embeddings

**Output:**
- Content UUID
- List of created quote UUIDs
- Author relationship created

### Concept Extraction Graph

Extracts atomic concepts from quotes using a sophisticated 3-phase workflow:

**Input:**
```python
{
    "content_uuid": "uuid-of-content-node",
    "user_suggestions": "Optional freeform text suggestions for the extraction process"
}
```

**Phase 1: LLM Self-Improvement Loop**
1. **check_content_processed**: Verifies content hasn't been processed
2. **load_content_quotes**: Loads all quotes for the content
3. **extract_candidate_concepts**: LLM extracts candidate concepts from quotes
4. **detect_duplicates_all**: Semantic search and LLM validation to find duplicates
5. **generate_relation_queries**: Generates search queries for finding related concepts
6. **search_relation_candidates**: Vector search for relation candidates
7. **create_relations_all**: LLM determines relations between concepts
8. **self_critique**: LLM validates extraction against quality checklist
9. **refine_extraction**: LLM refines extraction based on critique
10. **Loop**: Continues until quality passes or max iterations reached

**Phase 2: Human Review Loop**
1. **present_for_review**: Generates comprehensive report and interrupts for human review
2. **incorporate_feedback**: LLM incorporates human feedback into extraction
3. **Loop**: Continues until human approval or max iterations reached

**Phase 3: Commit to Database**
1. **create_concepts_db**: Creates Concept nodes in Neo4j
2. **create_relations_db**: Creates bidirectional concept relations
3. **create_supports_relations**: Creates SUPPORTS relations from quotes to concepts
4. **create_obsidian_files**: Generates Obsidian zettel markdown files
5. **update_processed_date**: Marks content as processed

**Output:**
- New Concept nodes created
- Relations between concepts created
- Quote-to-concept SUPPORTS relations created
- Obsidian zettel files generated
- Content marked as processed

## Configuration

### langgraph.json

The agent is configured via `langgraph.json`:
```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "quote_parse_graph": "./src/zettel_agent/quote_parse_graph.py:graph",
    "concept_extraction_graph": "./src/zettel_agent/concept_extraction_graph.py:graph"
  },
  "env": ".env"
}
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini LLM and Google Search grounding | Yes | - |
| Neo4j connection | Configured in `db.py` | Yes | `bolt://localhost:7687` |

### Neo4j Connection

Configure in `src/zettel_agent/db.py`:
```python
def get_neo4j_connection_manager() -> Neo4jConnectionManager:
    return Neo4jConnectionManager(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="your-password"
    )
```

## Usage Examples

### Parse Quotes from a Book

**Via LangGraph Studio:**
1. Connect to agent server at `http://127.0.0.1:2024`
2. Select `quote_parse_graph`
3. Input:
   ```json
   {
     "file_path": "/path/to/book.md",
     "author": "Vladimir Lenin",
     "title": "Obras Completas Tomo IV"
   }
   ```

**Via Python API:**
```python
from langchain.langgraph_sdk import get_client

client = get_client("http://127.0.0.1:2024")
result = await client.runs.create(
    assistant_id="quote_parse_graph",
    input={
        "file_path": "/path/to/book.md",
        "author": "Vladimir Lenin",
        "title": "Obras Completas Tomo IV"
    }
)

content_uuid = result["content_uuid"]
```

### Extract Concepts from Quotes

**Via LangGraph Studio:**
1. Select `concept_extraction_graph`
2. Input:
   ```json
   {
     "content_uuid": "43ecf73b-01c6-426d-978a-1b73e041370c",
     "user_suggestions": "Focus on extracting concepts related to machine learning. Pay special attention to any mentions of neural networks."
   }
   ```

**Via Python API:**
```python
result = await client.runs.create(
    assistant_id="concept_extraction_graph",
    input={
        "content_uuid": content_uuid,
        "user_suggestions": "Focus on extracting concepts related to machine learning. Pay special attention to any mentions of neural networks."
    }
)

# Review results
novel_concepts = result["novel_concepts"]
relations = result["relations"]
```

### Complete Workflow Example

```python
# Step 1: Parse quotes
quote_result = await client.runs.create(
    assistant_id="quote_parse_graph",
    input={
        "file_path": "/path/to/book.md",
        "author": "Vladimir Lenin",
        "title": "Obras Completas Tomo IV"
    }
)

content_uuid = quote_result["content_uuid"]

# Step 2: Extract concepts
concept_result = await client.runs.create(
    assistant_id="concept_extraction_graph",
    input={
        "content_uuid": content_uuid,
        "user_suggestions": "Optional: Provide guidance for the extraction process"
    }
)

# Review concept proposals
proposals = concept_result["novel_concepts"]
attributions = concept_result["existing_concepts_with_quotes"]
```

## Quote Format

The quote parser expects markdown files with this structure:

```markdown
# Citas

## Section Name

Quote text here

123

Another quote in the same section

124-125

## Another Section

More quotes here

200
```

**Format Rules:**
- Main header: `# Citas` (required)
- Sections: `## Section Name` (optional but recommended)
- Quotes: Separated by blank lines
- Page references: Numbers at end of quote (optional)
  - Single page: `123`
  - Page range: `124-125`
  - Multiple pages: `200\n201\n202`

## Concept Extraction Process

### Quality Criteria

The system validates concepts against these criteria:

1. **Atomicity**: Each concept contains ONE clear, standalone idea
2. **Distinctness**: New concepts are semantically distinct from existing concepts
3. **Quote Coverage**: All meaningful quotes are attributed to at least one concept
4. **Relation Accuracy**: Relations are semantically correct and meaningful
5. **Language**: All concepts are in Spanish
6. **Edge Cases**: Unattributed quotes, disconnected concepts are properly noted

### Workflow Details

**Phase 1: Extraction and Refinement**
- Extracts candidate concepts from all quotes
- Performs semantic duplicate detection
- Generates relation search queries
- Finds relation candidates via vector search
- Creates typed relations between concepts
- Self-critiques against quality checklist
- Refines extraction iteratively until quality passes

**Phase 2: Human Review**
- Presents comprehensive extraction report
- Waits for human feedback or approval
- Incorporates feedback into extraction
- Iterates until approval or max iterations

**Phase 3: Persistence**
- Creates Concept nodes in Neo4j
- Creates bidirectional concept relations
- Links quotes to concepts via SUPPORTS relations
- Generates Obsidian zettel files
- Marks content as processed

## Database Schema

### Nodes

- **Content**: Book metadata (title, author, summary, processed_date)
- **Quote**: Quote text, section, page reference, embedding
- **Concept**: Atomic concept (name, title, concept, analysis, summary, summary_short, embedding)
- **Person**: Author information (name, occupation, summary)

### Relationships

- **QUOTED_IN**: Quote → Content
- **AUTHORED_BY**: Person → Content
- **SUPPORTS**: Quote → Concept (with optional reasoning and confidence)
- **Concept Relations**: 9 typed relations between concepts:
  - GENERALIZES ↔ SPECIFIC_OF
  - PART_OF ↔ HAS_PART
  - SUPPORTS ↔ SUPPORTED_BY
  - OPPOSES (symmetric)
  - SIMILAR_TO (symmetric)
  - RELATES_TO (symmetric)

### Vector Indexes

- **quote_embeddings_index**: For Quote nodes (1024 dimensions, cosine similarity)
- **concept_embeddings_index**: For Concept nodes (1024 dimensions, cosine similarity)

## Project Structure

```
zettel/
├── src/
│   └── zettel_agent/
│       ├── __init__.py              # Module exports
│       ├── quote_parse_graph.py     # Quote parsing workflow
│       ├── concept_extraction_graph.py # Concept extraction workflow
│       ├── db.py                    # Neo4j connection and queries
│       ├── obsidian_utils.py        # Obsidian file generation
│       └── CONCEPT_EXTRACTION_DESIGN.md # Design document
├── docs/                            # Documentation
│   ├── README.md                    # Documentation index
│   ├── API.md                       # API reference
│   ├── ARCHITECTURE.md              # Architecture details
│   ├── DEVELOPER.md                 # Developer guide
│   └── WORKFLOWS.md                 # Workflow documentation
├── langgraph.json                   # LangGraph configuration
├── pyproject.toml                   # Poetry dependencies
├── poetry.lock                      # Dependency lock file
└── README.md                        # This file
```

## Troubleshooting

### Neo4j Connection Issues

**Connection refused:**
- Verify Neo4j is running: `neo4j status`
- Check connection string in `db.py`
- Verify credentials

**Authentication failed:**
- Check username and password
- Verify database exists
- Check Neo4j user permissions

### Vector Index Issues

**Index not found:**
- Indexes are created automatically on first run
- Verify in Neo4j browser: `SHOW INDEXES`
- Check embedding model is available

**Embedding errors:**
- Verify Ollama is running: `ollama list`
- Check model is installed: `ollama pull mxbai-embed-large`
- Verify model name matches code

### LLM Issues

**API key errors:**
- Verify `GOOGLE_API_KEY` in `.env`
- Check API key is valid
- Verify quota not exceeded

**Model errors:**
- Check model name in code matches available models
- Verify API has access to model
- Check temperature and other parameters

### Performance Issues

**Slow processing:**
- Reduce batch size in graph configuration
- Check Neo4j performance
- Verify Ollama is running locally
- Consider using faster embedding model

**Memory issues:**
- Process quotes in smaller batches
- Clear processed quotes from memory
- Monitor Neo4j memory usage

### Workflow Issues

**Content already processed:**
- Check `processed_date` field on Content node
- Workflow will exit early if already processed
- To reprocess, clear `processed_date` field

**Human review not appearing:**
- Verify checkpointer is configured
- Check LangGraph API is running
- Review interrupt configuration

## Development

### Adding New Features

**Modify graph workflows:**
- Edit graph files in `src/zettel_agent/`
- Update state schemas as needed
- Add new nodes and edges

**Add database queries:**
- Add functions to `db.py`
- Follow existing patterns for serialization
- Update documentation

**Customize LLM prompts:**
- Modify prompt strings in graph nodes
- Update system prompts for different behaviors
- Test with various inputs

### Testing

Run tests (when available):
```bash
poetry run pytest
```

### Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions
- Keep functions focused and single-purpose

## Documentation

For detailed documentation, see:

- **[API Reference](docs/API.md)**: Complete API reference for all functions and classes
- **[Architecture](docs/ARCHITECTURE.md)**: Technical architecture and design details
- **[Developer Guide](docs/DEVELOPER.md)**: Guide for extending and modifying the module
- **[Workflows](docs/WORKFLOWS.md)**: Detailed workflow documentation

Also see:
- [Architecture Documentation](../../docs/architecture/zettel.md) - Project-level architecture
- [Setup Guide](../../docs/setup/zettel-setup.md) - Detailed setup instructions
- [Usage Guide](../../docs/usage/zettel.md) - Usage examples and patterns

## Contributing

When contributing to this module:

1. Follow the existing code style and patterns
2. Add comprehensive docstrings to new functions
3. Update relevant documentation
4. Test your changes thoroughly
5. Update the [CHANGELOG.md](CHANGELOG.md) if applicable

## License

See project root LICENSE file.
