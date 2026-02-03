# Environment Variables Reference

Complete reference of all environment variables used across Minerva components.

## Backend API

Location: `backend/.env`

The backend uses pydantic-settings with `MINERVA_` prefix: set `MINERVA_<FIELD>` for each config field (e.g. `MINERVA_NEO4J_URI`).

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MINERVA_NEO4J_URI` | Neo4j connection URI | Yes | `bolt://localhost:7687` |
| `MINERVA_NEO4J_USER` | Neo4j username | Yes | `neo4j` |
| `MINERVA_NEO4J_PASSWORD` | Neo4j password | Yes | - |
| `MINERVA_TEMPORAL_URI` | Temporal server address | Yes | `localhost:7233` |
| `MINERVA_CURATION_DB_PATH` | SQLite curation DB path | No | `curation.db` |
| `MINERVA_OBSIDIAN_VAULT_PATH` | Obsidian vault path (workflows) | No | (platform-dependent) |

Ollama URL and model are currently hardcoded in the backend LLM service (defaults: `http://localhost:11434`, model `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest`). They are not read from env yet.

## minerva_agent

Location: `backend/minerva_agent/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |
| `OBSIDIAN_VAULT_PATH` | Path to Obsidian vault | No | `D:\yo` |

## Curation UI (frontend)

Location: `frontend/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | No | `http://localhost:8000` |

## zettel *(deprecated)*

Location: `backend/zettel/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |

Note: Neo4j connection configured in `src/zettel_agent/db.py` (not environment variable).

## minerva-desktop

Location: `minerva-desktop/.env.local`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_DEPLOYMENT_URL` | LangGraph server URL | Yes | `http://127.0.0.1:2024` |
| `NEXT_PUBLIC_AGENT_ID` | Agent ID from langgraph.json | Yes | `minerva_agent` |
| `NEXT_PUBLIC_LANGSMITH_API_KEY` | LangSmith API key | No | - |

Note: `NEXT_PUBLIC_*` variables are exposed to the browser client.

## Environment File Examples

### Backend API (.env)

```env
MINERVA_NEO4J_URI=bolt://localhost:7687
MINERVA_NEO4J_USER=neo4j
MINERVA_NEO4J_PASSWORD=your-secure-password
MINERVA_TEMPORAL_URI=localhost:7233
# MINERVA_CURATION_DB_PATH=curation.db
# MINERVA_OBSIDIAN_VAULT_PATH=D:\path\to\vault
```

### minerva_agent (.env)

```env
GOOGLE_API_KEY=AIzaSy...
OBSIDIAN_VAULT_PATH=D:\Documents\Obsidian\MyVault
```

### zettel (.env)

```env
GOOGLE_API_KEY=AIzaSy...
```

### minerva-desktop (.env.local)

```env
NEXT_PUBLIC_DEPLOYMENT_URL=http://127.0.0.1:2024
NEXT_PUBLIC_AGENT_ID=minerva_agent
NEXT_PUBLIC_LANGSMITH_API_KEY=lsv2_...
```

## Security Notes

### Never Commit .env Files

All `.env` files should be in `.gitignore`:
```
.env
.env.local
.env.*.local
```

### API Keys

- Store API keys in environment variables, never in code
- Use different keys for development and production
- Rotate keys regularly
- Never share keys publicly

### Client-Side Variables

Only `NEXT_PUBLIC_*` variables in Next.js are exposed to the browser. Never put secrets in these variables.

### Production

For production deployments:
- Use secure secret management (e.g., AWS Secrets Manager, HashiCorp Vault)
- Set environment variables in deployment platform
- Use different credentials for production
- Enable encryption at rest

## Validation

### Check Environment Variables

**Backend**:
```bash
cd backend
poetry run python -c "from minerva_backend.config import settings; print(settings)"
```

**Agents**:
```bash
cd backend/minerva_agent
poetry run python -c "import os; print('GOOGLE_API_KEY:', 'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET')"
```

**Desktop**:
```bash
cd minerva-desktop
node -e "console.log(process.env.NEXT_PUBLIC_DEPLOYMENT_URL)"
```

## Troubleshooting

### Variable Not Found

- Verify file is named correctly (`.env` or `.env.local`)
- Check file is in correct directory
- Restart application after adding variables
- Verify no typos in variable names

### Wrong Values

- Check for extra spaces or quotes
- Verify variable names match exactly
- Check for case sensitivity
- Review default values if variable not set

### Client-Side Variables

- Must start with `NEXT_PUBLIC_` in Next.js
- Rebuild application after changes
- Check browser console for values
- Verify no secrets in client variables

## Related Documentation

- [Complete Setup Guide](complete-setup.md)
- [Component Setup Guides](minerva-desktop-setup.md)

