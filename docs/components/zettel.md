# Zettel Agent - Component Overview

zettel is a LangGraph-based agent system for processing book quotes and extracting atomic concepts (Zettels) using Zettelkasten methodology.

## Key Features

- **Quote Parsing**: Extract quotes from markdown book notes with section and page references
- **Concept Extraction**: Generate atomic concepts (Zettels) from related quotes using vector search and LLM analysis
- **3-Phase Workflow**: LLM self-improvement loop, human-in-the-loop review, and database commit
- **User Suggestions**: Optional freeform text input to guide the extraction process
- **Duplicate Detection**: Semantic similarity search to avoid duplicate concepts
- **Relation Discovery**: Automatic detection of concept relationships
- **Neo4j Integration**: Graph database with vector indexes for semantic search
- **Obsidian Integration**: Automatic generation of Zettel markdown files

## Documentation

### Comprehensive Module Documentation

The zettel module now has comprehensive documentation in `backend/zettel/docs/`:

- **[API Reference](../../backend/zettel/docs/API.md)** - Complete API reference for all functions and classes
- **[Architecture Documentation](../../backend/zettel/docs/ARCHITECTURE.md)** - Deep technical architecture details
- **[Developer Guide](../../backend/zettel/docs/DEVELOPER.md)** - Guide for extending and modifying the module
- **[Workflows Documentation](../../backend/zettel/docs/WORKFLOWS.md)** - Detailed workflow documentation

### Project-Level Documentation

- **[Setup Guide](../setup/zettel-setup.md)** - Setup instructions
- **[Usage Guide](../usage/zettel.md)** - Usage examples and patterns
- **[Architecture Overview](../architecture/zettel.md)** - High-level architecture
- **[Module README](../../backend/zettel/README.md)** - Module overview and quick start

## Quick Links

- [Module Documentation Index](../../backend/zettel/docs/README.md)
- [Module README](../../backend/zettel/README.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Usage Guide](../usage/zettel.md)
- [Architecture Overview](../architecture/zettel.md)

