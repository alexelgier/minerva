# Zettel Agent Usage Guide

> **Current approach:** Quote parsing and concept extraction are now Temporal workflows in the backend. Use the **Curation UI** (Quotes, Concepts) and **minerva_agent** (workflow launcher tools) instead of the legacy zettel LangGraph server. See [Components Overview](../architecture/components.md) and [backend API](../../backend/docs/api/endpoints.md) (quotes/concepts endpoints).

How to use quote parsing and concept extraction (via Curation UI and minerva_agent).

## Current Workflow (Backend + Curation UI)

1. **Start quote parsing**: From minerva_agent (chat), use the workflow launcher tool `start_quote_parsing` with file_path, author, title. Confirm in chat (HITL). The backend Temporal workflow parses the file and submits quote items to the curation DB.
2. **Review quotes**: Open the Curation UI (Vue.js), go to **Quotes**, select the workflow, accept/reject items, then complete the workflow. The workflow writes Content, Quote, Person and relations to Neo4j.
3. **Start concept extraction**: From minerva_agent, use `start_concept_extraction` with content_uuid. Confirm in chat. The backend workflow extracts concepts and submits to curation DB.
4. **Review concepts**: In Curation UI go to **Concepts**, select the workflow, accept/reject concept and relation items, complete the workflow. The workflow writes Concept nodes and SUPPORTS/relations to Neo4j.

**Notifications**: Workflow events (workflow_started, curation_pending, workflow_completed) appear in Curation UI under **Notifications**.

---

## Legacy: Zettel Agent (Reference Only)

The following describes the deprecated LangGraph-based zettel agent.

### Start the Agent (Legacy)

```bash
cd backend/zettel
poetry run langgraph dev
```

Agent server exposed two graphs:
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
     "content_uuid": "uuid-from-quote-parsing",
     "user_suggestions": "Optional: Provide guidance for the extraction process"
   }
   ```

**Via API**:
```python
result = await client.runs.create(
    assistant_id="concept_extraction_graph",
    input={
        "content_uuid": "your-content-uuid",
        "user_suggestions": "Focus on extracting concepts related to machine learning. Pay special attention to any mentions of neural networks."
    }
)
```

**User Suggestions**: Optional freeform text that guides the extraction process. Suggestions are considered during:
- Concept extraction (Call 1.1a)
- Self-critique (Call 1.2)
- Refinement (Call 1.3)
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
    "content_uuid": content_uuid,
    "user_suggestions": "Optional: Provide guidance for the extraction process"
})

# Review concept proposals
proposals = concept_result.get("novel_concepts", [])
attributions = concept_result.get("existing_concepts_with_quotes", [])
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

The concept extraction process uses a sophisticated 3-phase workflow:

### Phase 1: LLM Self-Improvement Loop
1. Extract candidate concepts from quotes
2. Detect duplicates via semantic search and LLM validation
3. Generate relation search queries
4. Find relation candidates via vector search
5. Create relations between concepts
6. Self-critique against quality checklist
7. Refine extraction iteratively until quality passes (max 10 iterations)

**User Suggestions**: If provided, suggestions guide concept extraction, critique, and refinement.

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

**Note**: For detailed workflow documentation, see [Module Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md).

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

### Comprehensive Module Documentation

The zettel module has comprehensive documentation in `backend/zettel/docs/`:

- **[API Reference](../../backend/zettel/docs/API.md)** - Complete API reference
- **[Architecture Documentation](../../backend/zettel/docs/ARCHITECTURE.md)** - Deep technical architecture
- **[Developer Guide](../../backend/zettel/docs/DEVELOPER.md)** - Extension and modification guide
- **[Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md)** - Detailed workflow documentation

### Project-Level Documentation

- [Architecture Overview](../architecture/zettel.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Integration Workflows](integration-workflows.md)
- [Module README](../../backend/zettel/README.md)

