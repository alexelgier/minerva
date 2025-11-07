# Complete Setup Guide

Comprehensive setup instructions for all Minerva components.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Backend Setup](#backend-setup)
3. [Neo4j Configuration](#neo4j-configuration)
4. [Agent Setup](#agent-setup)
5. [Desktop App Setup](#desktop-app-setup)
6. [Environment Variables](#environment-variables)
7. [Verification](#verification)

## Prerequisites

### Required Software

- **Python 3.12+**: [Download](https://www.python.org/downloads/)
- **Poetry**: [Installation Guide](https://python-poetry.org/docs/#installation)
- **Node.js 18+**: [Download](https://nodejs.org/)
- **Neo4j**: [Neo4j Desktop](https://neo4j.com/download/) or server
- **Rust**: [Installation](https://www.rust-lang.org/tools/install) (for desktop app)
- **Ollama**: [Installation](https://ollama.ai/) (for local LLM)

### Required Accounts

- **Google API Key**: [Get API Key](https://makersuite.google.com/app/apikey) (for agents)

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
poetry install
```

### 2. Configure Environment

Create `.env` file in `backend/`:

```env
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Temporal Configuration (if using)
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

### 3. Initialize Database

```bash
poetry run python -c "from minerva_backend.containers import Container; container = Container(); container.db_connection().init_emotion_types()"
```

### 4. Start Backend

```bash
poetry run python -m minerva_backend.api.main
```

Backend runs on `http://localhost:8000`

### 5. Verify Backend

```bash
curl http://localhost:8000/api/health
```

## Neo4j Configuration

### Using Neo4j Desktop

1. Install Neo4j Desktop
2. Create new database
3. Set password
4. Start database
5. Note connection details:
   - URI: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: (your password)

### Using Neo4j Server

1. Install Neo4j server
2. Configure in `neo4j.conf`
3. Start server
4. Access at `http://localhost:7474`

### Create Vector Indexes (for zettel)

Indexes are created automatically by zettel agent, but you can verify:

```cypher
SHOW INDEXES
```

Should show `quote_embeddings_index` and `concept_embeddings_index`.

## Agent Setup

### minerva_agent

1. **Navigate to directory**:
```bash
cd backend/minerva_agent
```

2. **Install dependencies**:
```bash
poetry install
```

3. **Create `.env` file**:
```env
GOOGLE_API_KEY=your-google-api-key
OBSIDIAN_VAULT_PATH=D:\your\vault\path
```

4. **Start agent server**:
```bash
poetry run langgraph dev
```

Server runs on `http://127.0.0.1:2024`

### zettel

1. **Navigate to directory**:
```bash
cd backend/zettel
```

2. **Install dependencies**:
```bash
poetry install
```

3. **Create `.env` file**:
```env
GOOGLE_API_KEY=your-google-api-key
```

4. **Ensure Neo4j is running** (required for zettel)

5. **Start agent server**:
```bash
poetry run langgraph dev
```

Server runs on `http://127.0.0.1:2024` (different port if minerva_agent is running)

## Desktop App Setup

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

Create `.env.local` file:

```env
# LangGraph Server URL
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"

# Agent ID (from langgraph.json)
NEXT_PUBLIC_AGENT_ID="minerva_agent"

# LangSmith API Key (optional for local, required for production)
NEXT_PUBLIC_LANGSMITH_API_KEY="your-langsmith-key"
```

### 4. Development Mode

```bash
# Full Tauri app
npm run tauri:dev

# Next.js only (faster, no native features)
npm run dev
```

### 5. Build Production App

```bash
npm run tauri:build
```

Output in `src-tauri/target/release/`

## Environment Variables

See [Environment Variables Reference](environment-variables.md) for complete list.

## Verification

### Backend
```bash
curl http://localhost:8000/api/health
# Should return: {"status":"healthy"}
```

### Agent Server
```bash
curl http://127.0.0.1:2024/health
# Or open LangGraph Studio: http://127.0.0.1:2024
```

### Desktop App
- Should launch automatically in dev mode
- Check console for connection status
- Try sending a message to verify agent connection

### Neo4j
```bash
# Using cypher-shell
cypher-shell -u neo4j -p your-password
# Run: MATCH (n) RETURN count(n);
```

## Common Issues

### Port Conflicts
- Backend: Change port in `uvicorn` command
- Agents: LangGraph uses different ports automatically
- Desktop: Change `NEXT_PUBLIC_DEPLOYMENT_URL`

### Neo4j Connection
- Verify Neo4j is running
- Check connection string matches
- Verify credentials

### Agent Connection
- Verify agent server is running
- Check `NEXT_PUBLIC_DEPLOYMENT_URL` matches server
- Verify `NEXT_PUBLIC_AGENT_ID` matches langgraph.json

### Build Issues
- Install Rust: `rustc --version`
- Install Tauri CLI: `npm install -g @tauri-apps/cli`
- Check Tauri prerequisites

## Next Steps

- [Component-Specific Setup Guides](minerva-desktop-setup.md)
- [Usage Guides](../usage/overview.md)
- [Architecture Documentation](../architecture/components.md)

