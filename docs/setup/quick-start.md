# Quick Start Guide

Get Minerva up and running. This guide covers all services needed to run the **whole app**: backend API, Temporal workflows (journal, quote, concept, inbox), Curation UI, minerva_agent (chat and workflow launch), and minerva-desktop (desktop chat client).

## Prerequisites

- **Python 3.12+** and **Poetry**
- **Node.js 18+** and **npm**
- **Neo4j** (Desktop or server) — graph database
- **Temporal CLI** — for running Temporal Server (`temporal server start-dev`)
- **Ollama** — local LLM for backend extraction
- **Rust** and **Cargo** (for minerva-desktop)
- **Google API key** (for minerva_agent workflow launchers and LLM in workflows)

## What Runs Where

| Service | Purpose | Port / URL |
|--------|---------|------------|
| Neo4j | Knowledge graph | bolt://localhost:7687 |
| Temporal Server | Workflow orchestration | localhost:7233 |
| Ollama | Local LLM (backend) | http://localhost:11434 |
| Backend API | REST API, curation, pipeline | http://localhost:8000 |
| Temporal Worker | Runs journal/quote/concept/inbox workflows | (connects to Temporal) |
| Curation UI (Vue.js) | Review queue, quotes, concepts, inbox, notifications | http://localhost:5173 |
| minerva_agent (LangGraph) | Chat + workflow launcher tools (HITL) | http://127.0.0.1:2024 |
| minerva-desktop | Desktop chat client | (native window) |

## Option A: Scripted Start (Backend + Worker + Curation UI)

On **Windows** (PowerShell):

```powershell
.\start-minerva.ps1
```

On **Linux/macOS**:

```bash
./start-minerva.sh
```

This starts:

- Temporal Server  
- Ollama  
- Backend API  
- Temporal Worker  
- Curation UI (frontend)

**You must start separately:**

- **Neo4j** (before running the script, or ensure it’s running)
- **minerva_agent** (chat and workflow launch)
- **minerva-desktop** (optional; desktop chat client)

## Option B: Manual Start (Full Control)

Use this order so dependencies are up before services that need them.

### 1. Neo4j

- Open Neo4j Desktop (or start Neo4j server).
- Start the database.
- Default: `bolt://localhost:7687`. Create `backend/.env` with `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` (see [Environment Variables](environment-variables.md)).

### 2. Temporal Server

```bash
temporal server start-dev
```

Leave this running. Default: `localhost:7233`.

### 3. Ollama

```bash
ollama serve
# In another terminal, e.g.:
ollama pull hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest
```

Leave it running. Backend uses it for entity/relationship extraction and (optionally) for workflows.

### 4. Backend API

```bash
cd backend
poetry install
poetry run python -m minerva_backend.api.main
```

Runs at **http://localhost:8000**. Ensure `backend/.env` has Neo4j and Temporal settings (and optionally Ollama).

### 5. Temporal Worker

In a **new terminal**:

```bash
cd backend
poetry run python -m minerva_backend.processing.temporal_orchestrator
```

This runs the journal, quote parsing, concept extraction, and inbox classification workflows. It must be running for those workflows to execute.

### 6. Curation UI (Vue.js)

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Opens at **http://localhost:5173**. Use it for:

- **Queue** — journal entity/relationship curation  
- **Quotes** — quote parsing workflow items  
- **Concepts** — concept extraction workflow items  
- **Inbox** — inbox classification items  
- **Notifications** — workflow events  

If the API is on another host/port, set `VITE_API_BASE_URL` (e.g. `http://localhost:8000`) so the UI can call the backend.

### 7. minerva_agent (chat and workflow launch)

In a **new terminal**:

```bash
cd backend/minerva_agent
poetry install
# Create .env with GOOGLE_API_KEY and optionally OBSIDIAN_VAULT_PATH
poetry run langgraph dev
```

Runs at **http://127.0.0.1:2024**. Used by minerva-desktop for chat and for workflow launcher tools (quote parsing, concept extraction, inbox classification) with HITL confirmation.  
**Note:** zettel is deprecated; quote/concept flows use backend Temporal workflows + Curation UI (Quotes, Concepts).

### 8. minerva-desktop (desktop chat client)

In a **new terminal**:

```bash
cd minerva-desktop
npm install
# Create .env.local with NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024, NEXT_PUBLIC_AGENT_ID=minerva_agent
npm run tauri:dev
```

Connects to minerva_agent for chat and workflow launch. Requires minerva_agent to be running.

## Verify Installation

| Check | URL / Action |
|-------|----------------|
| Backend API | http://localhost:8000/api/health |
| API docs | http://localhost:8000/docs |
| Curation UI | http://localhost:5173 (Queue, Quotes, Concepts, Inbox, Notifications) |
| minerva_agent | http://127.0.0.1:2024 (e.g. LangGraph Studio) |
| minerva-desktop | App window opens when you run `npm run tauri:dev` |

## Whole app checklist

To run the **whole app**:

1. Neo4j  
2. Temporal Server  
3. Ollama  
4. Backend API  
5. Temporal Worker  
6. Curation UI  
7. minerva_agent (chat and workflow launch)  
8. minerva-desktop (desktop chat client)

Use the Curation UI for journal queue, quotes, concepts, inbox, and notifications. Use minerva_agent (via desktop or LangGraph Studio) to chat and launch quote/concept/inbox workflows with HITL confirmation.

## Next Steps

- [Complete Setup Guide](complete-setup.md) — detailed configuration and env vars  
- [Environment Variables](environment-variables.md) — all variables per component  
- [Usage Overview](../usage/overview.md) — how components work together  
- [Integration Workflows](../usage/integration-workflows.md) — multi-component flows  

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Backend won’t start | Neo4j running; `backend/.env` has correct Neo4j and Temporal settings. |
| Workflows don’t run | Temporal Server running; Temporal Worker process running (`temporal_orchestrator`). |
| Curation UI can’t reach API | Backend running on 8000; set `VITE_API_BASE_URL` if different. |
| minerva_agent won’t start | `GOOGLE_API_KEY` in `backend/minerva_agent/.env`. |
| minerva-desktop won’t build | Rust toolchain installed. |
| Desktop can’t reach agent | minerva_agent running; `NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024` in minerva-desktop `.env.local`. |

For more help, see the component-specific setup guides.
