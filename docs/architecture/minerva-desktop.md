# Minerva Desktop Architecture

Minerva Desktop is a native desktop application built with Tauri and Next.js, providing a modern UI for interacting with LangGraph deep agents.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Tauri Native Shell                         │
│  - System Tray                                          │
│  - Window Management                                    │
│  - Native APIs                                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              Next.js Application                        │
│  - React 19 Components                                  │
│  - App Router                                           │
│  - Server/Client Components                              │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────┐
│              LangGraph SDK Client                       │
│  - WebSocket Streaming                                  │
│  - REST API Calls                                       │
│  - Thread Management                                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
            LangGraph Server
```

## Technology Stack

### Frontend
- **Next.js 15**: React framework with App Router
- **React 19**: UI library with latest features
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **SCSS Modules**: Component-scoped styles

### Desktop
- **Tauri 2**: Native desktop wrapper
- **Rust**: System-level integration
- **System Tray**: Background operation support

### Communication
- **LangGraph SDK**: Agent communication library
- **WebSocket**: Real-time streaming
- **REST API**: Thread and state management

## Component Structure

### App Directory (`src/app/`)

```
app/
├── components/
│   ├── ChatInterface/      # Main chat UI
│   ├── ChatMessage/        # Message rendering
│   ├── FileViewDialog/      # File viewer modal
│   ├── SubAgentIndicator/  # Subagent status
│   ├── SubAgentPanel/      # Subagent details
│   ├── TasksFilesSidebar/  # Tasks and files list
│   └── ThreadHistorySidebar/ # Thread management
├── hooks/
│   └── useChat.ts          # Chat state management
├── types/
│   └── types.ts             # TypeScript definitions
└── page.tsx                 # Main page component
```

### Shared Components (`src/components/ui/`)

- **Button**: Accessible button component
- **Dialog**: Modal dialogs
- **Input**: Form inputs
- **ScrollArea**: Custom scrollbars
- **Tabs**: Tab navigation
- **Tooltip**: Tooltip component

### Libraries (`src/lib/`)

- **client.ts**: LangGraph SDK client factory
- **environment/deployments.ts**: Deployment configuration
- **utils.ts**: Utility functions

### Providers (`src/providers/`)

- **Auth.tsx**: Authentication context (LangSmith API key)

## State Management

### Chat State
- Managed via `useChat` hook
- Uses LangGraph SDK's `useStream` for real-time updates
- Thread state persisted in URL query parameters

### Component State
- React `useState` for local component state
- Context providers for global state (Auth)
- URL state for thread management (nuqs)

## Data Flow

### Message Sending
```
User Input → ChatInterface → useChat → LangGraph SDK → Agent Server
```

### Message Receiving
```
Agent Server → LangGraph SDK (WebSocket) → useChat → ChatInterface → UI Update
```

### State Updates
```
Agent State → SDK Stream → handleUpdateEvent → Component State → UI
```

## Key Features

### Real-Time Streaming
- WebSocket connection to LangGraph server
- Optimistic UI updates
- Automatic reconnection

### Thread Management
- Thread IDs stored in URL
- Thread history sidebar
- New thread creation

### Task Tracking
- Tasks extracted from agent state
- Sidebar display
- Real-time updates

### File Operations
- Files tracked from agent state
- File viewer dialog
- Content display with syntax highlighting

### Subagent Monitoring
- Subagent activity tracking
- Dedicated panel for subagent details
- Visual indicators

## Tauri Integration

### System Tray
- Minimize to tray
- Quick access menu
- Show/hide window

### Window Management
- Custom window configuration
- Initial visibility control
- Resizable windows

### Build Process
- Next.js build → `out/` directory
- Tauri bundles Next.js output
- Native executable generation

## Environment Configuration

### Development
```env
NEXT_PUBLIC_DEPLOYMENT_URL="http://127.0.0.1:2024"
NEXT_PUBLIC_AGENT_ID="minerva_agent"
NEXT_PUBLIC_LANGSMITH_API_KEY="optional-for-local"
```

### Production
```env
NEXT_PUBLIC_DEPLOYMENT_URL="https://your-deployment-url"
NEXT_PUBLIC_AGENT_ID="your-agent-id"
NEXT_PUBLIC_LANGSMITH_API_KEY="required-for-production"
```

## Development Workflow

1. **Next.js Development**: `npm run dev` (web only)
2. **Tauri Development**: `npm run tauri:dev` (full desktop app)
3. **Build**: `npm run tauri:build` (production bundle)

## Styling Architecture

- **Tailwind CSS**: Global utility classes
- **SCSS Modules**: Component-specific styles
- **CSS Variables**: Theme customization
- **Radix UI**: Accessible component primitives

## Performance Considerations

- **Code Splitting**: Next.js automatic code splitting
- **Lazy Loading**: Components loaded on demand
- **Optimistic Updates**: Immediate UI feedback
- **Streaming**: Incremental message rendering

## Security

- **CSP**: Content Security Policy via Tauri
- **Environment Variables**: Client-side only for public vars
- **API Keys**: Stored in environment, not in code
- **Path Sandboxing**: Tauri security model

## Related Documentation

- [Components Overview](components.md)
- [Setup Guide](../setup/minerva-desktop-setup.md)
- [Usage Guide](../usage/minerva-desktop.md)
- [minerva-desktop README](../../minerva-desktop/README.md)

