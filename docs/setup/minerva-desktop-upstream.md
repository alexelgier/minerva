# Minerva Frontend: Agent Chat UI

Minerva uses LangChain's Agent Chat UI for real-time chat with LangGraph agents.

| Project | Purpose | Upstream |
|---------|---------|----------|
| **Agent Chat UI** | Real-time chat interface for LangGraph agents | [langchain-ai/agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui) |

A Next.js app that connects to any LangGraph deployment. Run locally or integrate into Minerva with customizations.

---

## Current state

**Status:** Migration complete. `minerva-desktop/` now uses **Agent Chat UI** (langchain-ai/agent-chat-ui) via **git subtree**.

**What changed:**
- Replaced the old deepagent-ui copy with Agent Chat UI
- Added `agent-chat-ui` as a git remote
- Minerva styling (header, background, colors) applied on top
- Tied to upstream via subtree for easy updates
- Tauri integration added for native desktop app

**Key files customized:**
- `src/app/page.tsx` - Minerva header wrapper
- `src/app/globals.css` - Minerva color variables and container styles
- `public/assets/` - `MinervaLogo.png`, `relief.png`
- `src-tauri/` - Tauri desktop wrapper (not from upstream)

---

## Overview

A chat interface for interacting with LangGraph agents via a `messages` key. Features:
- Real-time streaming chat
- Artifact rendering (side panel for generated content)
- Message visibility control (`langsmith:nostream`, `do-not-render-` prefix)
- Production-ready with API passthrough

---

## Minerva styling

Minerva customizations applied on top of Agent Chat UI:

1. **Header** – Fixed header above the chat in `page.tsx`:
   - Logo: `/assets/MinervaLogo.png`
   - Styles: dark bar (`#222325`), `box-shadow: 0 4px 6px rgba(0,0,0,0.5)`, 60px height

2. **Page background** – Container in `page.tsx` with:
   - `background-color: #4c4f52`
   - `background-image: url('/assets/relief.png')`
   - `background-size: cover`

3. **Colors** – Added to `globals.css`:
   - Minerva color variables (`--minerva-color-*`)
   - Light and dark mode support

4. **Assets** – In `public/assets/`:
   - `MinervaLogo.png`
   - `relief.png`

When running `git subtree pull`, resolve conflicts in `page.tsx` and `globals.css` if upstream changed them.

---

## Local Development Setup

The UI lives under `minerva-desktop/` in the Minerva repo. Install and run from there:

```bash
cd minerva-desktop
npm install  # or pnpm install

# Configure (copy .env.example to .env)
NEXT_PUBLIC_API_URL=http://localhost:2024
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent

# Run (web only)
npm run dev
# Available at http://localhost:3000
```

---

## Tauri Desktop App

Tauri wraps the Next.js app in a native desktop window.

### Prerequisites

- Rust and Cargo installed ([rustup.rs](https://rustup.rs))
- Platform-specific requirements:
  - **Windows**: Microsoft Visual C++ Build Tools, WebView2 Runtime
  - **macOS**: Xcode Command Line Tools (`xcode-select --install`)
  - **Linux**: See [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/)

### Development

```bash
cd minerva-desktop
npm run tauri:dev
```

This starts the Next.js dev server and opens a native window with hot reload.

### Production Build

```bash
npm run tauri:build
```

Creates distributable installers in `src-tauri/target/release/bundle/`.

**Note:** Production builds require static export. See `next.config.mjs` comments for instructions (remove API routes, enable `output: "export"`). For desktop use, set `NEXT_PUBLIC_API_URL` directly to your LangGraph server.

### Tauri Configuration

- `src-tauri/tauri.conf.json` - Window settings, app name, bundle config
- `src-tauri/Cargo.toml` - Rust dependencies
- `src-tauri/src/lib.rs` - System tray implementation (minimize to tray, menu)

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

**We use API Passthrough.** The browser talks to your Next.js server (e.g. `your-site.com/api`); the server holds the LangSmith API key and forwards requests to LangGraph Cloud. LangGraph sees one identity (your app). The key never goes to the browser.

### API Passthrough (our setup)

Your Next.js app includes a **server-side proxy** (e.g. [langgraph-nextjs-api-passthrough](https://github.com/bracesproul/langgraph-nextjs-api-passthrough)). The frontend calls your own API; the Next.js server forwards to LangGraph Cloud and **injects** `LANGSMITH_API_KEY` on the server.

```env
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent
LANGGRAPH_API_URL=https://my-agent.default.us.langgraph.app
NEXT_PUBLIC_API_URL=https://my-website.com/api
LANGSMITH_API_KEY=lsv2_...  # Server-side only, no NEXT_PUBLIC_ prefix
```

If you later need per-user identity (e.g. "user A only sees their threads"), you can switch to [Custom Auth](https://langchain-ai.github.io/langgraph/how-tos/auth/custom_auth/) on the deployment and pass a user token in `defaultHeaders`.

---

## Upstream Management (subtree)

We use **subtree** so the UI lives in one Minerva repo and we can pull updates from the original agent-chat-ui.

### What "upstream" means

- **origin** = the Minerva repo (where you push).
- **upstream** = the original `langchain-ai/agent-chat-ui`; you only **pull** from it.

You add their repo as a remote and run `git subtree pull` to merge their `main` into `minerva-desktop/`. You never push to upstream.

### Pulling upstream updates

When you want the latest from agent-chat-ui:

```bash
# From Minerva repo root
git subtree pull --prefix=minerva-desktop agent-chat-ui main
```

Resolve any merge conflicts (usually in your customized files: `page.tsx`, `globals.css`). Keep customizations to a few files so pulls stay manageable.

### Trade-offs

| Pros | Cons |
|------|------|
| One repo, one clone; no submodules. | Conflicts when both you and upstream change the same file; resolve in Minerva. |
| No submodule pointer or nested-repo workflow. | Run `git subtree pull` manually when you want updates. |

---

## Related

- [minerva-desktop setup](minerva-desktop-setup.md)
- [minerva-desktop architecture](../architecture/minerva-desktop.md)
- Upstream: [agent-chat-ui](https://github.com/langchain-ai/agent-chat-ui)
