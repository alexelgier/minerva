# Project Minerva: AI-Powered Personal Knowledge Graph

> **Version 0.4.0** — Backend rework: quote/concept/inbox Temporal workflows, curation DB (quotes, concepts, inbox, notifications), Curation UI (Queue, Quotes, Concepts, Inbox, Notifications), minerva_agent refactor (read-only + workflow launchers with HITL), zettel deprecated.

## 1. Project Summary

**Purpose**: Minerva is a personal knowledge management system that transforms unstructured text (journal entries, book quotes) into a structured knowledge graph. It automates entity extraction, relationship discovery, and concept organization while maintaining human-in-the-loop quality control.

**Core Capabilities**:
- **Journal Processing**: Submit daily journals via REST API for automated entity and relationship extraction
- **Human Curation**: Review and correct AI-extracted data through a Vue.js curation interface
- **Knowledge Graph Storage**: Store structured data in Neo4j with semantic vector search capabilities
- **Agent Assistance**: LangGraph-based agents for Obsidian vault management and book quote processing
- **Desktop Application**: Native Tauri app for real-time agent interaction with chat, task tracking, and file management

**Target Users**: Individuals who journal, use Obsidian for note-taking, and want to build a queryable, interconnected knowledge base from their personal data.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              MINERVA SYSTEM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐       │
│  │  minerva-desktop │    │  Vue.js Frontend │    │   REST Clients   │       │
│  │  (Tauri+Next.js) │    │  (Curation UI)   │    │                  │       │
│  └────────┬─────────┘    └────────┬─────────┘    └────────┬─────────┘       │
│           │                       │                       │                  │
│           ▼                       ▼                       ▼                  │
│  ┌──────────────────┐    ┌──────────────────────────────────────────┐       │
│  │  LangGraph Agents│    │           FastAPI Backend                 │       │
│  │  ┌────────────┐  │    │  ┌──────────────────────────────────┐    │       │
│  │  │minerva_    │  │    │  │  REST API Endpoints               │    │       │
│  │  │agent       │  │    │  │  /api/journal, /api/curation,    │    │       │
│  │  └────────────┘  │    │  │  /api/pipeline, /api/health      │    │       │
│  │  ┌────────────┐  │    │  └──────────────┬───────────────────┘    │       │
│  │  │zettel      │  │    │                 │                         │       │
│  │  │(2 graphs)  │  │    │  ┌──────────────▼───────────────────┐    │       │
│  │  └────────────┘  │    │  │  Temporal.io Orchestrator         │    │       │
│  └────────┬─────────┘    │  │  (8-stage durable workflow)       │    │       │
│           │              │  └──────────────┬───────────────────┘    │       │
│           │              │                 │                         │       │
│           │              │  ┌──────────────▼───────────────────┐    │       │
│           │              │  │  Processing Layer                 │    │       │
│           │              │  │  • LLM Service (Ollama)           │    │       │
│           │              │  │  • Entity Processors              │    │       │
│           │              │  │  • Curation Manager (SQLite)      │    │       │
│           │              │  └──────────────┬───────────────────┘    │       │
│           │              └─────────────────┼────────────────────────┘       │
│           │                                │                                 │
│           ▼                                ▼                                 │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │                         Neo4j Graph Database                      │       │
│  │  Nodes: Entities, Documents, Temporal Tree, Concepts             │       │
│  │  Edges: MENTIONS, RELATED_TO, SUPPORTS, temporal links, etc.     │       │
│  │  Indexes: Vector embeddings (1024-dim) for semantic search       │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

### Backend (`backend/`)
| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.12+ |
| Web Framework | FastAPI | 0.112+ |
| Workflow Engine | Temporal.io | 1.17+ |
| Primary Database | Neo4j | 5.23+ |
| Curation Queue | SQLite (aiosqlite) | — |
| LLM Integration | Ollama | 0.6+ |
| Default LLM Model | Qwen3-4B-Instruct | — |
| Embedding Model | mxbai-embed-large | 1024-dim |
| DI Framework | dependency-injector | 4.41+ |
| Data Modeling | Pydantic | 2.x |

### Desktop Application (`minerva-desktop/`)
| Layer | Technology | Version |
|-------|------------|---------|
| Framework | Tauri | 2.9.x |
| Frontend | Next.js | 15.4+ |
| UI Library | React | 19.1+ |
| Styling | Tailwind CSS + SCSS | v4 |
| Agent SDK | @langchain/langgraph-sdk | 0.0.105+ |

