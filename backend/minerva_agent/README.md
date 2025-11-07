# Minerva Agent

A deep agent for Obsidian vault assistance built with LangChain's deepagents package. Minerva Agent provides intelligent file system operations, search capabilities, task planning, and subagent delegation for managing your Obsidian knowledge base.

## Features

- **File System Operations**: Read, write, and edit markdown files in your Obsidian vault
- **Search & Discovery**: Find files using glob patterns and search content with grep
- **Task Planning**: Break down complex tasks into manageable steps
- **Subagents**: Delegate specialized work to subagents for context isolation
- **Google Gemini**: Powered by Gemini 2.5 Flash for fast, efficient responses
- **Bilingual Support**: Responds in Spanish (Argentine) or English based on user input

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Google API key
- Obsidian vault (local filesystem)

### Installation

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
   - Create a `.env` file in this directory
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```
   - Optionally override the vault path (defaults to `D:\yo`):
     ```
     OBSIDIAN_VAULT_PATH=D:\your\vault\path
     ```

## Running the Agent

### Development Server

Start the development server:
```bash
poetry run langgraph dev
```

This will start a local server at `http://127.0.0.1:2024` that you can interact with via:
- LangGraph Studio
- Minerva Desktop application
- Direct API calls

### Production Deployment

Build and deploy using LangGraph CLI:
```bash
poetry run langgraph up
```

## Agent Capabilities

The agent provides the following capabilities:

### File Operations
- **Read Files**: Read markdown files with support for line ranges
- **Write Files**: Create new markdown files
- **Edit Files**: Edit existing files with precise string replacements
- **List Directory**: List files and directories with metadata

### Search Operations
- **Pattern Matching**: Find files using glob patterns
- **Content Search**: Search file contents with grep

### Task Management
- **Task Planning**: Plan and track complex multi-step operations
- **Task Execution**: Execute planned tasks with progress tracking

### Subagent System
- **Subagent Delegation**: Spawn specialized subagents for isolated tasks
- **Context Isolation**: Each subagent operates in its own context

## System Prompt

The agent is configured with a bilingual system prompt that:
- Responds in Spanish (Argentine) or English based on user input
- Uses "vos" form in Spanish (Buenos Aires dialect)
- Provides warm, conversational assistance
- Understands Obsidian vault structure (Daily Notes, Inbox, etc.)

## Configuration

The agent is configured via `langgraph.json`:
```json
{
  "graphs": {
    "minerva_agent": "./src/minerva_agent/agent.py:graph"
  },
  "env": ".env"
}
```

The main graph is exported from `src/minerva_agent/agent.py`.

## Architecture

- **Built on LangGraph**: Stateful, durable execution with workflow management
- **Uses deepagents**: Planning, filesystem, and subagent capabilities
- **Google Gemini 2.5 Pro**: LLM for agent reasoning and responses
- **FilesystemBackend**: Direct access to your Obsidian vault
- **Virtual Mode**: Path sandboxing and normalization for Windows compatibility

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Google API key for Gemini | Yes | - |
| `OBSIDIAN_VAULT_PATH` | Path to Obsidian vault | No | `D:\yo` |

## Integration

### With Minerva Desktop

1. Start the agent server: `poetry run langgraph dev`
2. Configure Minerva Desktop with:
   - `NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"`
   - `NEXT_PUBLIC_AGENT_ID="minerva_agent"`

### With LangGraph Studio

1. Start the agent server: `poetry run langgraph dev`
2. Open LangGraph Studio
3. Connect to `http://127.0.0.1:2024`

## Development

### Project Structure

```
minerva_agent/
├── src/
│   └── minerva_agent/
│       ├── agent.py          # Main agent graph definition
│       └── __init__.py
├── langgraph.json            # LangGraph configuration
├── pyproject.toml            # Poetry dependencies
└── .env                      # Environment variables (not in git)
```

### Adding New Capabilities

The agent uses the `deepagents` package which provides:
- Filesystem operations
- Task planning
- Subagent delegation

To extend capabilities, modify the system prompt in `agent.py` or add custom tools.

## Troubleshooting

### Connection Issues
- Verify Google API key is set correctly
- Check vault path is accessible
- Ensure LangGraph server is running on port 2024

### File Access Issues
- Verify `OBSIDIAN_VAULT_PATH` points to correct directory
- Check file permissions
- On Windows, ensure paths use proper format

## Documentation

For detailed documentation, see:
- [Architecture Documentation](../../docs/architecture/minerva-agent.md)
- [Setup Guide](../../docs/setup/minerva-agent-setup.md)
- [Usage Guide](../../docs/usage/minerva-agent.md)

## License

See project root LICENSE file.
