# Minerva Desktop Usage Guide

How to use the Minerva Desktop application to interact with LangGraph agents.

## Getting Started

### Launch the Application

1. Start your LangGraph agent server
2. Launch minerva-desktop:
   ```bash
   npm run tauri:dev
   ```
3. Application opens with chat interface

### First Connection

1. Verify agent server is running
2. Check environment variables are set
3. Application automatically connects
4. Connection status shown in UI

## Interface Overview

### Main Chat Area

- **Message Input**: Type messages at bottom
- **Chat History**: Scrollable message history
- **Agent Responses**: Streaming text responses
- **Tool Calls**: Visual indicators for agent tools

### Sidebar

- **Tasks**: List of todos from agent
- **Files**: Files created or modified by agent
- **Collapse/Expand**: Toggle sidebar visibility

### Thread Management

- **Thread History**: Access via history button
- **New Thread**: Create new conversation
- **Thread Switching**: Click thread to switch

### Subagent Panel

- **Subagent Indicator**: Shows when subagent active
- **Subagent Panel**: Detailed subagent information
- **Close Panel**: Click X to close

## Basic Usage

### Sending Messages

1. Type message in input field
2. Press Enter or click Send
3. Message appears in chat
4. Agent processes and responds
5. Response streams in real-time

### Viewing Tasks

1. Agent creates tasks during execution
2. Tasks appear in sidebar
3. Click task to view details
4. Tasks update in real-time

### Viewing Files

1. Agent creates or modifies files
2. Files appear in sidebar
3. Click file to view content
4. File viewer opens in modal

### Managing Threads

1. Click history button
2. See list of previous threads
3. Click thread to switch
4. Create new thread with + button

## Advanced Features

### Subagent Monitoring

When agent delegates to subagent:
1. Subagent indicator appears
2. Click to open subagent panel
3. View subagent activity
4. Monitor subagent progress

### Keyboard Shortcuts

- **Enter**: Send message
- **Escape**: Close modals
- **Ctrl/Cmd + K**: Focus input (if implemented)

### System Tray

- **Minimize**: App minimizes to tray
- **Right-click**: Access menu
- **Show**: Restore window
- **Quit**: Exit application

## Workflow Examples

### Organizing Obsidian Inbox

1. Open minerva-desktop
2. Connect to minerva_agent
3. Send: "Help me organize my inbox"
4. Agent plans tasks
5. Agent executes file operations
6. Review changes in sidebar
7. Approve or modify as needed

### Reading Journal Entry

1. Connect to minerva_agent
2. Send: "Read my journal from today"
3. Agent reads file
4. Content displayed in chat
5. Can ask follow-up questions

### Processing Book Quotes

1. Connect to zettel agent
2. Use quote_parse_graph
3. Process book markdown file
4. Quotes stored in Neo4j
5. Run concept_extraction_graph
6. Concepts extracted and displayed

## Tips and Best Practices

### Clear Communication

- Be specific in requests
- Break complex tasks into steps
- Review agent plans before execution

### Monitoring Progress

- Watch task sidebar for progress
- Check file sidebar for changes
- Monitor subagent panel for delegation

### Thread Management

- Use separate threads for different topics
- Keep thread history organized
- Create new thread for new projects

### Error Handling

- Check connection status
- Verify agent server is running
- Review error messages in chat
- Restart if connection lost

## Troubleshooting

### Connection Issues

**Can't connect to agent**:
- Verify agent server is running
- Check `NEXT_PUBLIC_DEPLOYMENT_URL`
- Verify `NEXT_PUBLIC_AGENT_ID` matches

**Connection lost**:
- Application auto-reconnects
- Check agent server status
- Restart if needed

### UI Issues

**Messages not appearing**:
- Check agent is responding
- Verify streaming is working
- Refresh if needed

**Sidebar not updating**:
- Agent state updates in real-time
- Check agent is creating tasks/files
- Verify state updates are working

### Performance

**Slow responses**:
- Check agent server performance
- Verify network connection
- Monitor agent processing time

**High memory usage**:
- Close old threads
- Clear chat history (if implemented)
- Restart application

## Related Documentation

- [Architecture](../architecture/minerva-desktop.md)
- [Setup Guide](../setup/minerva-desktop-setup.md)
- [Integration Workflows](integration-workflows.md)

