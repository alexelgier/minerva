"""New LangGraph Agent.

This module defines custom graphs.
"""

from .quote_parse_graph import graph as quote_parse_graph
from .concept_extraction_graph import graph as concept_extraction_graph

__all__ = ["quote_parse_graph", "concept_extraction_graph"]
