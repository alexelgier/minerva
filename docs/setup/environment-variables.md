# Environment Variables Reference

Complete reference of all environment variables used across Minerva components.

## Backend API

Location: `backend/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NEO4J_URI` | Neo4j connection URI | Yes | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | Yes | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Yes | - |
| `TEMPORAL_HOST` | Temporal server host | No | `localhost` |
| `TEMPORAL_PORT` | Temporal server port | No | `7233` |
| `OLLAMA_BASE_URL` | Ollama server URL | No | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | No | `qwen2.5:7b` |

## minerva_agent

Location: `backend/minerva_agent/.env`

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |
| `OBSIDIAN_VAULT_PATH` | Path to Obsidian vault | No | `D:\yo` |

## zettel

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
| `NEXT_PUBLIC_AGENT_ID` | Agent ID from langgraph.json | Yes | `deepagent` |
| `NEXT_PUBLIC_LANGSMITH_API_KEY` | LangSmith API key | No | - |

Note: `NEXT_PUBLIC_*` variables are exposed to the browser client.

## Environment File Examples

### Backend API (.env)

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-secure-password
TEMPORAL_HOST=localhost
TEMPORAL_PORT=7233
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
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

