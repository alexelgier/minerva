# Minerva

A personal knowledge management system that transforms unstructured text (journal entries, book notes) into a structured knowledge graph using AI-powered entity extraction, relationship discovery, and concept organization.

> **Version 0.4.0**: Backend rework with Temporal quote/concept/inbox workflows, Curation UI (Queue, Quotes, Concepts, Inbox, Notifications), minerva_agent refactor (read-only + workflow launchers with HITL), and zettel deprecated in favor of backend workflows.

## Overview

Minerva helps you build a "second brain" by:
- **Processing Journal Entries**: Extract entities and relationships from daily journals (Temporal pipeline + Curation UI)
- **Managing Obsidian Vaults**: Read-only vault access and workflow launches (quote parsing, concept extraction, inbox classification) with human approval in the Curation UI
- **Extracting Concepts**: Process book quotes and extract atomic concepts via backend Temporal workflows; review and approve in Curation UI (Quotes, Concepts)
- **Building Knowledge Graphs**: Store and query interconnected knowledge in Neo4j

## Components

### Backend API
FastAPI-based REST API for journal processing, quote/concept/inbox Temporal workflows, curation (journal, quotes, concepts, inbox, notifications), and knowledge graph management.

**Location**: `backend/`  
**Documentation**: [Backend README](backend/README.md) | [Backend Docs](backend/docs/)

### Curation UI (Vue.js)
Web frontend for human-in-the-loop approval: Queue (journal entities/relations), Quotes, Concepts, Inbox, and Notifications. Sole surface for approving workflow steps.

**Location**: `frontend/`  
**Documentation**: [Architecture](docs/architecture/components.md) | [Usage Overview](docs/usage/overview.md)

### minerva-desktop
Native desktop application (Tauri + React) for interacting with the LangGraph agent (chat, workflow launch with HITL confirmation).

**Location**: `minerva-desktop/`  
**Documentation**: [Desktop README](minerva-desktop/README.md) | [Architecture](docs/architecture/minerva-desktop.md)

### minerva_agent
LangGraph agent (LangChain 1.x) for Obsidian vault: read-only tools (read_file, list_dir, glob, grep) and workflow launcher tools (quote parsing, concept extraction, inbox classification) with mandatory HITL confirmation. Irreversible actions are performed by backend Temporal workflows after curation in the Curation UI.

**Location**: `backend/minerva_agent/`  
**Documentation**: [Agent README](backend/minerva_agent/README.md) | [Architecture](docs/architecture/minerva-agent.md)

### zettel *(deprecated)*
Quote parsing and concept extraction have been migrated to backend Temporal workflows. Use Curation UI (Quotes, Concepts) and minerva_agent workflow launcher tools instead. Folder kept for reference.

**Location**: `backend/zettel/`  
**Documentation**: [Module README](backend/zettel/README.md) (deprecation notice) | [Architecture](docs/architecture/zettel.md) | [Usage](docs/usage/zettel.md)

## Quick Start

### Prerequisites

- Python 3.12+ and Poetry
- Node.js 18+ and npm
- Neo4j Desktop or server
- Rust and Cargo (for desktop app)
- Google API key (for agents)

### Installation

1. **Backend**:
```bash
cd backend
poetry install
poetry run python -m minerva_backend.api.main
```

2. **Temporal worker** (for journal, quote, concept, inbox workflows):
```bash
cd backend
poetry run python -m minerva_backend.processing.temporal_orchestrator
```

3. **minerva_agent** (for chat and workflow launch from desktop):
```bash
cd backend/minerva_agent
poetry install
poetry run langgraph dev
```

4. **Curation UI** (optional; for reviewing quotes/concepts/inbox and notifications):
```bash
cd frontend
npm install
npm run dev
```

5. **Desktop App**:
```bash
cd minerva-desktop
npm install
npm run tauri:dev
```

See [Quick Start Guide](docs/setup/quick-start.md) for detailed instructions.

## Documentation

