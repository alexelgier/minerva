# Minerva Agent Usage Guide

How to use the minerva_agent for Obsidian vault assistance.

## Getting Started

### Start the Agent

```bash
cd backend/minerva_agent
poetry run langgraph dev
```

Agent server starts on `http://127.0.0.1:2024`

### Connect from Desktop

1. Configure minerva-desktop (see [desktop setup](../setup/minerva-desktop-setup.md))
2. Launch desktop app
3. Agent connects automatically

### Connect from LangGraph Studio

1. Open LangGraph Studio
2. Connect to `http://127.0.0.1:2024`
3. Select `minerva_agent` graph
4. Start chatting

## Agent Capabilities

### File Operations

**Read Files**:
```
"Read my journal entry from today"
"Show me the file at /02 - Daily Notes/2025-01-15.md"
```

**Write Files**:
```
"Create a new note called 'Meeting Notes' in the inbox"
"Write a summary of today's work"
```

**Edit Files**:
```
"Add a section about project status to my journal"
"Update the todo list in my daily note"
```

**List Directory**:
```
"Show me all files in the inbox"
"What files are in /02 - Daily Notes?"
```

### Search Operations

**Find Files**:
```
"Find all files about 'project X'"
"Show me notes from last week"
```

**Search Content**:
```
"Search for mentions of 'meeting' in my notes"
"Find where I wrote about 'deadline'"
```

### Task Planning

**Complex Tasks**:
```
"Help me organize my inbox"
"Plan the steps to migrate my notes"
"Break down the task of reviewing my journal entries"
```

Agent will:
1. Plan steps
2. Execute tasks
3. Report progress
4. Show results

### Subagent Delegation

Agent automatically delegates specialized work:
- File organization tasks
- Content analysis
- Complex multi-step operations

Monitor subagent activity in desktop app.

## Usage Examples

### Daily Workflow

**Morning**:
```
"Read my journal from yesterday"
"What did I write about yesterday?"
```

**During Day**:
```
"Add a note about the meeting to my inbox"
"Update my project status"
```

**Evening**:
```
"Help me organize my inbox"
"Create a summary of today"
```

### Vault Organization

**Organize Inbox**:
```
"Help me organize my inbox"
"Classify the notes in /01 - Inbox/"
```

Agent will:
1. Read inbox files
2. Analyze content
3. Suggest organization
4. Move files (with approval)

**Review Notes**:
```
"Show me all notes about 'project X'"
"Find notes I haven't reviewed in a while"
```

### Content Creation

**Create Notes**:
```
"Create a new note about 'Meeting Notes' with today's date"
"Write a summary of the book I'm reading"
```

**Update Notes**:
```
"Add a section to my journal about today's work"
"Update the status in my project note"
```

## Language Support

Agent responds in your language:
- **English**: Default responses
- **Spanish (Argentine)**: Uses "vos" form, Buenos Aires dialect

Agent matches your input language automatically.

## Best Practices

### Clear Requests

**Good**:
```
"Read my journal entry from 2025-01-15"
"Organize all files in the inbox folder"
"Create a new note called 'Meeting Notes'"
```

**Less Clear**:
```
"Do that thing with my notes"
"Fix my files"
```

### Specific Paths

When possible, specify exact paths:
```
"/02 - Daily Notes/2025-01-15.md"
"/01 - Inbox/Meeting Notes.md"
```

### Task Breakdown

For complex tasks, let agent plan:
```
"Help me organize my vault"  # Agent will plan steps
```

### Review Before Execution

- Review agent's plan
- Approve file operations
- Check file changes before committing

## Integration with Backend

Agent can work with backend API:
- Query knowledge graph
- Process journal entries
- Extract entities
- Manage concepts

## Troubleshooting

### Agent Not Responding

- Verify agent server is running
- Check Google API key is set
- Verify vault path is correct
- Check agent logs

### File Access Issues

- Verify vault path exists
- Check file permissions
- Verify path format (Windows vs Unix)
- Check path sandboxing settings

### Language Issues

- Agent matches your language
- If wrong language, try being explicit
- Check system prompt for language settings

### Performance

- Complex tasks may take time
- Monitor agent progress
- Check for subagent activity
- Review task planning steps

## Advanced Usage

### Custom System Prompt

Edit `src/minerva_agent/agent.py` to customize:
- Agent personality
- Language behavior
- Vault structure understanding
- Task preferences

### Tool Extension

Add custom tools via deepagents:
- New file operations
- Custom search functions
- Integration with other services

### Workflow Integration

Integrate agent into workflows:
- Automated vault organization
- Scheduled tasks
- Backend API integration

## Related Documentation

- [Architecture](../architecture/minerva-agent.md)
- [Setup Guide](../setup/minerva-agent-setup.md)
- [Integration Workflows](integration-workflows.md)

