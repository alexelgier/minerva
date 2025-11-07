# System Architecture Overview

This document provides a high-level overview of all Minerva components and how they work together.

## Component Overview

Minerva consists of four main components:

1. **Backend API** - FastAPI-based REST API for journal processing and knowledge graph management
2. **minerva-desktop** - Tauri desktop application for interacting with LangGraph agents
3. **minerva_agent** - LangGraph deep agent for Obsidian vault assistance
4. **zettel** - LangGraph agent for processing book quotes and extracting concepts

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Minerva Ecosystem                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  minerva-desktop  │────────│  LangGraph Agents   │
│  (Tauri + Next.js)│         │  (minerva_agent,  │
│                   │         │   zettel)         │
└────────┬──────────┘         └────────┬──────────┘
         │                              │
         │ HTTP/WebSocket               │ LangGraph SDK
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Backend API (FastAPI)                          │
│  - Journal Processing                                       │
│  - Curation Management                                      │
│  - Knowledge Graph Operations                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   │ Neo4j Driver
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│              Neo4j Knowledge Graph                          │
│  - Entities (Person, Concept, Event, etc.)                  │
│  - Relationships                                            │
│  - Vector Embeddings                                        │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### Backend API

**Technology**: FastAPI, Python 3.12+, Temporal.io, Neo4j

**Purpose**: 
- Process journal entries through multi-stage pipeline
- Manage human-in-the-loop curation workflows
- Provide REST API for frontend and external integrations
- Store and query knowledge graph data

**Key Features**:
- Entity extraction from journal entries
- Relationship discovery
- Curation queue management
- Obsidian vault synchronization
- Temporal workflow orchestration

**Documentation**: See [backend/README.md](../../backend/README.md) and [backend/docs/](../../backend/docs/)

### minerva-desktop

**Technology**: Tauri 2, Next.js 15, React 19, TypeScript, Tailwind CSS

**Purpose**:
- Native desktop UI for LangGraph agents
- Real-time chat interface
- Task and file management
- Subagent monitoring

**Key Features**:
- Chat interface with streaming responses
- Thread history management
- Task tracking sidebar
- File viewer
- Subagent activity panel
- System tray integration

**Documentation**: See [minerva-desktop/README.md](../../minerva-desktop/README.md)

### minerva_agent

**Technology**: LangGraph, deepagents, Google Gemini, Python 3.12+

**Purpose**:
- Assist with Obsidian vault operations
- File system operations (read, write, edit)
- Search and discovery
- Task planning and execution
- Subagent delegation

**Key Features**:
- Bilingual support (Spanish/English)
- Filesystem backend for vault access
- Task planning capabilities
- Subagent system for context isolation
- Pattern matching and grep search

**Documentation**: See [backend/minerva_agent/README.md](../../backend/minerva_agent/README.md)

### zettel

**Technology**: LangGraph, Neo4j, Google Gemini, Ollama, Python 3.12+

**Purpose**:
- Parse quotes from book markdown files
- Extract atomic concepts (Zettels) from quotes
- Attribute quotes to existing concepts
- Manage concept-quote relationships

**Key Features**:
- Two-graph system (quote parsing, concept extraction)
- Vector similarity search
- LLM-based concept analysis
- Batch quote processing
- Neo4j integration

**Documentation**: See [backend/zettel/README.md](../../backend/zettel/README.md)

## Data Flow

### Journal Processing Flow

```
User → Backend API → Temporal Workflow → LLM Extraction → Curation Queue → Neo4j
```

1. User submits journal entry via API
2. Backend creates Temporal workflow
3. LLM extracts entities and relationships
4. Results queued for human curation
5. Curated data stored in Neo4j

### Agent Interaction Flow

```
User → minerva-desktop → LangGraph Server → Agent → Obsidian Vault / Neo4j
```

1. User interacts with minerva-desktop
2. Desktop app connects to LangGraph server
3. Agent processes request using tools
4. Results returned to desktop app
5. User sees updates in real-time

### Quote Processing Flow

```
Book Markdown → quote_parse_graph → Neo4j (Quotes) → concept_extraction_graph → Neo4j (Concepts)
```

1. Parse quotes from markdown file
2. Store quotes in Neo4j with embeddings
3. Extract concepts using vector search
4. Attribute quotes to concepts
5. Store concepts and relationships

## Integration Points

### Backend ↔ Neo4j
- Direct Neo4j driver connection
- Repository pattern for data access
- Vector search for semantic queries

### minerva-desktop ↔ LangGraph Agents
- LangGraph SDK for agent communication
- WebSocket streaming for real-time updates
- REST API for thread management

### Agents ↔ Obsidian Vault
- Filesystem backend for direct file access
- Path sandboxing for security
- Windows path normalization

### Agents ↔ Neo4j
- Direct Neo4j driver connection
- Vector index queries
- Graph relationship management

## Technology Stack Summary

| Component | Frontend | Backend | Database | AI/ML |
|-----------|----------|---------|----------|-------|
| Backend API | - | FastAPI, Python | Neo4j, SQLite | Ollama (local LLM) |
| minerva-desktop | Next.js, React, Tauri | - | - | - |
| minerva_agent | - | LangGraph, Python | - | Google Gemini |
| zettel | - | LangGraph, Python | Neo4j | Google Gemini, Ollama |

## Communication Protocols

- **REST API**: Backend API endpoints (HTTP/JSON)
- **WebSocket**: Real-time agent streaming (LangGraph SDK)
- **Neo4j Bolt**: Database protocol for graph operations
- **LangGraph API**: Agent server communication

## Security Considerations

- **Local Processing**: LLM inference runs locally (Ollama) or via API keys
- **Path Sandboxing**: Agent filesystem access is sandboxed
- **Environment Variables**: Sensitive keys stored in `.env` files
- **CORS**: Backend API configured for specific origins

## Deployment

- **Backend API**: Runs as Python service (Uvicorn)
- **minerva-desktop**: Native desktop application (Tauri)
- **Agents**: LangGraph server instances (local or deployed)
- **Neo4j**: Database server (local or remote)

## Related Documentation

- [minerva-desktop Architecture](minerva-desktop.md)
- [minerva-agent Architecture](minerva-agent.md)
- [zettel Architecture](zettel.md)
- [Backend Architecture](../../backend/docs/architecture/overview.md)
- [Setup Guides](../setup/quick-start.md)

