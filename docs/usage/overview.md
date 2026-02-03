# Usage Overview

How all Minerva components work together to provide a complete knowledge management system.

## Component Roles

### Backend API
- Processes journal entries
- Manages curation workflows
- Stores knowledge graph data
- Provides REST API

### minerva-desktop
- User interface for agents
- Real-time chat with agents
- Task and file management
- Visual feedback

### minerva_agent
- Obsidian vault assistance (read-only tools: read_file, list_dir, glob, grep)
- Workflow launcher tools (quote parsing, concept extraction, inbox classification) with HITL confirmation
- Query workflow status

### Curation UI (Vue.js)
- Queue: Journal entity and relationship curation
- Quotes, Concepts, Inbox: Workflow item curation (accept/reject, complete workflow)
- Notifications: Workflow events (workflow_started, curation_pending, workflow_completed)

### zettel *(deprecated)*
- Quote/concept workflows are now in the backend (Temporal); use Curation UI (Quotes, Concepts) and minerva_agent workflow tools

## Typical Workflows

### Workflow 1: Journal Processing

```
1. User writes journal entry in Obsidian
2. Submit to Backend API
3. Backend extracts entities and relationships
4. User curates results via web interface
5. Data stored in Neo4j knowledge graph
```

### Workflow 2: Agent-Assisted Vault Management

```
1. User opens minerva-desktop
2. Connects to minerva_agent
3. Asks agent to organize inbox
4. Agent reads files, plans tasks, executes
5. User reviews results in desktop app
```

### Workflow 3: Book Quote and Concept Processing

```
1. User has book notes with quotes
2. From minerva_agent: start_quote_parsing (file_path, author, title); confirm in chat (HITL)
3. Backend QuoteParsing workflow parses file, submits to curation DB; notification appears
4. User reviews quotes in Curation UI (Quotes), accepts/rejects, completes workflow
5. Workflow writes Content, Quote, Person and relations to Neo4j
6. From minerva_agent: start_concept_extraction (content_uuid); confirm in chat
7. Backend ConceptExtraction workflow extracts concepts, submits to curation DB
8. User reviews concepts in Curation UI (Concepts), completes workflow
9. Workflow writes Concept nodes and SUPPORTS/relations to Neo4j
```

## Integration Patterns

### Backend + Agents

Backend can call agents via LangGraph SDK:
- Process journal entries with agent assistance
- Extract concepts using zettel
- Organize vault with minerva_agent

### Desktop + Agents

Desktop app connects to agents:
- Real-time chat interface
- Task tracking
- File operations
- Subagent monitoring

### Agents + Neo4j

Agents interact with knowledge graph:
- zettel stores quotes and concepts
- minerva_agent can query knowledge graph
- Backend manages graph operations

## Common Use Cases

### Daily Journaling

1. Write journal entry
2. Submit to backend
3. Review extracted entities
4. Approve relationships
5. Knowledge graph updated

### Vault Organization

1. Open minerva-desktop
2. Ask agent to organize inbox
3. Agent plans and executes
4. Review changes
5. Commit to vault

### Book Analysis

1. Prepare book notes with quotes
2. Run quote parsing
3. Extract concepts
4. Review concept proposals
5. Integrate into knowledge graph

## Getting Started

1. **Set up components** (see [Setup Guides](../setup/quick-start.md))
2. **Start services** (backend, agents, desktop)
3. **Try a workflow** (journal processing, agent chat, quote parsing)
4. **Explore features** (see component-specific usage guides)

## Next Steps

- [minerva-desktop Usage](minerva-desktop.md)
- [minerva-agent Usage](minerva-agent.md)
- [zettel Usage](zettel.md)
- [Integration Workflows](integration-workflows.md)
- [Common Use Cases](common-use-cases.md)

