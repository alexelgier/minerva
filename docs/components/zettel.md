# Zettel Agent - Component Overview

> **DEPRECATED.** Quote parsing and concept extraction have been migrated to Temporal workflows in the backend. Use the **Curation UI** (Quotes, Concepts) and **minerva_agent** workflow launcher tools (start_quote_parsing, start_concept_extraction) instead.

The legacy zettel module was a LangGraph-based system for processing book quotes and extracting atomic concepts (Zettels). That behavior is now implemented in:

- **Backend**: `quote_parsing_workflow.py`, `concept_extraction_workflow.py` (Temporal)
- **Curation UI**: Quotes view, Concepts view
- **minerva_agent**: start_quote_parsing, start_concept_extraction tools (HITL)

## Key Features (Current Implementation)

- **Quote Parsing**: Backend Temporal workflow; Curation UI (Quotes) for approval; Neo4j Content, Quote, Person, QUOTED_IN, AUTHORED_BY
- **Concept Extraction**: Backend Temporal workflow; Curation UI (Concepts) for approval; Neo4j Concept, SUPPORTS, concept relations
- **Notifications**: workflow_started, curation_pending, workflow_completed in Curation UI (Notifications)

## Documentation

### Current Implementation

- **[Backend Processing Pipeline](../../backend/docs/architecture/processing-pipeline.md)** - Quote/Concept/Inbox Temporal workflows
- **[Curation API](../../backend/docs/api/endpoints.md)** - quotes, concepts, inbox, notifications endpoints
- **[Architecture Overview](../architecture/zettel.md)** - Deprecation notice and migrated behavior
- **[Usage Guide](../usage/zettel.md)** - How to use via Curation UI and minerva_agent

### Legacy Module (Reference Only)

- **[Module README](../../backend/zettel/README.md)** - Deprecation notice at top
- **[Setup Guide](../setup/zettel-setup.md)** - Legacy setup (deprecated)

## Quick Links

- [Module Documentation Index](../../backend/zettel/docs/README.md)
- [Module README](../../backend/zettel/README.md)
- [Setup Guide](../setup/zettel-setup.md)
- [Usage Guide](../usage/zettel.md)
- [Architecture Overview](../architecture/zettel.md)

