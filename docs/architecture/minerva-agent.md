# Minerva Agent Architecture

Minerva Agent is a LangGraph-based deep agent for Obsidian vault assistance, providing intelligent file operations, search capabilities, and task planning.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph Server                          │
│  - State Management                                    │
│  - Workflow Orchestration                             │
│  - Tool Execution                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Deep Agent Graph                          │
│  - Planning Node                                       │
│  - Execution Node                                      │
│  - Tool Nodes                                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Tools & Backends                          │
│  - FilesystemBackend (Obsidian Vault)                  │
│  - Planning Tools                                     │
│  - Subagent Tools                                     │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
            Obsidian Vault
```

## Technology Stack

- **LangGraph**: Workflow orchestration and state management
- **deepagents**: Deep agent framework with planning and tools
- **Google Gemini 2.5 Pro**: LLM for agent reasoning
- **FilesystemBackend**: Direct vault file access
- **Python 3.12+**: Runtime environment

## Agent Graph Structure

### Main Graph (`agent.py`)

```python
graph = create_deep_agent(
    model=ChatGoogleGenerativeAI(model="gemini-2.5-pro"),
    system_prompt=vault_assistant_prompt,
    backend=FilesystemBackend(root_dir=VAULT_PATH, virtual_mode=True)
)
```

### Graph Nodes

1. **Planning Node**: Breaks down user requests into tasks
2. **Execution Node**: Executes tasks using available tools
3. **Tool Nodes**: Individual tool invocations
4. **Subagent Nodes**: Delegates work to specialized subagents

## System Prompt

The agent uses a bilingual system prompt that:
- Responds in Spanish (Argentine) or English based on user input
- Uses "vos" form in Spanish (Buenos Aires dialect)
- Provides warm, conversational assistance
- Understands Obsidian vault structure

### Key Instructions
- Daily Notes: `/02 - Daily Notes/` with format `YYYY-MM-DD.md`
- Inbox Processing: `/01 - Inbox/` for unclassified notes
- Language matching: Respond in user's language
- Conversational tone: Warm and helpful

## Tools and Capabilities

### Filesystem Operations
- **Read Files**: Read markdown files with line ranges
- **Write Files**: Create new markdown files
- **Edit Files**: Edit existing files with string replacements
- **List Directory**: List files and directories

### Search Operations
- **Glob Patterns**: Find files using patterns
- **Grep Search**: Search file contents

### Task Management
- **Task Planning**: Break down complex tasks
- **Task Execution**: Execute planned tasks
- **Progress Tracking**: Monitor task completion

### Subagent System
- **Subagent Creation**: Spawn specialized subagents
- **Context Isolation**: Each subagent has own context
- **Delegation**: Delegate specific work to subagents

## Filesystem Backend

### Configuration
```python
FilesystemBackend(
    root_dir=VAULT_PATH,
    virtual_mode=True  # Path sandboxing for Windows
)
```

### Features
- **Path Sandboxing**: Security through path normalization
- **Windows Compatibility**: Handles Windows path formats
- **Direct Access**: No intermediate layer, direct file operations

## State Management

### LangGraph State
- **Messages**: Conversation history
- **Tasks**: Planned and executed tasks
- **Files**: Files created or modified
- **Subagents**: Active subagent information

### State Updates
- Real-time updates via LangGraph SDK
- State persisted across agent invocations
- Thread-based state isolation

## Integration Points

### With Minerva Desktop
- LangGraph server exposes agent via HTTP/WebSocket
- Desktop app connects using LangGraph SDK
- Real-time streaming for responses

### With Obsidian Vault
- Direct filesystem access
- No Obsidian API required
- Works with any markdown vault

### With LangGraph Studio
- Visual debugging interface
- State inspection
- Workflow visualization

## Workflow Example

1. **User Request**: "Read my journal entry from today"
2. **Planning**: Agent plans to read `/02 - Daily Notes/2025-01-15.md`
3. **Execution**: FilesystemBackend reads the file
4. **Response**: Agent returns file content to user

## Environment Configuration

```env
GOOGLE_API_KEY=your-api-key
OBSIDIAN_VAULT_PATH=D:\your\vault\path
```

## Development

### Project Structure
```
minerva_agent/
├── src/
│   └── minerva_agent/
│       ├── agent.py          # Main graph definition
│       └── __init__.py
├── langgraph.json            # Server configuration
└── pyproject.toml            # Dependencies
```

### Running Locally
```bash
poetry run langgraph dev
```

### Extending Capabilities
- Modify system prompt for new behaviors
- Add custom tools via deepagents
- Extend FilesystemBackend capabilities

## Performance Considerations

- **Lazy Initialization**: LLM and backends initialized on first use
- **Caching**: LangGraph state caching
- **Streaming**: Incremental response generation
- **Batch Operations**: Efficient file operations

## Security

- **Path Sandboxing**: Virtual mode prevents path traversal
- **API Keys**: Stored in environment variables
- **Vault Isolation**: Only accesses specified vault directory

## Related Documentation

- [Components Overview](components.md)
- [Setup Guide](../setup/minerva-agent-setup.md)
- [Usage Guide](../usage/minerva-agent.md)
- [minerva_agent README](../../backend/minerva_agent/README.md)

