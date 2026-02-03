# Minerva Desktop Architecture

Minerva Desktop is a Next.js application (optionally wrapped with Tauri for native desktop) providing a modern UI for interacting with LangGraph agents. It uses [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) as the base, with Minerva-specific styling applied on top. See [upstream management](../setup/minerva-desktop-upstream.md) for how we track upstream updates.

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

Based on Agent Chat UI with Minerva customizations:

```
app/
├── api/
│   └── [..._path]/         # API passthrough routes
├── globals.css             # Global styles + Minerva customizations
├── layout.tsx              # Root layout
└── page.tsx                # Main page (Minerva header wrapper)
```

### Components (`src/components/`)

```
components/
├── thread/                 # Chat thread components
│   ├── artifact.tsx        # Artifact side panel
│   ├── history/            # Thread history
│   ├── messages/           # Message rendering (AI, human, tools)
│   └── index.tsx           # Main Thread component
├── ui/                     # Shared UI components (button, input, etc.)
└── icons/                  # Icon components
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
- Streaming message updates
- Automatic reconnection

### Thread Management
- Thread IDs stored in URL
- Thread history sidebar
- New thread creation

### Artifact Rendering
- Side panel for generated content
- Supports custom artifact components

### Minerva Branding
- Custom header with logo
- Background styling
- Color theme customization

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
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent
```

### Production (API Passthrough)
```env
NEXT_PUBLIC_API_URL=https://your-site.com/api
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent
LANGGRAPH_API_URL=https://my-agent.default.us.langgraph.app
LANGSMITH_API_KEY=lsv2_...  # Server-side only
```

See [upstream management](../setup/minerva-desktop-upstream.md) for production deployment details.

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