### Getting Started
- [Quick Start Guide](docs/setup/quick-start.md) - Get up and running in 10 minutes
- [Complete Setup Guide](docs/setup/complete-setup.md) - Comprehensive setup instructions
- [Environment Variables](docs/setup/environment-variables.md) - All configuration options

### Architecture
- [System Overview](docs/architecture/components.md) - How all components work together
- [Backend Architecture](backend/docs/architecture/overview.md) - Backend API design
- [Desktop Architecture](docs/architecture/minerva-desktop.md) - Desktop app structure
- [Agent Architecture](docs/architecture/minerva-agent.md) - Agent system design
- [Zettel Architecture](docs/architecture/zettel.md) - Concept extraction system

### Usage
- [Usage Overview](docs/usage/overview.md) - How components work together
- [Desktop Usage](docs/usage/minerva-desktop.md) - Using the desktop app
- [Agent Usage](docs/usage/minerva-agent.md) - Working with agents
- [Zettel Usage](docs/usage/zettel.md) - Processing quotes and concepts (via Curation UI + backend; zettel deprecated)
- [Integration Workflows](docs/usage/integration-workflows.md) - Multi-component workflows
- [Common Use Cases](docs/usage/common-use-cases.md) - Real-world scenarios

### Project Information
- [Project Overview](docs/project_overview.md) - Comprehensive project analysis
- [Project Summary](docs/PROJECT_OVERVIEW_2.md) - High-level overview
- [Product Requirements](docs/Product%20Requirements%20Document%20-%20Minerva.md) - PRD

## Technology Stack

- **Backend**: Python 3.12+, FastAPI, Temporal.io, Neo4j
- **Desktop**: Next.js 15, React 19, Tauri 2, TypeScript
- **Agents**: LangGraph, deepagents, Google Gemini
- **Database**: Neo4j (graph), SQLite (curation queue)
- **AI/ML**: Ollama (local LLM), Google Gemini (agents)

## Project Structure

```
Minerva/
├── backend/              # Backend API and Temporal workflows
│   ├── src/             # Backend source (API, processing, quote/concept/inbox workflows)
│   ├── minerva_agent/   # LangGraph agent (read-only + workflow launchers, HITL)
│   ├── zettel/          # Deprecated (quote/concept migrated to backend)
│   └── docs/            # Backend documentation
├── frontend/            # Curation UI (Vue.js): Queue, Quotes, Concepts, Inbox, Notifications
├── minerva-desktop/     # Desktop application (Tauri + React)
├── docs/                # Project documentation
└── README.md           # This file
```

## Features

### Journal Processing
- Multi-stage entity extraction
- Relationship discovery
- Human-in-the-loop curation
- Knowledge graph integration

### Agent Assistance
- Obsidian vault: read-only tools (read_file, list_dir, glob, grep)
- Workflow launchers (quote parsing, concept extraction, inbox classification) with HITL confirmation
- Irreversible actions only after approval in Curation UI

### Quote, Concept, and Inbox Workflows
- Quote parsing from book markdown → Curation UI (Quotes) → Neo4j
- Concept extraction from content quotes → Curation UI (Concepts) → Neo4j
- Inbox classification (LLM-suggested moves) → Curation UI (Inbox) → file moves
- Notifications (workflow_started, curation_pending, workflow_completed) in Curation UI

### Desktop Application
- Real-time agent chat
- Task and file management
- Thread history
- Subagent monitoring

## Development

### Running Tests

**Backend**:
```bash
cd backend
poetry run pytest
```

### Code Quality

**Backend**:
```bash
cd backend
poetry run black src/
poetry run isort src/
poetry run flake8 src/
```

**Desktop**:
```bash
cd minerva-desktop
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

See [LICENSE](LICENSE) file for details.

## Support

- **Documentation**: See [docs/](docs/) directory
- **Issues**: Create an issue on GitHub
- **Questions**: Check documentation or create a discussion

## Roadmap

- Enhanced graph visualization
- Advanced concept linking
- Improved agent capabilities
- Better integration between components
- Performance optimizations

---

Built with ❤️ for personal knowledge management

