# Minerva Frontend: Agent Chat UI

Minerva uses LangChain's Agent Chat UI for real-time chat with LangGraph agents.

| Project | Purpose | Upstream |
|---------|---------|----------|
| **Agent Chat UI** | Real-time chat interface for LangGraph agents | [langchain-ai/agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) |

A Next.js app that connects to any LangGraph deployment. Run locally or integrate into Minerva with customizations.

---

## Overview

A chat interface for interacting with LangGraph agents via a `messages` key. Features:
- Real-time streaming chat
- Artifact rendering (side panel for generated content)
- Message visibility control (`langsmith:nostream`, `do-not-render-` prefix)
- Production-ready with API passthrough or custom auth

---

## Local Development Setup

```bash
# Clone and install
git clone https://github.com/langchain-ai/agent-chat-ui.git
cd agent-chat-ui
pnpm install

# Configure (copy .env.example to .env)
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=agent

# Run
pnpm dev
# Available at http://localhost:3000
```

Or use npx:
```bash
npx create-agent-chat-app
```

---

## Backend Integration

### Connecting to Minerva Backend

```env
NEXT_PUBLIC_API_URL=http://localhost:2024  # or your Minerva LangGraph URL
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent     # your graph name
```

### Hiding Messages

Control message visibility in the chat:

```python
from langchain_anthropic import ChatAnthropic

# Prevent live streaming (message appears after completion)
model = ChatAnthropic().with_config(
    config={"tags": ["langsmith:nostream"]}
)

# Hide message permanently (never rendered)
result = model.invoke([messages])
result.id = f"do-not-render-{result.id}"
return {"messages": [result]}
```

---

## Production Deployment

### Option 1: API Passthrough (recommended)

Uses a server-side proxy to inject the LangSmith API key:

```env
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent
LANGGRAPH_API_URL=https://my-agent.default.us.langgraph.app
NEXT_PUBLIC_API_URL=https://my-website.com/api
LANGSMITH_API_KEY=lsv2_...  # Server-side only, no NEXT_PUBLIC_ prefix
```

### Option 2: Custom Authentication

Configure [LangGraph custom auth](https://langchain-ai.github.io/langgraph/concepts/auth/) on your deployment, then pass tokens in `defaultHeaders`:

```typescript
const streamValue = useTypedStream({
  apiUrl: process.env.NEXT_PUBLIC_API_URL,
  assistantId: process.env.NEXT_PUBLIC_ASSISTANT_ID,
  defaultHeaders: {
    Authentication: `Bearer ${yourToken}`,
  },
});
```

---

## Upstream Management

Choose how to track upstream changes:

### Option A: Fork + Submodule (recommended)

Best for maintaining Minerva-specific customizations while pulling upstream updates.

```bash
# 1. Fork the repo on GitHub (e.g., to alexelgier/agent-chat-ui)

# 2. In your fork, add upstream remote
cd agent-chat-ui-fork
git remote add upstream https://github.com/langchain-ai/agent-chat-ui.git

# 3. Add fork as submodule in Minerva
cd /path/to/Minerva
git submodule add https://github.com/alexelgier/agent-chat-ui.git minerva-chat-ui

# 4. To update from upstream later
cd minerva-chat-ui
git fetch upstream && git merge upstream/main
# Resolve conflicts, push to fork
cd ..
git add minerva-chat-ui && git commit -m "Update agent-chat-ui from upstream"
```

**Pros:** Real git tie; easy upstream pulls; customizations in fork.  
**Cons:** Submodule workflow; clones need `git submodule update --init --recursive`.

### Option B: Subtree (single repo)

Keep everything in one repo with subtree merging:

```bash
# Add remote
git remote add agent-chat-ui https://github.com/langchain-ai/agent-chat-ui.git

# Add as subtree
git subtree add --prefix=minerva-chat-ui agent-chat-ui main

# Update from upstream
git subtree pull --prefix=minerva-chat-ui agent-chat-ui main
```

**Pros:** Single repo; no submodule complexity.  
**Cons:** Potential merge conflicts on customized files.

---

## Comparison

| Approach | Location | Customizable? | Maintenance |
|----------|----------|---------------|-------------|
| Fork + submodule | Submodule in Minerva | Yes | Low |
| Subtree | Directory in Minerva | Yes | Low |
| Deploy your own | Your Vercel/server | Yes | Medium |

---

## Recommendation

1. **Fork + submodule** when you need Minerva branding, custom defaults, or additional features.
2. **Subtree** if you prefer a single repo and one clone.
3. **Deploy your own** (Vercel, etc.) when you want hosted convenience with your customizations baked in.

---

## Related

- [minerva-desktop setup](minerva-desktop-setup.md)
- [minerva-desktop architecture](../architecture/minerva-desktop.md)
- Upstream: [agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui)
