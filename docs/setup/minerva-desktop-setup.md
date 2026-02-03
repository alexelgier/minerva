# Minerva Desktop Setup Guide

Detailed setup instructions for the Minerva Desktop application.

**Note:** `minerva-desktop/` now uses [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) via git subtree. See [minerva-desktop-upstream.md](minerva-desktop-upstream.md) for upstream management.

## Prerequisites

- Node.js 18+ and npm (or pnpm)
- Rust and Cargo (for Tauri desktop builds)
- Tauri prerequisites (platform-specific, optional for web-only dev)

## Installation

### 1. Install Node Dependencies

```bash
cd minerva-desktop
npm install
```

### 2. Install Tauri Prerequisites

#### Windows
- Microsoft Visual C++ Build Tools
- WebView2 Runtime (usually pre-installed with Windows 11)

#### macOS
```bash
xcode-select --install
```

#### Linux
```bash
sudo apt update
sudo apt install libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

### 3. Verify Rust Installation

```bash
rustc --version
cargo --version
```

If not installed, see [Rust Installation Guide](https://www.rust-lang.org/tools/install).

## Configuration

### Environment Variables

Create `.env` in `minerva-desktop/` (copy from `.env.example`):

```env
# Required: LangGraph server URL
NEXT_PUBLIC_API_URL=http://localhost:2024

# Required: Graph/assistant ID from langgraph.json
NEXT_PUBLIC_ASSISTANT_ID=minerva_agent

# Optional: LangSmith API key (for production, server-side only)
LANGSMITH_API_KEY=
```

See [minerva-desktop-upstream.md](minerva-desktop-upstream.md) for production deployment with API passthrough.

## Development

### Run with Tauri (Recommended)

```bash
npm run tauri:dev
```

This:
- Starts Next.js dev server
- Builds Tauri app
- Opens native window
- Enables hot reload

### Run Next.js Only

```bash
npm run dev
```

Access at `http://localhost:3000` (no native features).

### Tauri Commands

```bash
# Development
npm run tauri:dev

# Build production app
npm run tauri:build

# Tauri CLI directly
npm run tauri -- <command>
```

## Building

### Development Build

```bash
npm run tauri:build
```

Output: `src-tauri/target/debug/minerva-desktop`

### Production Build

```bash
npm run tauri:build -- --release
```

Output: `src-tauri/target/release/minerva-desktop`

### Platform-Specific Builds

```bash
# Windows
npm run tauri:build -- --target x86_64-pc-windows-msvc

# macOS
npm run tauri:build -- --target aarch64-apple-darwin

# Linux
npm run tauri:build -- --target x86_64-unknown-linux-gnu
```

## Configuration Files

### Tauri Configuration

`src-tauri/tauri.conf.json`:
- Window settings
- Build configuration
- Security settings
- Bundle settings

### Next.js Configuration

`next.config.ts`:
- Build settings
- Output configuration

### TypeScript Configuration

`tsconfig.json`:
- Type checking rules
- Path aliases

## Troubleshooting

### Build Errors

**Rust not found**:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**Tauri CLI missing**:
```bash
npm install -g @tauri-apps/cli
```

**WebView2 missing (Windows)**:
Download from [Microsoft](https://developer.microsoft.com/microsoft-edge/webview2/)

### Runtime Errors

**Connection refused**:
- Verify LangGraph server is running
- Check `NEXT_PUBLIC_API_URL` matches server URL
- Verify firewall settings

**Agent not found**:
- Check `NEXT_PUBLIC_ASSISTANT_ID` matches graph name in langgraph.json
- Verify agent server is running

**Authentication errors**:
- For production: Set `LANGSMITH_API_KEY` (server-side) and use API passthrough
- For local: Usually not required

### Performance Issues

**Slow builds**:
- Use `npm run dev` for faster iteration
- Only use `tauri:dev` when testing native features

**Large bundle size**:
- Check Next.js build output
- Review included dependencies
- Use production build optimizations

## System Tray

The app includes system tray functionality:
- **Minimize to tray**: Closing the window hides it to tray instead of quitting
- **Left-click tray icon**: Shows and focuses the window
- **Right-click menu**: Show/Hide toggle and Quit option
- **Tooltip**: Shows "Minerva" on hover

Configure in `src-tauri/src/lib.rs`.

## Security

### Content Security Policy

Configured in `tauri.conf.json`:
```json
{
  "app": {
    "security": {
      "csp": null  // Configure as needed
    }
  }
}
```

### Environment Variables

- Only `NEXT_PUBLIC_*` variables are exposed to client
- Never put secrets in environment variables
- Use Tauri commands for secure operations

## Distribution

### Windows

Creates `.msi` installer in `src-tauri/target/release/bundle/msi/`

### macOS

Creates `.dmg` in `src-tauri/target/release/bundle/dmg/`

### Linux

Creates `.deb` and `.AppImage` in `src-tauri/target/release/bundle/`

## Related Documentation

- [Architecture](../architecture/minerva-desktop.md)
- [Usage Guide](../usage/minerva-desktop.md)
- [Quick Start](quick-start.md)

