# Minerva Agent Setup Guide

Detailed setup instructions for the minerva_agent LangGraph agent.

## Prerequisites

- Python 3.12+
- Poetry
- Google API key
- Obsidian vault (local filesystem)

## Installation

### 1. Navigate to Directory

```bash
cd backend/minerva_agent
```

### 2. Install Dependencies

```bash
poetry install
```

This installs:
- LangGraph and LangGraph CLI
- deepagents package
- Google Gemini integration
- Other dependencies

### 3. Configure Environment

Create `.env` file in `backend/minerva_agent/`:

```env
# Required: Google API key for Gemini
GOOGLE_API_KEY=your-google-api-key-here

# Optional: Obsidian vault path (defaults to D:\yo)
OBSIDIAN_VAULT_PATH=D:\your\vault\path
```

### 4. Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create new API key
3. Copy key to `.env` file

## Running the Agent

### Development Server

```bash
poetry run langgraph dev
```

This:
- Starts LangGraph server on `http://127.0.0.1:2024`
- Enables hot reload
- Exposes agent via HTTP and WebSocket

### Production Deployment

```bash
poetry run langgraph up
```

Deploys to LangGraph Platform (requires account setup).

## Configuration

### langgraph.json

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "minerva_agent": "./src/minerva_agent/agent.py:graph"
  },
  "env": ".env"
}
```

### Agent Configuration

Edit `src/minerva_agent/agent.py` to customize:
- System prompt
- Model settings
- Vault path
- Agent behavior

## Verification

### Check Server Status

```bash
curl http://127.0.0.1:2024/health
```

### Test with LangGraph Studio

1. Open [LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/)
2. Connect to `http://127.0.0.1:2024`
3. Select `minerva_agent` graph
4. Send test message

### Test with Minerva Desktop

1. Configure desktop app (see [minerva-desktop setup](minerva-desktop-setup.md))
2. Start desktop app
3. Verify connection to agent

## Customization

### System Prompt

Edit `vault_assistant_prompt` in `agent.py`:
- Modify language behavior
- Add new instructions
- Change personality

### Model Settings

```python
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",  # Change model
    temperature=0,            # Adjust creativity
)
```

### Vault Path

Set in environment variable or code:
```python
_vault_path = os.getenv("OBSIDIAN_VAULT_PATH", r"D:\yo")
```

## Troubleshooting

### Server Won't Start

**Port already in use**:
- LangGraph automatically uses next available port
- Check logs for actual port number
- Update desktop app configuration

**Missing dependencies**:
```bash
poetry install
poetry run langgraph --version
```

### Agent Not Responding

**API key issues**:
- Verify `GOOGLE_API_KEY` in `.env`
- Check API key is valid
- Verify API quota not exceeded

**Vault path issues**:
- Verify path exists
- Check path format (Windows: `D:\path`, Unix: `/path`)
- Verify read/write permissions

### Connection Issues

**Desktop can't connect**:
- Verify server is running
- Check `NEXT_PUBLIC_DEPLOYMENT_URL` matches server URL
- Verify `NEXT_PUBLIC_AGENT_ID` matches graph name

**LangGraph Studio can't connect**:
- Check server is running
- Verify URL is correct
- Check firewall settings

## Development

### Project Structure

```
minerva_agent/
├── src/
│   └── minerva_agent/
│       ├── agent.py          # Main agent graph
│       └── __init__.py
├── langgraph.json            # Server config
├── pyproject.toml            # Dependencies
└── .env                      # Environment (not in git)
```

### Adding Features

1. Modify system prompt for new behaviors
2. Add custom tools via deepagents
3. Extend FilesystemBackend capabilities
4. Update agent graph structure

### Testing

Test agent locally:
```bash
poetry run langgraph dev
# Then use LangGraph Studio or desktop app
```

## Integration

### With Minerva Desktop

1. Start agent: `poetry run langgraph dev`
2. Configure desktop with agent URL and ID
3. Connect from desktop app

### With LangGraph Studio

1. Start agent: `poetry run langgraph dev`
2. Open LangGraph Studio
3. Connect to server URL

### With Other Clients

Use LangGraph SDK:
```python
from langchain.langgraph_sdk import get_client

client = get_client("http://127.0.0.1:2024")
# Use client to interact with agent
```

## Related Documentation

- [Architecture](../architecture/minerva-agent.md)
- [Usage Guide](../usage/minerva-agent.md)
- [Quick Start](quick-start.md)