### LangGraph Agent (`backend/minerva_agent/`)
| Layer | Technology | Version |
|-------|------------|---------|
| Framework | LangGraph | 1.0+ |
| Agent API | LangChain 1.x create_agent | — |
| LLM Provider | Google Gemini | 2.5 Pro/Flash |
| Workflow Client | Temporal (minerva-backend) | 1.17+ |
| Note: zettel deprecated; quote/concept workflows in backend Temporal | — | — |

### Legacy Frontend (`frontend/`)
| Layer | Technology | Version |
|-------|------------|---------|
| Framework | Vue.js | 3.5+ |
| State Management | Pinia | 3.0+ |
| UI Library | Element Plus | 2.13+ |
| Build Tool | Vite | 7.3+ |

---

## 4. Components

### 4.1 Backend API (`backend/src/minerva_backend/`)

The FastAPI backend exposes REST endpoints for journal processing, curation, and system health.

**Key Endpoints**:
- Journal: `POST /api/journal/submit`, `GET /api/curation/pending`, `POST /api/curation/entities/{journal_id}/complete`, `POST /api/curation/entities/{journal_id}/{entity_id}`, `POST /api/curation/relationships/{journal_id}/complete`, `POST /api/curation/relationships/{journal_id}/{relationship_id}`
- Quote curation: `GET /api/curation/quotes/pending`, `GET /api/curation/quotes/{workflow_id}/items`, `POST /api/curation/quotes/{workflow_id}/{quote_id}`, `POST /api/curation/quotes/{workflow_id}/complete`
- Concept curation: `GET /api/curation/concepts/pending`, `GET /api/curation/concepts/{workflow_id}/items`, `POST /api/curation/concepts/{workflow_id}/{concept_id}`, `POST /api/curation/concepts/{workflow_id}/relations/{relation_id}`, `POST /api/curation/concepts/{workflow_id}/complete`
- Inbox curation: `GET /api/curation/inbox/pending`, `GET /api/curation/inbox/{workflow_id}/items`, `POST /api/curation/inbox/{workflow_id}/{item_id}`
- Notifications: `GET /api/curation/notifications`, `POST /api/curation/notifications/{id}/read`, `POST /api/curation/notifications/{id}/dismiss`
- `GET /api/pipeline/status/{workflow_id}` — Get pipeline status
- `GET /api/health/` — Comprehensive health check

**Entry Points**:
```bash
# Start API server
poetry run python -m minerva_backend.api.main

# Start Temporal worker
poetry run python -m minerva_backend.processing.temporal_orchestrator
```

### 4.2 Processing Pipeline (Temporal.io)

An 8-stage durable workflow orchestrated by Temporal.io:

| Stage | Activity | Description |
|-------|----------|-------------|
| 1 | `SUBMITTED` | Journal entry received |
| 2 | `ENTITY_PROCESSING` | LLM extracts entities (Person, Concept, Project, Consumable, Content, Event, Place) |
| 3 | `SUBMIT_ENTITY_CURATION` | Queue entities for human review |
| 4 | `WAIT_ENTITY_CURATION` | Wait for human curation (polls every 30s, 7-day timeout) |
| 5 | `RELATION_PROCESSING` | LLM extracts relationships and feelings |
| 6 | `SUBMIT_RELATION_CURATION` | Queue relationships for human review |
| 7 | `WAIT_RELATION_CURATION` | Wait for human curation |
| 8 | `DB_WRITE` → `COMPLETED` | Persist to Neo4j knowledge graph |

**Entity Extraction Order**: Person → Concept → Project → Consumable → Content → Event → Place

**Relationship Extraction**: Generic relations, concept relations, emotion feelings, concept feelings

**Additional Temporal Workflows** (quote/concept/inbox):
- **QuoteParsingWorkflow**: Parse markdown quotes → submit to curation DB → wait for approval → write Content, Quote, Person, QUOTED_IN, AUTHORED_BY to Neo4j. Emits notifications.
- **ConceptExtractionWorkflow**: Load content/quotes from Neo4j → LLM extract concepts/relations → submit to curation DB → wait for approval → write Concept, SUPPORTS, relations to Neo4j. Emits notifications.
- **InboxClassificationWorkflow**: Scan inbox → LLM suggest target folder per note → submit to curation DB → wait for approval → execute file moves. Emits notifications.

### 4.3 LLM Service (`processing/llm_service.py`)

