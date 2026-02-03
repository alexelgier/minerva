# Minerva Desktop Usage Guide

How to use the Minerva Desktop application to interact with LangGraph agents.

## Getting Started

### Launch the Application

1. Start your LangGraph agent server
2. Launch minerva-desktop:
   ```bash
   cd minerva-desktop
   npm run dev
   ```
3. Open http://localhost:3000 in your browser
4. Application shows chat interface with Minerva header

### First Connection

1. Verify agent server is running at `NEXT_PUBLIC_API_URL`
2. Check `.env` has correct `NEXT_PUBLIC_ASSISTANT_ID`
3. Application automatically connects when you send a message
4. Streaming responses appear in the chat

## Interface Overview

### Header

- **Minerva Logo**: Branding
- **Thread History**: Access via history icon (if available in Agent Chat UI)

### Main Chat Area

- **Message Input**: Type messages at bottom
- **Chat History**: Scrollable message history
- **Agent Responses**: Streaming text responses
- **Tool Calls**: Visual indicators for agent tool usage

### Artifact Panel

- **Side panel**: Appears when agent generates artifacts
- **Artifact rendering**: Displays generated content (code, documents, etc.)

### Thread Management

- **Thread History**: Access previous conversations
- **New Thread**: Start fresh conversation
- **Thread Switching**: Click thread to switch

## Basic Usage

### Sending Messages

1. Type message in input field
2. Press Enter or click Send
3. Message appears in chat
4. Agent processes and responds
5. Response streams in real-time

### Managing Threads

1. Use thread history to see previous conversations
2. Click thread to switch
3. Create new thread for new topics

### Viewing Artifacts

1. Agent may generate artifacts (code, documents, etc.)
2. Artifacts appear in side panel
3. Review and interact with generated content

## Keyboard Shortcuts

- **Enter**: Send message
- **Escape**: Close modals/panels

## Troubleshooting

### Connection Issues

**Can't connect to agent**:
- Verify agent server is running
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Verify `NEXT_PUBLIC_ASSISTANT_ID` matches your graph name

**Connection lost**:
- Application may auto-reconnect
- Check agent server status
- Refresh page if needed

### UI Issues

**Messages not appearing**:
- Check agent is responding
- Verify streaming is working
- Refresh page if needed

**Artifacts not showing**:
- Check agent is generating artifacts
- Verify artifact provider is configured

### Performance

**Slow responses**:
- Check agent server performance
- Verify network connection

**High memory usage**:
- Refresh page to clear state
- Close unused tabs

## Related Documentation

- [Architecture](../architecture/minerva-desktop.md)
- [Setup Guide](../setup/minerva-desktop-setup.md)
- [Upstream Management](../setup/minerva-desktop-upstream.md)
- [Integration Workflows](integration-workflows.md)
