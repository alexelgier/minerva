# System Architecture Overview

This document provides a high-level overview of all Minerva components and how they work together.

## Component Overview

Minerva consists of four main components:

1. **Backend API** - FastAPI-based REST API for journal processing, quote/concept/inbox workflows, curation, and knowledge graph management
2. **Curation UI (Vue.js)** - Web frontend for human-in-the-loop: Queue (journal entities/relations), Quotes, Concepts, Inbox, Notifications
3. **minerva-desktop** - Tauri desktop application for interacting with the LangGraph agent (chat, workflow launch with HITL)
4. **minerva_agent** - LangGraph agent (LangChain 1.x) for Obsidian vault: read-only tools + workflow-launcher tools; HITL for workflow confirmation
5. **zettel** *(deprecated)* - Quote/concept workflows migrated to backend Temporal workflows; folder kept for reference

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Minerva Ecosystem                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  minerva-desktop  │────────│  minerva_agent   │
│  (Tauri + React) │         │  (LangGraph)     │
└────────┬──────────┘         └────────┬──────────┘
         │                              │
┌────────▼──────────┐                   │
│  Curation UI      │                   │ LangGraph SDK
│  (Vue.js)         │                   │
│  Queue/Quotes/    │                   │
│  Concepts/Inbox/  │                   │
│  Notifications    │                   │
└────────┬──────────┘                   │
         │                              ▼
         │              ┌─────────────────────────────────────────────┐
         └─────────────│              Backend API (FastAPI)           │
                       │  - Journal / Quote / Concept / Inbox         │
                       │  - Curation Management + Notifications       │
                       │  - Temporal Workflows + Knowledge Graph      │
                       └──────────────────┬──────────────────────────┘
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
- Entity extraction from journal entries (8-stage Temporal pipeline)
- Quote parsing, concept extraction, inbox classification (Temporal workflows)
- Curation queue management (journal, quote, concept, inbox) and notifications
- Obsidian vault synchronization (Zettel sync)
- Temporal workflow orchestration (Journal, QuoteParsing, ConceptExtraction, InboxClassification)

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

### Curation UI (Vue.js)

**Technology**: Vue 3, Vite, Pinia

**Purpose**: Human-in-the-loop approval for all workflow outputs.

**Key Features**:
- **Queue**: Journal entity and relationship curation
- **Quotes**: Quote parsing workflow items (accept/reject, complete workflow)
- **Concepts**: Concept extraction workflow items (concepts and relations)
- **Inbox**: Inbox classification workflow items (accept/reject moves)
- **Notifications**: List, mark read, dismiss (workflow_started, curation_pending, workflow_completed)

**Documentation**: See [frontend/](../../frontend/) and backend curation API.

### minerva_agent

**Technology**: LangGraph 1.x, LangChain agents, Google Gemini, Temporal client, Python 3.12+

**Purpose**:
- Assist with Obsidian vault operations via read-only tools
- Launch Temporal workflows (quote parsing, concept extraction, inbox classification) with mandatory HITL confirmation

**Key Features**:
- Bilingual support (Spanish/English)
- Read-only tools: read_file, list_dir, glob, grep (sandboxed to vault)
- Workflow launcher tools: start_quote_parsing, start_concept_extraction, start_inbox_classification, get_workflow_status
- HumanInTheLoopMiddleware for workflow tools (user must confirm before execution)
- No direct file writes; irreversible actions are performed by Temporal workflows after curation

**Documentation**: See [backend/minerva_agent/README.md](../../backend/minerva_agent/README.md) and [minerva-agent Architecture](minerva-agent.md)

### zettel *(deprecated)*

**Status**: Quote parsing and concept extraction have been migrated to Temporal workflows in the backend (`quote_parsing_workflow.py`, `concept_extraction_workflow.py`). The Curation UI (Quotes, Concepts) and minerva_agent workflow tools use the backend. This folder is kept for reference only.

**Documentation**: See [backend/zettel/README.md](../../backend/zettel/README.md) (deprecation notice) and [zettel Architecture](zettel.md)

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

### Quote / Concept Flow (Backend Temporal)

```
User (agent or API) → Start QuoteParsing workflow → Curation UI (Quotes) → Neo4j
User → Start ConceptExtraction workflow → Curation UI (Concepts) → Neo4j
```

1. User launches quote parsing via minerva_agent (HITL) or API; workflow parses markdown, submits to curation DB
2. User reviews quotes in Curation UI (Quotes), accepts/rejects, completes workflow
3. Workflow writes Content, Quote, Person and QUOTED_IN/AUTHORED_BY to Neo4j
4. User launches concept extraction for a content UUID; workflow extracts concepts, submits to curation DB
5. User reviews concepts/relations in Curation UI (Concepts); workflow writes Concept nodes and SUPPORTS/relations to Neo4j

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
| Curation UI | Vue.js, Vite | - | - | - |
| minerva-desktop | React, Tauri | - | - | - |
| minerva_agent | - | LangGraph, Python | - | Google Gemini |
| zettel *(deprecated)* | - | (migrated to backend) | Neo4j | Google Gemini, Ollama |

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