- **Provider**: Ollama (local inference)
- **Default Model**: `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest`
- **Embedding Model**: `mxbai-embed-large:latest` (1024 dimensions)
- **Features**: Caching (diskcache), retry logic (3 attempts), streaming, JSON schema validation

### 4.4 Curation Manager (`processing/curation_manager.py`)

SQLite-based queue for human-in-the-loop validation.

**Database Tables**:
1. `journal_curation` — Journal entries and overall status
2. `entity_curation_items` — Entities awaiting curation
3. `relationship_curation_items` — Relationships awaiting curation
4. `span_curation_items` — Text spans linked to entities
5. `relationship_context_items` — Context for relationships

**Status Flow**: `PENDING_ENTITIES` → `ENTITIES_DONE` → `PENDING_RELATIONS` → `COMPLETED`

### 4.5 minerva-desktop (`minerva-desktop/`)

Native desktop application for agent interaction built with Tauri + Next.js.

**Features**:
- Real-time streaming chat with LangGraph agents
- Thread management (create, switch, search history)
- Task tracking (todos synced from agent state)
- File viewer with syntax highlighting
- Sub-agent monitoring
- Tool call visualization
- System tray with global shortcut (Ctrl+Alt+M)

**Connection**: Connects to LangGraph deployment at `http://127.0.0.1:2024` via LangGraph SDK

### 4.6 minerva_agent (`backend/minerva_agent/`)

LangGraph agent (LangChain 1.x) for Obsidian vault assistance. Read-only vault tools + workflow launcher tools with mandatory HITL confirmation. Irreversible actions are performed by backend Temporal workflows after curation in the Curation UI.

**Capabilities**:
- **Read-only tools** (sandboxed to OBSIDIAN_VAULT_PATH): read_file, list_dir, glob, grep
- **Workflow launcher tools** (HITL required): start_quote_parsing, start_concept_extraction, start_inbox_classification, get_workflow_status
- HumanInTheLoopMiddleware: user must confirm in chat before a workflow is started
- No direct file writes; quote/concept/inbox steps approved in Curation UI (Quotes, Concepts, Inbox)

**LLM**: Google Gemini (temperature: 0)

### 4.7 zettel (`backend/zettel/`) — DEPRECATED

Quote parsing and concept extraction have been migrated to Temporal workflows in the backend (`quote_parsing_workflow.py`, `concept_extraction_workflow.py`). Use the Curation UI (Quotes, Concepts) and minerva_agent workflow launcher tools instead. The zettel folder is kept for reference only.

### 4.8 Curation UI — Vue.js Frontend (`frontend/`)

Human-in-the-loop curation interface for journal entities/relations and for quote, concept, and inbox workflows.

**Purpose**: Sole surface for approving workflow steps (journal pipeline, quote parsing, concept extraction, inbox classification)

**Routes**:
- `/curation-queue` — Journal pending curation tasks (Queue)
- `/curation/:journalId/:entityId` — Detailed entity/relationship editing
- `/quotes` — Quote curation (workflow list, items, accept/reject, complete)
- `/concepts` — Concept curation (workflow list, concept/relation items, accept/reject, complete)
- `/inbox` — Inbox classification curation (workflow list, items, accept/reject)
- `/notifications` — Notifications (workflow_started, curation_pending, workflow_completed); mark read, dismiss

**Features**: Nav (Queue, Quotes, Concepts, Inbox, Notifications with unread badge), split-panel view for journal, quick accept/reject, span highlighting

---

## 5. Data Model

### 5.1 Entity Types (Nodes)

| Entity | Description | Key Fields |
|--------|-------------|------------|
| **Person** | Individual persons | name, occupation, birth_date |
| **Emotion** | Distinct emotion types | name (from 50 defined types) |
| **FeelingEmotion** | Person experiences emotion (temporal) | timestamp, intensity (1-10), duration |
| **FeelingConcept** | Person feels about concept (temporal) | timestamp, intensity, duration |
| **Event** | Notable occurrences | category, date, duration, location |
| **Project** | Multi-step initiatives | status, start_date, target_completion, progress |
| **Concept** | Atomic Zettelkasten ideas | title, concept, analysis, source |
| **Content** | Resources (books, articles, videos) | title, category, url, author, status |
| **Consumable** | Consumable items | category (food, drink, medicine) |
| **Place** | Physical locations | address, category |

### 5.2 Document Types (Nodes)

