# Changelog

All notable changes to the zettel_agent module will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-01-27

### Added
- **Web Search Enrichment**: Added automatic web search enrichment for author and book summaries using Gemini's built-in Google Search tool (grounding)
  - Author enrichment: Automatically enriches newly created author entities with comprehensive biography, summary, and occupation information from web search
  - Book summary enrichment: Automatically enhances book summaries with additional context and information from web search
  - Uses Gemini's native `google_search` tool - no separate CSE ID required, only `GOOGLE_API_KEY` needed
  - Enrichment happens automatically within existing workflow nodes (`make_summary` and `get_or_create_author`)
  - Gracefully falls back to basic data if enrichment fails or is unavailable

### Changed
- Renamed `ensure_author_exists` node to `get_or_create_author` for better clarity
- Refactored author creation to enrich first, then create (avoiding wasteful create-then-update pattern)
- Integrated web search enrichment directly into `make_summary` and `get_or_create_author` nodes (removed separate enrichment nodes)
- Simplified workflow: enrichment now happens automatically within core nodes
- Updated database functions: Added `update_person()` and `update_content()` functions for updating existing entities

### Documentation
- Updated README.md with web search enrichment feature documentation
- Updated workflow documentation to reflect integrated enrichment approach
- Updated API documentation with new function names and web search capabilities

## [0.1.0] - 2025-01-27

### Added
- **User Suggestions for Concept Extraction**: Added optional `user_suggestions` field to the concept extraction graph input state. Users can now provide freeform text suggestions that guide the extraction process. These suggestions are:
  - Included in the initial concept extraction prompt
  - Considered during self-critique quality assessment
  - Incorporated during refinement iterations
  - Available throughout the entire workflow via the `ConceptExtractionState`

### Changed
- Updated `ConceptExtractionState` TypedDict to include `user_suggestions: Optional[str]` field
- Updated `InputState` dataclass to include `user_suggestions: Optional[str] = None` field
- Modified `extract_candidate_concepts` node to include user suggestions in the LLM prompt
- Modified `self_critique` node to consider user suggestions when evaluating extraction quality
- Modified `refine_extraction` node to incorporate user suggestions during refinement

### Documentation
- Updated README.md with examples showing how to use `user_suggestions`
- Updated API.md to document the new field in `ConceptExtractionState`
- Updated WORKFLOWS.md to explain how user suggestions are used in each phase

## [0.0.1] - Initial Development

Initial development version of the zettel_agent module with:
- Quote parsing graph
- Concept extraction graph with 3-phase workflow
- Neo4j integration
- Obsidian file generation

**Note:** This version represents the initial implementation. Core functionality is complete but not yet tested or production-ready.

[Unreleased]: https://github.com/yourusername/minerva/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/yourusername/minerva/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/yourusername/minerva/compare/v0.0.1...v0.1.0
[0.0.1]: https://github.com/yourusername/minerva/releases/tag/v0.0.1

