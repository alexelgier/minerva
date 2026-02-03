# Minerva Agent Architecture

Minerva Agent is a LangGraph-based agent for Obsidian vault assistance. It provides read-only vault access and launches Temporal workflows (quote parsing, concept extraction, inbox classification) with mandatory human-in-the-loop (HITL) confirmation. Irreversible actions are performed by backend Temporal workflows after curation in the Curation UI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              LangGraph Server (minerva_agent)           │
│  - State Management                                    │
│  - HumanInTheLoopMiddleware (workflow tools)           │
│  - Tool Execution                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Graph (create_agent)                  │
│  - LangChain 1.x create_agent                          │
│  - HITL interrupt on workflow-launch tools             │
└──────────────────┬──────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌──────────────────┐
│ Read-only     │    │ Workflow launcher │
│ tools         │    │ tools             │
│ read_file,    │    │ start_quote_      │
│ list_dir,     │    │ parsing,          │
│ glob, grep    │    │ start_concept_    │
│ (vault only)  │    │ extraction,       │
└───────┬───────┘    │ start_inbox_      │
        │            │ classification,  │
        ▼            │ get_workflow_     │
 Obsidian Vault      │ status            │
                    └─────────┬─────────┘
                              ▼
                    Temporal (backend workflows)
```

## Technology Stack

- **LangGraph**: Workflow orchestration and state management
- **LangChain 1.x**: `create_agent` (replaces legacy deepagents)
- **Google Gemini**: LLM for agent reasoning
- **HumanInTheLoopMiddleware**: Mandatory confirmation for workflow-launch tools
- **Temporal client**: Start workflows and query status (minerva-backend)
- **Python 3.12+**: Runtime environment

## Agent Graph Structure

### Main Graph (`agent.py`)

- Uses `langchain.agents.create_agent` with LangChain 1.x specification.
- **HumanInTheLoopMiddleware**: Interrupts on workflow-launcher tool names so the user must confirm before a workflow is started.
- No direct file writes; no deepagents or FilesystemBackend write tools.

### Tools

1. **Read-only tools** (sandboxed to `OBSIDIAN_VAULT_PATH`): `read_file`, `list_dir`, `glob`, `grep`
2. **Workflow launcher tools** (require HITL): `start_quote_parsing`, `start_concept_extraction`, `start_inbox_classification`, `get_workflow_status`

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

### Read-Only Tools (vault sandbox)
- **read_file**: Read markdown file content (optional line range)
- **list_dir**: List files and directories under vault path
- **glob**: Find files matching a pattern under vault
- **grep**: Search file contents under vault

### Workflow Launcher Tools (HITL required)
- **start_quote_parsing**: Start Temporal QuoteParsing workflow (file_path, author, title); user must confirm in chat
- **start_concept_extraction**: Start Temporal ConceptExtraction workflow (content_uuid); user must confirm
- **start_inbox_classification**: Start Temporal InboxClassification workflow (inbox_path); user must confirm
- **get_workflow_status**: Query Temporal for workflow status by ID

### Design Principles
- **No write tools**: Agent does not write, edit, or delete files directly. Quote/concept/inbox workflows perform irreversible actions only after human approval in the Curation UI.
- **Path Sandboxing**: All read tools are restricted to `OBSIDIAN_VAULT_PATH`.

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

### With Backend Temporal
- Workflow launcher tools start workflows via Temporal client (minerva-backend)
- Curation UI (Quotes, Concepts, Inbox) is the only surface for approving workflow steps
- Notifications emitted by workflows appear in Curation UI (Notifications)

## Workflow Example

1. **User Request**: "Parse quotes from book X"
2. **Agent**: Proposes `start_quote_parsing` with file_path, author, title
3. **HITL**: User confirms in chat; workflow starts
4. **Backend**: QuoteParsing workflow parses file, submits items to curation DB, emits notification
5. **User**: Reviews quotes in Curation UI (Quotes), accepts/rejects, completes workflow
6. **Backend**: Workflow writes Content, Quote, Person and relations to Neo4j

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
│       ├── agent.py          # Main graph (create_agent + HITL)
│       ├── tools/
│       │   ├── read_file.py
│       │   ├── list_dir.py
│       │   ├── glob.py
│       │   ├── grep.py
│       │   ├── start_workflows.py   # quote/concept/inbox launchers
│       │   └── get_workflow_status.py
│       └── __init__.py
├── langgraph.json            # Server configuration
└── pyproject.toml            # Dependencies (langchain, temporalio, minerva-backend)
```

### Running Locally
```bash
poetry run langgraph dev
```

### Extending Capabilities
- Modify system prompt for new behaviors
- Add read-only tools in `tools/` (sandboxed to vault)
- Add workflow launcher tools that call Temporal; register tool names in HITL middleware

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

