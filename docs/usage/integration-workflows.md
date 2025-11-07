# Integration Workflows

Common workflows that use multiple Minerva components together.

## Workflow 1: Journal Processing with Agent Assistance

### Overview
Use minerva_agent to help prepare journal entries before backend processing.

### Steps

1. **Write Journal Entry** in Obsidian
2. **Agent Review**:
   - Open minerva-desktop
   - Ask agent to review journal entry
   - Agent suggests improvements or extracts key points
3. **Submit to Backend**:
   - Use backend API to submit journal
   - Backend processes with LLM extraction
4. **Curation**:
   - Review extracted entities
   - Approve or modify relationships
5. **Knowledge Graph Update**:
   - Curated data stored in Neo4j
   - Concepts linked to journal entry

### Benefits
- Agent helps improve journal quality
- Better entity extraction
- More accurate relationships

## Workflow 2: Book Analysis Pipeline

### Overview
Process book quotes and extract concepts, then integrate with knowledge graph.

### Steps

1. **Prepare Book Notes**:
   - Create markdown with quotes
   - Format with "# Citas" section
2. **Parse Quotes** (zettel):
   - Run `quote_parse_graph`
   - Store quotes in Neo4j
3. **Extract Concepts** (zettel):
   - Run `concept_extraction_graph`
   - Generate concept proposals
4. **Review Concepts**:
   - Review proposals in Neo4j
   - Accept or modify concepts
5. **Link to Knowledge Graph**:
   - Link concepts to journal entries
   - Create relationships with entities
   - Build concept network

### Benefits
- Systematic concept extraction
- Reusable concepts
- Knowledge graph integration

## Workflow 3: Vault Organization with Knowledge Graph

### Overview
Use agent to organize vault, then sync to knowledge graph.

### Steps

1. **Agent Organization**:
   - Open minerva-desktop
   - Ask agent to organize inbox
   - Agent plans and executes
2. **Review Changes**:
   - Check file operations
   - Approve or modify
3. **Sync to Backend**:
   - Backend syncs Obsidian vault
   - Updates knowledge graph
   - Links new files to entities
4. **Query Knowledge Graph**:
   - Query for related files
   - Find connections
   - Discover patterns

### Benefits
- Automated organization
- Knowledge graph integration
- Pattern discovery

## Workflow 4: Concept Discovery and Linking

### Overview
Extract concepts from books, then link to journal entries and entities.

### Steps

1. **Extract Concepts** (zettel):
   - Process book quotes
   - Extract atomic concepts
2. **Query Knowledge Graph**:
   - Find related journal entries
   - Identify related entities
3. **Create Relationships**:
   - Link concepts to entries
   - Connect to entities
   - Build concept network
4. **Agent Assistance**:
   - Use agent to explore connections
   - Query knowledge graph
   - Discover patterns

### Benefits
- Cross-reference concepts
- Build knowledge network
- Discover insights

## Workflow 5: Daily Knowledge Management

### Overview
Complete daily workflow using all components.

### Morning
1. **Review Yesterday**:
   - Agent reads yesterday's journal
   - Summarizes key points
2. **Plan Today**:
   - Agent helps plan tasks
   - Creates notes

### During Day
1. **Capture Information**:
   - Add notes to inbox
   - Agent organizes
2. **Process Quotes** (if reading):
   - Extract quotes from books
   - Process with zettel

### Evening
1. **Write Journal**:
   - Write daily entry
   - Agent reviews
2. **Process Journal**:
   - Submit to backend
   - Review entities
   - Approve relationships
3. **Review Concepts**:
   - Review new concepts from books
   - Link to journal entries

## Workflow 6: Research and Analysis

### Overview
Research topic using multiple sources, extract concepts, build knowledge.

### Steps

1. **Collect Sources**:
   - Books, articles, notes
   - Store in Obsidian
2. **Extract Quotes**:
   - Process with zettel
   - Extract concepts
3. **Write Analysis**:
   - Create analysis note
   - Link to concepts
4. **Process Analysis**:
   - Submit to backend
   - Extract entities
   - Link to concepts
5. **Build Knowledge**:
   - Query knowledge graph
   - Find connections
   - Discover insights

## Best Practices

### Component Selection

- **File Operations**: Use minerva_agent
- **Quote Processing**: Use zettel
- **Journal Processing**: Use backend API
- **Visualization**: Use minerva-desktop

### Workflow Design

- Start with agent assistance
- Process with specialized tools
- Review and curate
- Integrate into knowledge graph

### Data Flow

- Raw data → Processing → Curation → Knowledge Graph
- Use agents for preparation
- Use specialized tools for extraction
- Use backend for storage

## Related Documentation

- [Usage Overview](overview.md)
- [Common Use Cases](common-use-cases.md)
- [Component Usage Guides](minerva-desktop.md)

