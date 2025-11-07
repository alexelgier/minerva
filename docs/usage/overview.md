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
- Obsidian vault assistance
- File operations
- Search and discovery
- Task planning

### zettel
- Quote processing
- Concept extraction
- Knowledge organization

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

### Workflow 3: Book Quote Processing

```
1. User has book notes with quotes
2. Run zettel quote_parse_graph
3. Quotes stored in Neo4j
4. Run concept_extraction_graph
5. Concepts extracted and organized
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

