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
Process book quotes and extract concepts via backend Temporal workflows and Curation UI.

### Steps

1. **Prepare Book Notes**:
   - Create markdown with quotes
   - Format with "# Citas" section
2. **Start Quote Parsing** (minerva_agent or API):
   - From minerva_agent: use workflow launcher tool `start_quote_parsing` (file_path, author, title); confirm in chat (HITL)
   - Backend QuoteParsing workflow parses file, submits quote items to curation DB; notification appears
3. **Review Quotes** (Curation UI):
   - Open Curation UI → **Quotes**; select workflow; accept/reject items; complete workflow
   - Workflow writes Content, Quote, Person and QUOTED_IN/AUTHORED_BY to Neo4j
4. **Start Concept Extraction** (minerva_agent or API):
   - Use `start_concept_extraction` (content_uuid); confirm in chat
   - Backend ConceptExtraction workflow extracts concepts/relations, submits to curation DB
5. **Review Concepts** (Curation UI):
   - Open Curation UI → **Concepts**; select workflow; accept/reject concept and relation items; complete workflow
   - Workflow writes Concept nodes, SUPPORTS (Quote→Concept), and concept relations to Neo4j
6. **Notifications**: Workflow events appear in Curation UI → **Notifications**

### Benefits
- Systematic concept extraction with human approval at each step
- Reusable concepts; knowledge graph integration
- Single Curation UI for quotes, concepts, and notifications

## Workflow 3: Inbox Classification (Backend + Curation UI)

### Overview
Classify inbox notes with LLM suggestions; approve moves in Curation UI; workflow executes file moves.

### Steps

1. **Start Inbox Classification** (minerva_agent or API):
   - From minerva_agent: use `start_inbox_classification` (inbox_path); confirm in chat (HITL)
   - Backend InboxClassification workflow scans inbox, LLM suggests target folder per note, submits to curation DB
2. **Review Classifications** (Curation UI):
   - Open Curation UI → **Inbox**; select workflow; accept/reject each move
   - Workflow executes approved moves (moves files from inbox to target folders)
3. **Notifications**: workflow_started, curation_pending, workflow_completed in Curation UI → **Notifications**

## Workflow 4: Vault Organization with Knowledge Graph

### Overview
Use agent to organize vault, then sync to knowledge graph.

### Steps

1. **Agent Organization** (read-only + workflow launch):
   - Open minerva-desktop; ask agent to organize inbox
   - Agent can read files and launch inbox classification workflow (HITL); Curation UI is where moves are approved
2. **Review Changes** (Curation UI):
   - Review and approve/reject moves in Curation UI (Inbox)
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

## Workflow 6: Daily Knowledge Management

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

