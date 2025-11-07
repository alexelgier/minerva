# Minerva Agent

A deep agent for Obsidian vault assistance built with LangChain's deepagents package.

## Features

- **File System Operations**: Read, write, and edit markdown files in your Obsidian vault
- **Search & Discovery**: Find files using glob patterns and search content with grep
- **Task Planning**: Break down complex tasks into manageable steps
- **Subagents**: Delegate specialized work to subagents for context isolation
- **Google Gemini**: Powered by Gemini 2.5 Flash for fast, efficient responses

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set up environment variables:
   - Create a `.env` file in this directory
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your-api-key-here
     ```
   - Optionally override the vault path (defaults to `D:\yo`):
     ```
     OBSIDIAN_VAULT_PATH=D:\your\vault\path
     ```

## Running the Agent

### Development Server

Start the development server:
```bash
poetry run langgraph dev
```

This will start a local server that you can interact with via the LangGraph Studio or API.

### Production Deployment

Build and deploy using LangGraph CLI:
```bash
poetry run langgraph up
```

## Usage

The agent provides the following capabilities:

- **File Reading**: Read markdown files with support for line ranges
- **File Writing**: Create new markdown files
- **File Editing**: Edit existing files with precise string replacements
- **Directory Listing**: List files and directories with metadata
- **Pattern Matching**: Find files using glob patterns
- **Content Search**: Search file contents with grep
- **Task Management**: Plan and track complex multi-step operations
- **Subagent Delegation**: Spawn specialized subagents for isolated tasks

## Configuration

The agent is configured via `langgraph.json`. The main graph is exported from `src/minerva_agent/agent.py`.

## Architecture

- Built on LangGraph for stateful, durable execution
- Uses deepagents for planning, filesystem, and subagent capabilities
- Integrates with Google Gemini 2.5 Flash for LLM interactions
- FilesystemBackend provides direct access to your Obsidian vault

