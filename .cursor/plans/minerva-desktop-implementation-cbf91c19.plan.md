<!-- cbf91c19-ce9d-4c47-81ac-21e0be811caa 78c6ea6c-9b64-4a98-a545-a6b13d93f5c3 -->
# Minerva Desktop Implementation Plan

## Project Structure

Create a new desktop application at `minerva-desktop/` with:

- Tauri shell (Rust)
- React + Vite frontend
- JSONL IPC protocol over stdin/stdout
- Integration with new LangGraph agent in `backend/minerva_agent/`

## Directory Structure

```
minerva-desktop/
├── src/                    # React UI
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/
│   │   ├── SidePanel.tsx
│   │   ├── Composer.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageItem.tsx
│   │   ├── ActionModal.tsx
│   │   └── TypingIndicator.tsx
│   ├── hooks/
│   │   └── useAgentStream.ts
│   └── styles/
│       └── theme.css
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   ├── agent_bridge.rs
│   │   ├── hotkey.rs
│   │   └── tray.rs
│   └── tauri.conf.json
├── dev-scripts/
│   ├── test_agent.py
│   └── run-local.ps1
├── Cargo.toml
├── package.json
└── README.md
```

## Visual Style

Maintain existing Minerva frontend aesthetic:

- Dark theme base: `#4c4f52`
- Accent color: `#9eb0c2`
- Glassmorphism: `rgba(69, 76, 82, 0.3)` backgrounds with `backdrop-filter: blur(10px)`
- Scrollbar: thin, `rgba(158, 176, 194, 0.6)`
- Text: `rgb(211, 211, 211)`

## Implementation Phases

### Phase 0: Project Setup

- Initialize Tauri + React + Vite project in `minerva-desktop/`
- Configure dependencies: react-markdown, react-syntax-highlighter, uuid, react-virtual (virtualization)
- Set up Tailwind CSS or equivalent for styling
- Configure build tooling
- Install Tauri plugins: global-shortcut, tray, shell

### Phase 1: LangGraph Agent (`backend/minerva_agent/`)

- Create new Poetry project in `backend/minerva_agent/`
- Implement simple chat agent using LangGraph 1.0.0 patterns
- Add streaming support using LangGraph's streaming capabilities
- Add JSONL stdin/stdout IO wrapper with error handling
- Support message types: user_message, response_chunk, response_done, action_proposal, error
- Add checkpoint/persistence for conversation state (optional, for Phase 6)
- Create test agent script for development with simulated streaming

### Phase 2: Tauri Shell

- Implement `agent_bridge.rs`: spawn Python subprocess, manage stdin/stdout with tokio
- Parse JSONL from Python agent with error handling and validation
- Emit Tauri events: `agent:chunk`, `agent:done`, `agent:action`, `agent:error`, `history:page`
- Add process lifecycle management: auto-restart on crash, cleanup on exit
- Configure Tauri plugins: `tauri-plugin-global-shortcut` for `Ctrl+Alt+M` hotkey
- Configure Tauri plugins: `tauri-plugin-tray` for system tray with show/hide
- Configure window: side panel style, always on top when visible, transparent/rounded corners
- Add error recovery: handle Python path resolution, validate subprocess communication

### Phase 3: React UI Foundation

- Create `SidePanel.tsx`: main container with slide-in animation
- Create `Composer.tsx`: message input with send button
- Create `MessageList.tsx`: container with virtualization support (react-virtual)
- Create `MessageItem.tsx`: markdown rendering, code highlighting, copy button
- Implement `useAgentStream.ts`: hook to listen to Tauri events and manage state
- Add error boundaries for UI error handling
- Apply visual theme matching existing frontend
- Set up state management (Context API or zustand) for chat state

### Phase 4: Chat & Streaming

- Implement streaming response handling: accumulate chunks, update UI in real-time
- Add typing indicator component
- Implement infinite scroll history loading (50 messages at a time)
- Add message persistence (localStorage for UI state only, not agent memory)
- Handle message rendering: markdown, code blocks, images

### Phase 5: Actions & Confirmations

- Create `ActionModal.tsx`: display action proposals with approve/deny buttons
- Send confirmations back to Python agent via Tauri invoke commands
- Handle action success/error states
- Display action results in chat

### Phase 6: Polish & Integration

- Implement tray behavior: minimize to tray, close to tray
- Persist UI preferences: window size, position, theme
- Add comprehensive error handling and reconnection logic
- Implement agent process auto-restart on crash
- Add input validation and sanitization for security
- Replace test agent with real `backend/minerva_agent/`
- Test full integration end-to-end
- Add logging/debugging tools for development
- Build Windows installer configuration (optional)

## Technical Details

### JSONL Protocol

Messages are newline-delimited JSON:

- **UI → Python**: `{"id": "uuid", "type": "user_message", "text": "...", "meta": {...}}`
- **Python → UI**: `{"id": "uuid", "type": "response_chunk", "chunk": "..."}`
- Actions: `{"type": "action_proposal", "action_id": "...", "label": "...", "desc": "...", "params": {...}}`

### Tauri Events

- `agent:chunk` - streaming response chunk
- `agent:done` - response complete
- `agent:action` - action proposal from agent
- `agent:error` - error from agent or bridge
- `history:page` - paginated history messages

### Error Handling

- Rust: Validate all JSON from Python, handle subprocess crashes gracefully
- React: Error boundaries around components, user-friendly error messages
- IPC: Retry logic for failed messages, timeout handling for unresponsive agent

### Rust Dependencies

- `tauri` - core framework
- `serde_json` - JSON parsing
- `tokio` - async runtime for subprocess management
- `anyhow` / `thiserror` - error handling
- `tauri-plugin-global-shortcut` - official global hotkey support
- `tauri-plugin-tray` - official system tray support
- `tauri-plugin-shell` - process management

### React Dependencies

- `react-markdown` - markdown rendering
- `react-syntax-highlighter` - code highlighting
- `react-virtual` - virtualization (lighter alternative to react-window)
- `uuid` - message IDs
- `@tauri-apps/api` - Tauri core bindings
- `@tauri-apps/plugin-global-shortcut` - frontend hotkey integration
- `@tauri-apps/plugin-tray` - frontend tray integration
- `zustand` (optional) - lightweight state management for chat history