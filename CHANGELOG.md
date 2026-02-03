# Changelog

All notable changes to the Minerva project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-02-03

### Added
- **Backend — Quote Parsing Workflow**: Temporal `QuoteParsingWorkflow`; parse markdown quotes, submit to curation DB, wait for approval, write Content/Quote/Person and QUOTED_IN/AUTHORED_BY to Neo4j. Emits notifications (workflow_started, curation_pending, workflow_completed).
- **Backend — Concept Extraction Workflow**: Temporal `ConceptExtractionWorkflow`; load content/quotes from Neo4j, LLM extract concepts/relations, submit to curation DB, wait for approval, write Concept nodes and SUPPORTS/relations to Neo4j. Emits notifications.
- **Backend — Inbox Classification Workflow**: Temporal `InboxClassificationWorkflow`; scan inbox, LLM suggest target folder per note, submit to curation DB, wait for approval, execute file moves. Emits notifications.
- **Curation DB**: New tables `quote_workflow_curation`, `quote_curation_items`, `concept_workflow_curation`, `concept_curation_items`, `concept_relation_curation_items`, `inbox_classification_items`, `notifications`. CurationManager methods for all of the above and for create/list/mark-read/dismiss notifications.
- **Curation API**: Endpoints for quote curation (`/api/curation/quotes/*`), concept curation (`/api/curation/concepts/*`), inbox curation (`/api/curation/inbox/*`), notifications (`/api/curation/notifications`, `.../read`, `.../dismiss`).
- **Curation UI (Vue.js)**: New routes and views — `/quotes` (QuoteCurationView), `/concepts` (ConceptCurationView), `/inbox` (InboxCurationView), `/notifications` (NotificationsView). Header nav: Queue, Quotes, Concepts, Inbox, Notifications (with unread badge).
- **minerva_agent**: Read-only tools (`read_file`, `list_dir`, `glob`, `grep`) sandboxed to `OBSIDIAN_VAULT_PATH`; workflow launcher tools (`start_quote_parsing`, `start_concept_extraction`, `start_inbox_classification`, `get_workflow_status`) with mandatory HITL (HumanInTheLoopMiddleware). Agent no longer performs direct file writes; irreversible actions are done by backend Temporal workflows after curation.

### Changed
- **minerva_agent**: Migrated from `deepagents.create_deep_agent` to LangChain 1.x `create_agent`; removed deepagents and FilesystemBackend write tools. Workflow launches require user confirmation in chat (HITL).
- **Backend**: All new workflows and activities registered in `temporal_orchestrator.py` (QuoteParsing, ConceptExtraction, InboxClassification).
- **Documentation**: Updated `backend/docs` (architecture overview, processing pipeline, database schema, API endpoints) and `docs` (architecture/components, minerva-agent, zettel; setup zettel-setup; usage overview, zettel, integration-workflows; components minerva-agent, zettel; PROJECT_OVERVIEW_V3) to describe Temporal quote/concept/inbox workflows, notifications, Curation UI, and minerva_agent refactor.
- **Version**: Bumped all project versions to 0.4.0 (root `pyproject.toml`, backend, minerva_agent, zettel, minerva-models, minerva-desktop Cargo.toml and package.json). Subprojects follow the workspace release version.

### Deprecated
- **zettel** (`backend/zettel/`): Quote parsing and concept extraction have been migrated to backend Temporal workflows. Use Curation UI (Quotes, Concepts) and minerva_agent workflow launcher tools instead. Deprecation notice added to `backend/zettel/README.md` and relevant docs; folder kept for reference.

## [0.3.0] - 2026-02-02

### Added
- **minerva-desktop**: Migrated from deepagent-ui to [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui) via git subtree; minerva-desktop updatable with `git subtree pull --prefix=minerva-desktop agent-chat-ui main`.
- **minerva-desktop**: Re-initialized Tauri; system tray (minimize to tray, Show/Hide, Quit, tooltip). Run with `npm run tauri:dev` or `npm run tauri:build`.
- **Documentation**: [docs/setup/minerva-desktop-upstream.md](docs/setup/minerva-desktop-upstream.md) for subtree, styling, Tauri, production; setup/architecture/components/usage docs aligned.

