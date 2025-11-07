# Quick Start Guide

Get Minerva up and running in 10 minutes.

## Prerequisites

- Python 3.12+ and Poetry
- Node.js 18+ and npm
- Neo4j Desktop or Neo4j server
- Rust and Cargo (for minerva-desktop)
- Google API key (for agents)

## Step 1: Backend Setup (5 minutes)

```bash
cd backend
poetry install
poetry run python -m minerva_backend.api.main
```

Backend runs on `http://localhost:8000`

## Step 2: Start Neo4j (1 minute)

- Open Neo4j Desktop
- Start your database
- Default connection: `bolt://localhost:7687`

## Step 3: Start an Agent (2 minutes)

### minerva_agent
```bash
cd backend/minerva_agent
poetry install
# Create .env with GOOGLE_API_KEY
poetry run langgraph dev
```

### zettel
```bash
cd backend/zettel
poetry install
# Create .env with GOOGLE_API_KEY
poetry run langgraph dev
```

## Step 4: Start minerva-desktop (2 minutes)

```bash
cd minerva-desktop
npm install
# Create .env.local with:
# NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
# NEXT_PUBLIC_AGENT_ID="minerva_agent"
npm run tauri:dev
```

## Verify Installation

1. Backend API: `http://localhost:8000/api/health`
2. Agent Server: `http://127.0.0.1:2024` (check LangGraph Studio)
3. Desktop App: Should open automatically

## Next Steps

- See [Complete Setup Guide](complete-setup.md) for detailed configuration
- Check [Component-Specific Setup](minerva-desktop-setup.md) guides
- Review [Usage Guides](../usage/overview.md)

## Troubleshooting

**Backend won't start**: Check Neo4j is running
**Agent won't start**: Verify Google API key in `.env`
**Desktop won't build**: Install Rust toolchain

For detailed help, see component-specific setup guides.

