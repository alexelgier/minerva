# Minerva

A personal knowledge management system that transforms unstructured text (journal entries, book notes) into a structured knowledge graph using AI-powered entity extraction, relationship discovery, and concept organization.

> **🎉 Version 0.2.0 Milestone**: Minerva is now usable for the first time! With minerva-desktop and minerva-agent working together, you can interact with your Obsidian vault through a native desktop application. While still limited, the core system is functional end-to-end.

## Overview

Minerva helps you build a "second brain" by:
- **Processing Journal Entries**: Extract entities and relationships from daily journals
- **Managing Obsidian Vaults**: Intelligent assistance for file operations and organization
- **Extracting Concepts**: Process book quotes and extract atomic concepts (Zettels)
- **Building Knowledge Graphs**: Store and query interconnected knowledge in Neo4j

## Components

### Backend API
FastAPI-based REST API for journal processing, curation workflows, and knowledge graph management.

**Location**: `backend/`  
**Documentation**: [Backend README](backend/README.md) | [Backend Docs](backend/docs/)

### minerva-desktop
Native desktop application (Tauri + Next.js) for interacting with LangGraph agents.

**Location**: `minerva-desktop/`  
**Documentation**: [Desktop README](minerva-desktop/README.md) | [Architecture](docs/architecture/minerva-desktop.md)

### minerva_agent
LangGraph deep agent for Obsidian vault assistance with file operations, search, and task planning.

**Location**: `backend/minerva_agent/`  
**Documentation**: [Agent README](backend/minerva_agent/README.md) | [Architecture](docs/architecture/minerva-agent.md)

### zettel
LangGraph agent system for processing book quotes and extracting atomic concepts using Zettelkasten methodology.

**Location**: `backend/zettel/`  
**Documentation**: 
- [Module README](backend/zettel/README.md) - Overview and quick start
- [Module Documentation](backend/zettel/docs/) - Comprehensive API, architecture, developer guide, and workflows
- [Architecture Overview](docs/architecture/zettel.md) - High-level architecture
- [Usage Guide](docs/usage/zettel.md) - Usage examples

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

2. **Agent** (choose one or both):
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

3. **Desktop App**:
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
- [Zettel Usage](docs/usage/zettel.md) - Processing quotes and concepts
  - [Comprehensive Module Docs](backend/zettel/docs/) - Full API reference, architecture, developer guide, and workflows
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
├── backend/              # Backend API and agents
│   ├── src/             # Backend source code
│   ├── minerva_agent/   # Obsidian vault agent
│   ├── zettel/          # Quote and concept agent
│   └── docs/            # Backend documentation
├── minerva-desktop/     # Desktop application
├── frontend/            # Legacy Vue.js frontend
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
- Obsidian vault management
- File operations (read, write, edit)
- Search and discovery
- Task planning and execution

### Concept Extraction
- Quote parsing from books
- Atomic concept extraction
- Vector similarity search
- Knowledge organization

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

