# Minerva Agent - Detailed Documentation

See [Architecture Documentation](../architecture/minerva-agent.md) for technical details.

This document provides comprehensive information about the minerva_agent LangGraph agent.

## Overview

minerva_agent is a LangGraph agent (LangChain 1.x) that provides read-only Obsidian vault access and launches Temporal workflows (quote parsing, concept extraction, inbox classification) with mandatory human-in-the-loop (HITL) confirmation. Irreversible actions are performed by backend workflows after curation in the Curation UI.

## Key Features

- Read-only vault tools (read_file, list_dir, glob, grep) sandboxed to OBSIDIAN_VAULT_PATH
- Workflow launcher tools (start_quote_parsing, start_concept_extraction, start_inbox_classification, get_workflow_status) with HITL
- Bilingual support (Spanish/English)
- No direct file writes; workflow steps approved in Curation UI (Quotes, Concepts, Inbox)

## Quick Links

- [Setup Guide](../setup/minerva-agent-setup.md)
- [Usage Guide](../usage/minerva-agent.md)
- [Architecture](../architecture/minerva-agent.md)
- [README](../../backend/minerva_agent/README.md)

