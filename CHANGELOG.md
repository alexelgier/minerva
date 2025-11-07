# Changelog

All notable changes to the Minerva project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-11-XX

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

[0.2.0]: https://github.com/yourusername/Minerva/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/Minerva/releases/tag/v0.1.0

