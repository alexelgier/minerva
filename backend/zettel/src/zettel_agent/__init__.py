"""Zettel Agent - LangGraph-based agent system for processing book quotes and extracting atomic concepts.

This module provides two main LangGraph workflows:

1. **quote_parse_graph**: Processes markdown book notes and extracts quotes with metadata
2. **concept_extraction_graph**: Extracts atomic concepts (Zettels) from quotes using vector search and LLM analysis

The module implements Zettelkasten methodology for knowledge management, transforming
unstructured book quotes into a structured knowledge graph of atomic, interconnected concepts.

Example:
    ```python
    from zettel_agent import quote_parse_graph, concept_extraction_graph
    
    # Parse quotes from a book
    quote_result = await quote_parse_graph.ainvoke({
        "file_path": "/path/to/book.md",
        "author": "Author Name",
        "title": "Book Title"
    })
    
    # Extract concepts from quotes
    concept_result = await concept_extraction_graph.ainvoke({
        "content_uuid": quote_result["content_uuid"]
    })
    ```

See Also:
    - [API Reference](../docs/API.md) - Complete API documentation
    - [Architecture Documentation](../docs/ARCHITECTURE.md) - Technical architecture
    - [Developer Guide](../docs/DEVELOPER.md) - Extension guide
"""

from .quote_parse_graph import graph as quote_parse_graph
from .concept_extraction_graph import graph as concept_extraction_graph

__all__ = ["quote_parse_graph", "concept_extraction_graph"]
