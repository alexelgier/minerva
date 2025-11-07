# Zettel Agent Usage Guide

How to use the zettel agent for processing book quotes and extracting concepts.

## Getting Started

### Start the Agent

```bash
cd backend/zettel
poetry run langgraph dev
```

Agent server exposes two graphs:
- `quote_parse_graph`: Parse quotes from markdown
- `concept_extraction_graph`: Extract concepts from quotes

## Quote Parsing Workflow

### Prepare Book Notes

Create markdown file with this structure:

```markdown
# Citas

## Chapter 1

Quote text here

123

Another quote from the same chapter

124-125

## Chapter 2

More quotes here

200
```

### Run Quote Parsing

**Via LangGraph Studio**:
1. Connect to agent server
2. Select `quote_parse_graph`
3. Input:
   ```json
   {
     "file_path": "/path/to/book.md",
     "author": "Author Name",
     "title": "Book Title"
   }
   ```

**Via API**:
```python
from langchain.langgraph_sdk import get_client

client = get_client("http://127.0.0.1:2024")
result = await client.runs.create(
    assistant_id="quote_parse_graph",
    input={
        "file_path": "/path/to/book.md",
        "author": "Author Name",
        "title": "Book Title"
    }
)
```

### What Happens

1. **Read File**: Reads markdown file
2. **Generate Summary**: LLM creates book summary
3. **Parse Quotes**: Extracts quotes from "# Citas" section
4. **Create Author**: Ensures Person entity exists
5. **Store in Neo4j**: Saves book, quotes, and relationships

### Results

- Content node created in Neo4j
- Quote nodes created with embeddings
- Author relationship created
- Quotes linked to content

## Concept Extraction Workflow

### Prerequisites

- Quotes must be parsed first
- Content UUID from quote parsing
- Vector indexes created (automatic)

### Run Concept Extraction

**Via LangGraph Studio**:
1. Select `concept_extraction_graph`
2. Input:
   ```json
   {
     "content_uuid": "uuid-from-quote-parsing"
   }
   ```

**Via API**:
```python
result = await client.runs.create(
    assistant_id="concept_extraction_graph",
    input={
        "content_uuid": "your-content-uuid"
    }
)
```

### What Happens

1. **Load Content**: Loads content and quotes
2. **Attribute Quotes**: Matches quotes to existing concepts
3. **Form Concepts**: Creates new concepts from quote clusters
4. **Iterate**: Continues until all quotes processed

### Results

- Quote attributions to existing concepts
- New concept proposals
- Concepts stored in Neo4j
- Relationships created

## Usage Examples

### Complete Workflow

**Step 1: Parse Quotes**
```python
quote_result = await quote_parse_graph.ainvoke({
    "file_path": "/path/to/book.md",
    "author": "Vladimir Lenin",
    "title": "Obras Completas Tomo IV"
})

content_uuid = quote_result["content_uuid"]
```

**Step 2: Extract Concepts**
```python
concept_result = await concept_extraction_graph.ainvoke({
    "content_uuid": content_uuid
})

# Review concept proposals
proposals = concept_result["concept_proposals"]
attributions = concept_result["quote_attributions"]
```

### Batch Processing

Process multiple books:

```python
books = [
    {"file_path": "book1.md", "author": "Author 1", "title": "Book 1"},
    {"file_path": "book2.md", "author": "Author 2", "title": "Book 2"},
]

for book in books:
    # Parse quotes
    result = await quote_parse_graph.ainvoke(book)
    
    # Extract concepts
    await concept_extraction_graph.ainvoke({
        "content_uuid": result["content_uuid"]
    })
```

## Book Markdown Format

### Required Structure

```markdown
# Citas

## Section Name

Quote text here

Page number

Another quote

Page range
```

### Format Rules

- **Main Header**: `# Citas` (required)
- **Sections**: `## Section Name` (optional but recommended)
- **Quotes**: Separated by blank lines
- **Page References**: Numbers at end of quote (optional)

### Example

```markdown
# Citas

## Introduction

This is an important quote about the topic.

5

Another quote that continues the thought.

6-7

## Main Content

More quotes here with different page numbers.

50
51
52-53
```

## Concept Extraction Process

### Phase 1: Attribution

1. Get unprocessed quotes
2. Vector search for similar concepts
3. LLM analyzes if quote supports concept
4. Attribute if confidence > 0.7

### Phase 2: Concept Formation

1. Pick seed quote (unprocessed)
2. Vector search for similar quotes
3. Cluster quotes (max 10 per cluster)
4. LLM generates concept proposal
5. Store proposal

### Phase 3: Iteration

- Continues until all quotes processed
- Max 100 iterations
- Tracks processed quotes

## Reviewing Results

### Quote Attributions

Check which quotes were attributed to existing concepts:
```python
attributions = result["quote_attributions"]
for attr in attributions:
    print(f"Quote {attr.quote_uuid} → Concept {attr.concept_uuid}")
    print(f"Confidence: {attr.confidence}")
    print(f"Reasoning: {attr.reasoning}")
```

### Concept Proposals

Review new concept proposals:
```python
proposals = result["concept_proposals"]
for prop in proposals:
    print(f"Name: {prop.name}")
    print(f"Title: {prop.title}")
    print(f"Concept: {prop.concept}")
    print(f"Analysis: {prop.analysis}")
    print(f"Source Quotes: {len(prop.source_quote_uuids)}")
```

## Best Practices

### Quote Format

- Keep quotes in "# Citas" section
- Use section headers for organization
- Include page references when available
- Separate quotes with blank lines

### Concept Review

- Review concept proposals before accepting
- Check quote attributions for accuracy
- Verify concepts are atomic (one idea)
- Ensure concepts are in Spanish (as configured)

### Performance

- Process books in batches
- Monitor Neo4j performance
- Check embedding generation time
- Review iteration counts

## Troubleshooting

### Quotes Not Parsed

- Verify "# Citas" section exists
- Check markdown format
- Review parsing logs
- Ensure file is readable

### Concepts Not Extracted

- Verify quotes were parsed
- Check content UUID is correct
- Verify vector indexes exist
- Check LLM API key

### Low Quality Concepts

- Adjust similarity threshold
- Review quote clustering
- Check LLM temperature
- Verify quote quality

### Performance Issues

- Reduce batch size
- Process in smaller chunks
- Check Neo4j performance
- Verify Ollama is running

## Integration

### With Backend API

Integrate zettel into backend workflows:
- Process quotes from journal entries
- Extract concepts for knowledge graph
- Link concepts to journal entities

### With Knowledge Graph

Concepts stored in Neo4j:
- Query concepts
- Link to other entities
- Build concept relationships
- Visualize in graph

## Related Documentation

- [Architecture](../architecture/zettel.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Integration Workflows](integration-workflows.md)