| Document | Description | Key Fields |
|----------|-------------|------------|
| **JournalEntry** | Daily journal text | content, entry_date |
| **Quote** | Extracted quote from content | text, section, page |
| **Span** | Text span within document | start_offset, end_offset, text |
| **Chunk** | Text chunk for processing | text, embedding |

### 5.3 Temporal Nodes

| Node | Description |
|------|-------------|
| **Year** | Year node (e.g., 2025) |
| **Month** | Month node linked to Year |
| **Day** | Day node linked to Month |

### 5.4 Relationship Types (Edges)

| Edge | From → To | Description |
|------|-----------|-------------|
| **MENTIONS** | Chunk → Entity | Entity mentioned in text chunk |
| **RELATED_TO** | Entity → Entity | Generic relationship with summary |
| **HAS_RELATION** | Entity → Relation | Links to reified Relation node |
| **OCCURRED_ON** | Entity → Day | Temporal link to day node |
| **QUOTED_IN** | Quote → Content | Quote belongs to content |
| **SUPPORTS** | Quote → Concept | Quote supports concept (with confidence) |
| **AUTHORED_BY** | Person → Content | Person authored content |
| **IS_EMOTION** | FeelingEmotion → Emotion | Feeling is of emotion type |
| **FEELS_ABOUT** | FeelingConcept → Concept/Person | Feeling target |
| **HAS_MONTH** | Year → Month | Temporal hierarchy |
| **HAS_DAY** | Month → Day | Temporal hierarchy |

### 5.5 Concept Relation Types

| Type | Description |
|------|-------------|
| GENERALIZES | Concept generalizes another |
| SPECIFIC_OF | Concept is specific case of another |
| PART_OF | Concept is part of another |
| HAS_PART | Concept contains another |
| SUPPORTS | Concept supports another |
| SUPPORTED_BY | Concept is supported by another |
| OPPOSES | Concept opposes another |
| SIMILAR_TO | Concept is similar to another |
| RELATES_TO | Generic relation |

---

## 6. Repository Layer (`graph/repositories/`)

All entity repositories extend `BaseRepository[T]` with common CRUD operations:

**Common Operations** (inherited):
- `create(node)` — Create with embedding generation
- `find_by_uuid(uuid)` — Find by UUID
- `list_all(limit, offset)` — Paginated listing
- `update(uuid, updates)` — Update with embedding regeneration
- `delete(uuid)` — Delete node and relationships
- `vector_search(query_text, limit, threshold)` — Semantic search
- `find_similar(node, limit)` — Find similar nodes

**Specialized Repositories** (14 total):
- PersonRepository, EventRepository, ConceptRepository, ProjectRepository
- EmotionRepository, ContentRepository, ConsumableRepository, PlaceRepository
- FeelingEmotionRepository, FeelingConceptRepository, JournalEntryRepository
- QuoteRepository, RelationRepository, TemporalRepository

---

## 7. Project Structure

```
Minerva/
├── backend/                      # Backend API and agents
│   ├── src/minerva_backend/      # Main backend source
│   │   ├── api/                  # FastAPI endpoints
│   │   │   ├── main.py           # Application entry point
│   │   │   └── routers/          # Route handlers
│   │   ├── graph/                # Neo4j layer
│   │   │   ├── db.py             # Database connection
│   │   │   ├── models/           # Pydantic models
│   │   │   ├── repositories/     # Data access layer
│   │   │   └── services/         # Business logic
│   │   └── processing/           # Processing pipeline
│   │       ├── temporal_orchestrator.py   # Temporal workflow
│   │       ├── curation_manager.py        # SQLite curation queue
│   │       ├── llm_service.py             # Ollama integration
│   │       └── extraction/                # Entity processors
│   ├── minerva_agent/            # Obsidian vault agent
│   │   ├── langgraph.json        # LangGraph config
│   │   └── src/minerva_agent/    # Agent source
│   ├── zettel/                   # Quote/concept agent
│   │   ├── langgraph.json        # LangGraph config (2 graphs)
│   │   └── src/zettel_agent/     # Agent source
│   ├── tests/                    # Test suite (346 tests, 100% coverage)
│   └── docs/                     # Backend documentation
├── minerva-desktop/              # Desktop application
│   ├── src/                      # Next.js source
│   │   ├── app/                  # App router pages
│   │   └── components/           # React components
│   └── src-tauri/                # Tauri Rust backend
├── frontend/                     # Legacy Vue.js curation UI
│   ├── src/
│   │   ├── components/           # Vue components
│   │   ├── views/                # Page views
│   │   └── stores/               # Pinia stores
├── minerva-models/               # Shared Pydantic models
│   └── src/minerva_models/       # Entity definitions
├── docker/
│   └── docker_compose.yml        # Docker services
└── docs/                         # Project documentation
```

