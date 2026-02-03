# Zettel Agent Setup Guide

> **DEPRECATED.** Quote parsing and concept extraction are now implemented as Temporal workflows in the backend. Use the **Curation UI** (Quotes, Concepts) and **minerva_agent** workflow launcher tools (start_quote_parsing, start_concept_extraction) instead. See [backend processing pipeline](../../backend/docs/architecture/processing-pipeline.md) and [curation API](../../backend/docs/api/endpoints.md). The instructions below refer to the legacy `backend/zettel` module (kept for reference only).

Detailed setup instructions for the legacy zettel agent (quote parsing and concept extraction).

## Prerequisites

- Python 3.12+
- Poetry
- Neo4j database (running locally or remotely)
- Google API key
- Ollama (for embeddings)

## Installation

### 1. Navigate to Directory

```bash
cd backend/zettel
```

### 2. Install Dependencies

```bash
poetry install
```

This installs:
- LangGraph and LangGraph CLI
- Neo4j driver
- Google Gemini integration
- Ollama embeddings
- Other dependencies

### 3. Configure Environment

Create `.env` file in `backend/zettel/`:

```env
# Required: Google API key for Gemini
GOOGLE_API_KEY=your-google-api-key-here
```

### 4. Configure Neo4j Connection

Edit `src/zettel_agent/db.py` to set Neo4j connection:

```python
def get_neo4j_connection_manager() -> Neo4jConnectionManager:
    return Neo4jConnectionManager(
        uri="bolt://localhost:7687",  # Your Neo4j URI
        user="neo4j",                 # Your username
        password="your-password"      # Your password
    )
```

Or use environment variables (modify code to read from env).

### 5. Start Neo4j

Ensure Neo4j is running:
- Neo4j Desktop: Start your database
- Neo4j Server: Start service
- Verify connection: `cypher-shell -u neo4j -p password`

### 6. Install Ollama Embedding Model

```bash
ollama pull mxbai-embed-large
```

Verify:
```bash
ollama list
# Should show mxbai-embed-large
```

## Running the Agent

### Development Server

```bash
poetry run langgraph dev
```

This:
- Starts LangGraph server (default: `http://127.0.0.1:2024`)
- Exposes two graphs: `quote_parse_graph` and `concept_extraction_graph`
- Creates vector indexes automatically on first run

### Production Deployment

```bash
poetry run langgraph up
```

## Configuration

### langgraph.json

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

### Graph Configuration

Edit graph files to customize:
- Similarity thresholds
- Batch sizes
- LLM models
- Vector search parameters

## Vector Indexes

Indexes are created automatically, but you can verify:

```cypher
SHOW INDEXES
```

Should show:
- `quote_embeddings_index` (1024 dimensions, cosine)
- `concept_embeddings_index` (1024 dimensions, cosine)

### Manual Index Creation

If needed, create manually:

```cypher
CREATE VECTOR INDEX quote_embeddings_index IF NOT EXISTS
FOR (n:Quote) ON (n.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};

CREATE VECTOR INDEX concept_embeddings_index IF NOT EXISTS
FOR (n:Concept) ON (n.embedding)
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 1024,
        `vector.similarity_function`: 'cosine'
    }
};
```

## Verification

### Check Server Status

```bash
curl http://127.0.0.1:2024/health
```

### Test Quote Parsing

Using LangGraph Studio or API:

```python
result = await quote_parse_graph.ainvoke({
    "file_path": "/path/to/book.md",
    "author": "Author Name",
    "title": "Book Title"
})
```

### Test Concept Extraction

```python
result = await concept_extraction_graph.ainvoke({
    "content_uuid": "your-content-uuid"
})
```

## Book Markdown Format

Zettel expects markdown files with this structure:

```markdown
# Citas

## Section Name

Quote text here

123

Another quote in the same section

124-125
```

- Quotes in `# Citas` section
- Section headers with `##`
- Page references at end of quotes
- Quotes separated by blank lines

## Troubleshooting

### Neo4j Connection Issues

**Connection refused**:
- Verify Neo4j is running
- Check connection string in `db.py`
- Verify credentials

**Authentication failed**:
- Check username and password
- Verify database exists
- Check Neo4j user permissions

### Vector Index Issues

**Index not found**:
- Indexes created automatically on first run
- Verify in Neo4j browser: `SHOW INDEXES`
- Check embedding model is available

**Embedding errors**:
- Verify Ollama is running: `ollama list`
- Check model is installed: `ollama pull mxbai-embed-large`
- Verify model name matches code

### LLM Issues

**API key errors**:
- Verify `GOOGLE_API_KEY` in `.env`
- Check API key is valid
- Verify quota not exceeded

**Model errors**:
- Check model name in code matches available models
- Verify API has access to model
- Check temperature and other parameters

### Performance Issues

**Slow processing**:
- Reduce batch size in graph configuration
- Check Neo4j performance
- Verify Ollama is running locally
- Consider using faster embedding model

**Memory issues**:
- Process quotes in smaller batches
- Clear processed quotes from memory
- Monitor Neo4j memory usage

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
├── langgraph.json                    # Server config
├── pyproject.toml                    # Dependencies
└── .env                              # Environment
```

### Customization

**Similarity Threshold**:
```python
SIMILARITY_THRESHOLD = 0.7  # Adjust in graph files
```

**Batch Size**:
```python
BATCH_SIZE = 50  # Process quotes in batches
```

**Model Settings**:
```python
model="gemini-2.5-flash-lite"  # Change model
temperature=0.3                 # Adjust creativity
```

## Integration

### With Minerva Desktop

1. Start zettel: `poetry run langgraph dev`
2. Configure desktop with zettel URL
3. Use `quote_parse_graph` or `concept_extraction_graph` as agent ID

### With LangGraph Studio

1. Start zettel: `poetry run langgraph dev`
2. Open LangGraph Studio
3. Connect to server and select graph

### With Backend API

Integrate zettel graphs into backend workflows:
- Call graphs via LangGraph SDK
- Process quotes from journal entries
- Extract concepts for knowledge graph

## Related Documentation

- [Architecture](../architecture/zettel.md)
- [Usage Guide](../usage/zettel.md)
- [Quick Start](quick-start.md)

