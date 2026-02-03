# Complete Setup Guide

Comprehensive setup instructions for all Minerva components. For a shorter path, see [Quick Start](quick-start.md).

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Neo4j Configuration](#neo4j-configuration)
3. [Temporal Server](#temporal-server)
4. [Ollama](#ollama)
5. [Backend Setup](#backend-setup)
6. [Temporal Worker](#temporal-worker)
7. [Curation UI (Vue.js)](#curation-ui-vuejs)
8. [minerva_agent](#minerva_agent)
9. [minerva-desktop](#minerva-desktop)
10. [Environment Variables](#environment-variables)
11. [Verification](#verification)
12. [Common Issues](#common-issues)

## Prerequisites

### Required Software

- **Python 3.12+**: [Download](https://www.python.org/downloads/)
- **Poetry**: [Installation Guide](https://python-poetry.org/docs/#installation)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **Neo4j**: [Neo4j Desktop](https://neo4j.com/download/) or server — graph database
- **Temporal CLI**: For running Temporal Server (`temporal server start-dev`). [Install](https://docs.temporal.io/cli)
- **Ollama**: [Installation](https://ollama.ai/) — local LLM for backend extraction
- **Rust** and **Cargo**: [Installation](https://www.rust-lang.org/tools/install) — for minerva-desktop

### Required Accounts

- **Google API Key**: [Get API Key](https://makersuite.google.com/app/apikey) — for minerva_agent (chat and workflow launchers) and for LLM in quote/concept/inbox workflows

## Neo4j Configuration

### Using Neo4j Desktop

1. Install Neo4j Desktop
2. Create a new database
3. Set password
4. Start the database
5. Note connection details:
   - URI: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: (your password)

### Using Neo4j Server

1. Install Neo4j server
2. Configure in `neo4j.conf`
3. Start server
4. Access browser at `http://localhost:7474`

### Vector Indexes

The backend creates vector indexes as needed for embeddings. No manual Neo4j index setup is required for the backend. To verify: `SHOW INDEXES` in Cypher.

## Temporal Server

Temporal is required for journal, quote parsing, concept extraction, and inbox classification workflows.

1. **Install Temporal CLI** (see [Temporal docs](https://docs.temporal.io/cli))

2. **Start Temporal Server** (development mode):
```bash
temporal server start-dev
```

Leave it running. Default: `localhost:7233`. The Backend API and Temporal Worker connect to this.

## Ollama

The backend uses Ollama for entity/relationship extraction (journal pipeline) and optionally for other LLM calls.

1. **Install Ollama** from [ollama.ai](https://ollama.ai/)

2. **Start Ollama**:
```bash
ollama serve
```

3. **Pull the default LLM model** (used by backend):
```bash
ollama pull hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest
```

4. **Pull the embedding model** (for vector search):
```bash
ollama pull mxbai-embed-large
```

See [Environment Variables](environment-variables.md) for backend and other component variables.

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
poetry install
```

### 2. Configure Environment

Create `.env` file in `backend/`. The backend reads all settings with the `MINERVA_` prefix (pydantic-settings):

```env
# Neo4j (required)
MINERVA_NEO4J_URI=bolt://localhost:7687
MINERVA_NEO4J_USER=neo4j
MINERVA_NEO4J_PASSWORD=your-password

# Temporal (required for workflows)
MINERVA_TEMPORAL_URI=localhost:7233

# Curation DB (optional; default: curation.db in backend dir)
# MINERVA_CURATION_DB_PATH=curation.db

# Obsidian vault (optional; used by workflows that read/write vault paths)
# MINERVA_OBSIDIAN_VAULT_PATH=D:\path\to\vault
```

Ollama URL and model are currently fixed in code (defaults: `http://localhost:11434`, model `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest`). See [Environment Variables](environment-variables.md) for the full list and other components.

### 3. Initialize Database

**Neo4j**: Ensure Neo4j is running. The backend initializes emotion types on first use. You can run:

```bash
cd backend
poetry run python -c "from minerva_backend.containers import Container; import asyncio; asyncio.run(Container().db_connection().initialize())"
```

**Curation DB (SQLite)**: Created automatically when the Backend API or Temporal Worker starts (via `curation_manager.initialize()`). No separate step needed.

### 4. Start Backend API

```bash
cd backend
poetry run python -m minerva_backend.api.main
```

Backend runs on `http://localhost:8000`

### 5. Verify Backend

```bash
curl http://localhost:8000/api/health
```

## Temporal Worker

The Temporal Worker runs the journal, quote parsing, concept extraction, and inbox classification workflows. It must be running for those workflows to execute.

1. **In a separate terminal** (Backend API can stay running in another):
```bash
cd backend
poetry run python -m minerva_backend.processing.temporal_orchestrator
```

2. Leave it running. It connects to Temporal Server (`TEMPORAL_URI`) and to the same curation DB and Neo4j as the Backend API (use same `backend/.env`).

## Curation UI (Vue.js)

The Curation UI is the human-in-the-loop interface for the journal queue, quote curation, concept curation, inbox classification, and notifications.

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API URL (optional)

If the Backend API is not at `http://localhost:8000`, create `frontend/.env` (or set in shell):

```env
VITE_API_BASE_URL=http://localhost:8000
```

The Curation UI calls `/api/curation/*` endpoints; if the frontend is served from a different origin, set this so requests go to the correct backend.

### 3. Start Development Server

```bash
cd frontend
npm run dev
```

Opens at **http://localhost:5173**. Use the nav: **Queue** (journal), **Quotes**, **Concepts**, **Inbox**, **Notifications**.

## minerva_agent

minerva_agent provides chat and workflow launcher tools (quote parsing, concept extraction, inbox classification) with mandatory HITL confirmation. It uses read-only vault tools and launches backend Temporal workflows (no direct file writes).

### 1. Navigate to Directory

```bash
cd backend/minerva_agent
```

### 2. Install Dependencies

```bash
poetry install
```

### 3. Create `.env` File

```env
GOOGLE_API_KEY=your-google-api-key
# Optional: override default vault path
OBSIDIAN_VAULT_PATH=D:\your\vault\path
```

### 4. Start Agent Server

```bash
poetry run langgraph dev
```

Server runs on **http://127.0.0.1:2024**. minerva-desktop connects here for chat and workflow launch.

### zettel *(deprecated)*

Quote parsing and concept extraction have been migrated to backend Temporal workflows. Use the Curation UI (Quotes, Concepts) and minerva_agent workflow launcher tools instead. The `backend/zettel` folder is kept for reference only. See [Quick Start](quick-start.md) and [Usage (Zettel)](../usage/zettel.md).

## minerva-desktop

Desktop chat client that connects to minerva_agent for chat and workflow launch (HITL).

### 1. Install Dependencies

```bash
cd minerva-desktop
npm install
```

### 2. Install Tauri Prerequisites

**Windows**:
- Microsoft Visual C++ Build Tools
- WebView2 (usually pre-installed)

**macOS**:
```bash
xcode-select --install
```

**Linux**:
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

### 3. Configure Environment

Create `.env.local` in `minerva-desktop/`:

```env
# LangGraph server (minerva_agent)
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
NEXT_PUBLIC_AGENT_ID="minerva_agent"

# LangSmith API Key (optional for local)
# NEXT_PUBLIC_LANGSMITH_API_KEY="your-langsmith-key"
```

### 4. Development Mode

```bash
# Full Tauri app (desktop window, tray, etc.)
npm run tauri:dev

# Next.js only (faster iteration, no native features)
npm run dev
```

### 5. Build Production App

```bash
npm run tauri:build
```

Output in `src-tauri/target/release/` (or equivalent for your OS).

## Environment Variables

See [Environment Variables Reference](environment-variables.md) for the complete list for Backend, minerva_agent, Curation UI (frontend), and minerva-desktop.

## Verification

### Full Stack Checklist

| Component        | How to verify |
|------------------|----------------|
| Neo4j            | Browser: `http://localhost:7474` or cypher-shell |
| Temporal Server  | Running (e.g. `temporal server start-dev` in a terminal) |
| Ollama           | `curl http://localhost:11434/api/tags` or `ollama list` |
| Backend API      | `curl http://localhost:8000/api/health` |
| Temporal Worker  | Process running; no separate HTTP endpoint |
| Curation UI      | Open `http://localhost:5173` — Queue, Quotes, Concepts, Inbox, Notifications |
| minerva_agent    | `curl http://127.0.0.1:2024/ok` or LangGraph Studio at `http://127.0.0.1:2024` |
| minerva-desktop  | Run `npm run tauri:dev` — app window opens and can connect to agent |

### Backend

```bash
curl http://localhost:8000/api/health
# Expect healthy status for database, curation, ollama, temporal
```

### Curation UI

- Open http://localhost:5173
- Navigate to Queue, Quotes, Concepts, Inbox, Notifications (header links)
- If you see "Loading..." or errors, check Backend API is running and `VITE_API_BASE_URL` if needed

### minerva_agent

```bash
curl http://127.0.0.1:2024/ok
# Or open LangGraph Studio: http://127.0.0.1:2024
```

### minerva-desktop

- Launch with `npm run tauri:dev`
- Check console for connection status
- Send a message to verify agent connection

### Neo4j

```bash
# Using cypher-shell (if installed)
cypher-shell -u neo4j -p your-password
# Run: MATCH (n) RETURN count(n);
```

## Common Issues

### Backend Ignores .env

- Backend reads settings with the **`MINERVA_` prefix** (e.g. `MINERVA_NEO4J_URI`, not `NEO4J_URI`). Use the variable names shown in [Backend Setup](#backend-setup) and [Environment Variables](environment-variables.md).

### Port Conflicts

- **Backend**: Change port in uvicorn (e.g. `--port 8001`) and set `VITE_API_BASE_URL` in frontend
- **minerva_agent**: LangGraph dev server port is configured in langgraph.json
- **minerva-desktop**: `NEXT_PUBLIC_DEPLOYMENT_URL` must match the agent server URL/port

### Neo4j Connection

- Verify Neo4j is running
- Check `MINERVA_NEO4J_URI`, `MINERVA_NEO4J_USER`, `MINERVA_NEO4J_PASSWORD` in `backend/.env`
- Test with Neo4j Browser or cypher-shell

### Temporal / Workflows Not Running

- Ensure **Temporal Server** is running (`temporal server start-dev`)
- Ensure **Temporal Worker** process is running (`poetry run python -m minerva_backend.processing.temporal_orchestrator` from `backend/`)
- Check `MINERVA_TEMPORAL_URI` in `backend/.env` (default `localhost:7233`)

### Curation UI Can’t Reach API

- Backend API must be running on the URL the frontend uses
- If not same origin, set `VITE_API_BASE_URL` (e.g. `http://localhost:8000`) in `frontend/.env`

### minerva_agent Won’t Start

- `GOOGLE_API_KEY` must be set in `backend/minerva_agent/.env`
- Run from `backend/minerva_agent` with `poetry run langgraph dev`

### minerva-desktop Can’t Reach Agent

- minerva_agent must be running at the URL in `NEXT_PUBLIC_DEPLOYMENT_URL` (default `http://127.0.0.1:2024`)
- `NEXT_PUBLIC_AGENT_ID` must match the agent ID in minerva_agent’s langgraph.json (e.g. `minerva_agent`)

### Build Issues (minerva-desktop)

- Install Rust: `rustc --version`
- Ensure Tauri prerequisites are installed for your OS
- See [minerva-desktop setup](minerva-desktop-setup.md) for detailed desktop setup

## Next Steps

- [Quick Start](quick-start.md) — minimal steps to run the whole app
- [Environment Variables](environment-variables.md) — full variable reference
- [Component-Specific Setup](minerva-desktop-setup.md) — desktop and agent details
- [Usage Overview](../usage/overview.md) — how components work together
- [Architecture](../architecture/components.md) — system overview