---

## 8. Configuration

### Environment Variables

**Backend** (`backend/.env`):
```bash
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Temporal
TEMPORAL_HOST=localhost:7233

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest
OLLAMA_EMBEDDING_MODEL=mxbai-embed-large:latest

# Obsidian
OBSIDIAN_VAULT_PATH=D:\yo
```

**Agents** (`backend/minerva_agent/.env`, `backend/zettel/.env`):
```bash
GOOGLE_API_KEY=your-gemini-api-key
OBSIDIAN_VAULT_PATH=D:\yo

# Optional: LangSmith tracing
LANGSMITH_PROJECT=minerva
LANGSMITH_API_KEY=your-langsmith-key
```

**Desktop** (`minerva-desktop/.env`):
```bash
NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024
NEXT_PUBLIC_AGENT_ID=deepagent
NEXT_PUBLIC_LANGSMITH_API_KEY=your-langsmith-key
```

---

## 9. Running the System

### Prerequisites
- Python 3.12+ with Poetry
- Node.js 18+ with npm
- Rust and Cargo (for desktop app)
- Neo4j (local or Docker)
- Ollama (for local LLM)
- Google API key (for agents)

### Quick Start

**1. Infrastructure** (Docker):
```bash
cd docker
docker-compose up -d neo4j temporal temporal-ui ollama
```

**2. Backend**:
```bash
cd backend
poetry install
poetry run python -m minerva_backend.api.main &
poetry run python -m minerva_backend.processing.temporal_orchestrator &
```

**3. Agent** (choose one):
```bash
# minerva_agent
cd backend/minerva_agent
poetry install
poetry run langgraph dev

# zettel
cd backend/zettel
poetry install
poetry run langgraph dev
```

**4. Desktop App**:
```bash
cd minerva-desktop
npm install
npm run tauri:dev
```

**5. Curation UI** (optional):
```bash
cd frontend
npm install
npm run dev
```

---

## 10. Current Status

### Implemented ✅
- Complete 8-stage Temporal.io processing pipeline
- LLM-based entity extraction (7 entity types) and relationship extraction
- Human-in-the-loop curation with accept/reject workflow
- Neo4j graph database with 14 repositories and vector search
- minerva-desktop: Native desktop app with real-time agent chat
- minerva_agent: Deep agent for Obsidian vault operations
- zettel: Two-graph system for quote parsing and concept extraction
- Vue.js curation interface (functional, legacy)
- 346 tests with 100% code coverage

### Partially Implemented 🚧
- Some pipeline status endpoints return placeholder data
- Bulk accept/reject functionality incomplete
- Workflow cancellation not fully implemented
- Obsidian router exists but has no endpoints

### Planned 📋
- Enhanced graph visualization
- Advanced concept linking and relationship discovery
- Graph analytics (centrality, community detection)
- Semantic search across journal entries
- Broader data source ingestion

---

## 11. Key Design Patterns

1. **Repository Pattern**: Clean separation of data access logic from business logic
2. **Durable Workflows (Temporal.io)**: Long-running, stateful workflows that survive failures
3. **Human-in-the-Loop**: Mandatory human review steps for data quality
4. **Dependency Injection**: Testable, modular service architecture
5. **Async Everywhere**: Non-blocking I/O for database and API operations
6. **Vector Embeddings**: Semantic search capability across all entities
7. **Reified Relationships**: Some relationships stored as nodes for rich metadata

---

## 12. Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| Quick Start | `docs/setup/quick-start.md` | Get running in 10 minutes |
| Complete Setup | `docs/setup/complete-setup.md` | Full installation guide |
| Backend Architecture | `backend/docs/architecture/overview.md` | API design details |
| Desktop Architecture | `docs/architecture/minerva-desktop.md` | Desktop app structure |
| Agent Architecture | `docs/architecture/minerva-agent.md` | Agent system design |
| Zettel Architecture | `docs/architecture/zettel.md` | Concept extraction system |
| Zettel Module Docs | `backend/zettel/docs/` | Comprehensive API, workflows |
| Database Schema | `backend/docs/architecture/database-schema.md` | Neo4j schema |

---

*Last verified: February 2026 against codebase version 0.2.0*
