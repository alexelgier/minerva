# Zettel Agent

A LangGraph-based agent system for processing book quotes and extracting atomic concepts (Zettels) from them. The Zettel agent implements a Zettelkasten methodology for knowledge management, processing quotes from books and organizing them into atomic, interconnected concepts.

## Features

- **Quote Parsing**: Extract quotes from markdown book notes with section and page references
- **Concept Extraction**: Generate atomic concepts (Zettels) from related quotes using vector search and LLM analysis
- **Vector Search**: Semantic similarity search using Neo4j vector indexes
- **Quote Attribution**: Automatically attribute quotes to existing concepts or propose new ones
- **Neo4j Integration**: Store quotes, concepts, and relationships in Neo4j graph database
- **Batch Processing**: Process quotes in batches for efficiency

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Neo4j database (running locally)
- Google API key (for Gemini)
- Ollama (for embeddings)

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
   - Create a `.env` file in this directory
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```
   - Ensure Neo4j is running (default: `bolt://localhost:7687`)

3. Ensure Neo4j vector indexes exist (created automatically on first run)

## Running the Agent

### Development Server

Start the development server:
```bash
poetry run langgraph dev
```

This exposes two graphs:
- `quote_parse_graph`: Parse quotes from markdown files
- `concept_extraction_graph`: Extract concepts from quotes

### Production Deployment

Build and deploy using LangGraph CLI:
```bash
poetry run langgraph up
```

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
1. Read markdown file
2. Generate book summary (LLM)
3. Parse quotes from "# Citas" section
4. Ensure author exists as Person entity
5. Store book, quotes, and relationships in Neo4j

### Concept Extraction Graph

Extracts atomic concepts from quotes:

**Input:**
```python
{
    "content_uuid": "uuid-of-content-node"
}
```

**Workflow:**
1. Ensure vector indexes exist
2. Load content and quotes
3. Attribute quotes to existing concepts (vector search + LLM)
4. Form new concepts from unprocessed quotes (clustering + LLM)
5. Iterate until all quotes are processed

## Architecture

- **LangGraph**: Stateful workflow orchestration
- **Neo4j**: Graph database for quotes, concepts, and relationships
- **Vector Search**: Semantic similarity using Ollama embeddings (mxbai-embed-large)
- **Google Gemini**: LLM for concept extraction and analysis
- **Two-Graph System**: Separate graphs for quote parsing and concept extraction

## Configuration

The agent is configured via `langgraph.json`:
```json
{
  "graphs": {
    "quote_parse_graph": "./src/zettel_agent/quote_parse_graph.py:graph",
    "concept_extraction_graph": "./src/zettel_agent/concept_extraction_graph.py:graph"
  },
  "env": ".env"
}
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |
| Neo4j connection | Configured in `db.py` | Yes | `bolt://localhost:7687` |

## Usage Examples

### Parse Quotes from a Book

```python
result = await quote_parse_graph.ainvoke({
    "file_path": "/path/to/book.md",
    "author": "Vladimir Lenin",
    "title": "Obras Completas Tomo IV"
})
```

### Extract Concepts from Quotes

```python
result = await concept_extraction_graph.ainvoke({
    "content_uuid": "43ecf73b-01c6-426d-978a-1b73e041370c"
})
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
```

- Quotes are separated by blank lines
- Page references appear at the end of each quote
- Section headers use `##`

## Concept Extraction Process

1. **Vector Search**: Find similar existing concepts using quote embeddings
2. **LLM Analysis**: Determine if quote supports existing concept
3. **Clustering**: Group unprocessed quotes by semantic similarity
4. **Concept Proposal**: Generate atomic concept from quote cluster
5. **Iteration**: Continue until all quotes are attributed or proposed

## Database Schema

- **Content**: Book nodes with metadata
- **Quote**: Quote nodes with text, section, page reference, and embeddings
- **Concept**: Atomic concept nodes (Zettels) with title, concept, analysis
- **Person**: Author nodes
- **Relationships**:
  - `QUOTED_IN`: Quote → Content
  - `AUTHORED_BY`: Person → Content
  - Concept relationships (via concept_extraction_graph)

## Development

### Project Structure

```
zettel/
├── src/
│   └── zettel_agent/
│       ├── quote_parse_graph.py      # Quote parsing workflow
│       ├── concept_extraction_graph.py # Concept extraction workflow
│       ├── db.py                      # Neo4j connection and queries
│       └── __init__.py
├── langgraph.json                    # LangGraph configuration
├── pyproject.toml                    # Poetry dependencies
└── .env                              # Environment variables
```

### Adding New Features

- Modify graph workflows in respective graph files
- Add database queries in `db.py`
- Update vector search thresholds in graph files

## Troubleshooting

### Neo4j Connection Issues
- Verify Neo4j is running: `neo4j status`
- Check connection settings in `db.py`
- Ensure database exists

### Vector Index Issues
- Indexes are created automatically on first run
- Verify index creation in Neo4j browser
- Check embedding model is available in Ollama

### LLM Issues
- Verify Google API key is set
- Check API quota limits
- Review error logs for specific failures

## Documentation

For detailed documentation, see:
- [Architecture Documentation](../../docs/architecture/zettel.md)
- [Setup Guide](../../docs/setup/zettel-setup.md)
- [Usage Guide](../../docs/usage/zettel.md)

## License

See project root LICENSE file.