### Changed
- **minerva-desktop**: Preserved Minerva styling (header, background, colors) on Agent Chat UI base; key files: `src/app/page.tsx`, `src/app/globals.css`, `public/assets/`.
- **Backend**: Graph repositories and journal-entry repository now import entities from `minerva_models` instead of removed `minerva_backend.graph.models.entities` (fixes startup `ModuleNotFoundError`).
- **Backend**: Clearer error when Temporal Server is not running: actionable message suggesting `temporal server start-dev` or `start-minerva.ps1`.
- **Backend**: Ollama Python client updated from 0.1.9 to 0.6.1 (`backend/pyproject.toml`).

## [0.2.0] - 2025-11-XX

### 🎉 Milestone: Minerva is Now Usable!

**For the first time, Minerva is fully functional and usable end-to-end!** With minerva-desktop and minerva-agent working together, users can now:
- Launch the desktop application and connect to the agent
- Interact with minerva-agent through a native chat interface
- Perform Obsidian vault operations (read, write, edit files)
- Execute complex tasks with agent assistance
- Monitor agent activities and subagent delegation

While functionality is still limited and many features are in development, this release marks the first time all core components work together to provide a usable knowledge management system.

### Added
- **Enhanced Concept Extraction**: Three-section context system combining linked concepts, RAG results, and recent concepts for improved accuracy
- **Concept Merging**: Automatic LLM-based merging of existing concepts with new information
- **Concept Relations**: Automatic extraction of typed relationships between concepts with bidirectional relation creation
- **Field Comparison System**: Intelligent content comparison that only updates concepts when core content changes, optimizing LLM calls
- **Frontmatter Constants Standardization**: Centralized frontmatter key constants for consistency across the codebase
- **Custom Temporal Data Converter**: Preserves domain entity types during Temporal workflow serialization/deserialization

### Changed
- **Pydantic v2 Migration**: Updated all models to use `SettingsConfigDict` and proper field definitions, removing deprecated class-based Config
- **Code Quality Improvements**: Reduced cyclomatic complexity across 15+ methods using method extraction
- **Type Safety**: Fixed 100+ mypy type errors and improved type annotations throughout codebase
- **Test Performance**: Improved test execution time from 53s to 11s for LLM service tests (3x faster)
- **Code Complexity**: Reduced average cyclomatic complexity from C-15 to B-6

### Fixed
- **Temporal Serialization Issue**: Resolved `'dict' object has no attribute 'uuid'` error by implementing custom data converter
- **Entity UUID AttributeError**: Fixed `AttributeError: 'entity' object has no attribute 'uuid'` in curation pipeline through proper entity conversion

### Improved
- **LLM Service**: Refactored complex `generate` method (C-31) into 7 focused helper methods
- **Curation Manager**: Refactored `get_all_pending_curation_tasks` (D-21) into 8 specialized methods
- **Obsidian Service**: Refactored 6 complex methods including `_create_concept_relations` (C-18) and `_parse_zettel_sections` (C-14)
- **Health Check API**: Simplified `health_check` function (C-16) into 6 focused helper methods
- **Document Models**: Refactored `JournalEntry.from_text` method and related parsing functions
- **Test Suite**: Maintained 100% test coverage (346 tests) while improving reliability and performance

### Documentation
- Added comprehensive documentation for frontmatter constants
- Enhanced concept extraction and concept relations documentation
- Updated database schema documentation with new ConceptRelation models
- Added dependency injection documentation with comprehensive code comments
- Improved inline documentation throughout refactored methods

### Technical Details
- **Code Quality Standards**: Achieved 100% pass rate on all quality checks (Black, isort, flake8, radon, vulture, mypy)
- **Type Safety**: 0 mypy errors (down from 100+)
- **Test Coverage**: 100% coverage maintained with 346 passing tests
- **Performance**: Optimized LLM calls by avoiding unnecessary updates for unchanged concepts

## [0.1.0] - Initial Release

### Added
- Backend API for journal submission and curation
- Complete 6-stage Temporal pipeline
- LLM-based extraction for entities and relationships
- Neo4j integration with repository pattern for all major entity types
- Curation queue system
- Basic Obsidian link resolution
- minerva-desktop: Native desktop application for agent interaction
- minerva_agent: Deep agent for Obsidian vault assistance
- zettel: Quote parsing and concept extraction agents

---

[0.4.0]: https://github.com/yourusername/Minerva/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/yourusername/Minerva/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/yourusername/Minerva/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/Minerva/releases/tag/v0.1.0

