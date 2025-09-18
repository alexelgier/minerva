from typing import Dict, List, Tuple

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import Chunk, JournalEntry


def build_and_insert_lexical_tree(connection: Neo4jConnection, journal_entry: JournalEntry, nlp=None) -> Dict[
    Tuple[int, int], str]:
    """
    Build a lexical tree from a JournalEntry's text and insert it into the database.

    Args:
        connection: Neo4jConnection
        journal_entry: JournalEntry object (already in DB)
        nlp: Optional Stanza pipeline for testing

    Returns:
        Dict[Tuple[int, int], str]: Mapping from (start_char, end_char) spans to chunk UUIDs
    """
    # Get text and add journal entry to span mapping
    text = journal_entry.entry_text
    if not text:
        return {}

    # Initialize span mapping with journal entry (full text span)
    span_to_uuid = {(0, len(text)): journal_entry.uuid}

    # Allow injecting a nlp pipeline for testing; lazily import stanza if needed
    if nlp is None:
        import stanza
        nlp = stanza.Pipeline(lang="es", processors="tokenize")

    sentences = nlp(text).sentences
    if not sentences:
        return span_to_uuid

    # Create leaf chunks (sentences)
    all_chunks = []
    leaves = []

    for sent in sentences:
        start = int(sent.tokens[0].start_char)
        end = int(sent.tokens[-1].end_char)
        chunk_text = text[start:end]

        chunk = Chunk(text=chunk_text)
        all_chunks.append(chunk)
        leaves.append((chunk.uuid, start, end))
        span_to_uuid[(start, end)] = chunk.uuid

    # Build balanced tree structure bottom-up using center-out strategy
    relationships = []
    current_level = leaves

    while len(current_level) > 2:  # Stop when we have 2 nodes (journal entry's children)
        next_level = []

        # Create sibling relationships for current level
        for i in range(len(current_level) - 1):
            left_uuid = current_level[i][0]
            right_uuid = current_level[i + 1][0]
            relationships.append({
                "parent": left_uuid,
                "child": right_uuid,
                "type": "NEXT_SIBLING"
            })

        # Build balanced subtrees using center-out approach
        next_level.extend(_build_balanced_level(current_level, text, all_chunks, relationships, span_to_uuid))
        current_level = next_level

    # Connect top-level chunks to journal entry (CONTAINS relationships)
    for top_chunk_uuid, _, _ in current_level:
        relationships.append({
            "parent": journal_entry.uuid,
            "child": top_chunk_uuid,
            "type": "CONTAINS"
        })

    # Create direct HAS_CHUNK relationships from journal entry to all chunks
    for chunk in all_chunks:
        relationships.append({
            "parent": journal_entry.uuid,
            "child": chunk.uuid,
            "type": "HAS_CHUNK"
        })

    # Insert everything into database
    _insert_chunks_and_relationships(connection, all_chunks, relationships)

    return span_to_uuid


def _build_balanced_level(current_level: List[Tuple], text: str, all_chunks: List,
                          relationships: List[Dict], span_to_uuid: Dict) -> List[Tuple]:
    """Build a balanced level using recursive center-out strategy."""
    if len(current_level) <= 1:
        return current_level

    # Split into two roughly equal halves
    mid = len(current_level) // 2
    left_half = current_level[:mid]
    right_half = current_level[mid:]

    result = []

    # Process left half
    if len(left_half) == 1:
        result.append(left_half[0])
    else:
        left_parent = _create_parent_chunk(left_half, text, all_chunks, relationships, span_to_uuid)
        result.append(left_parent)

    # Process right half
    if len(right_half) == 1:
        result.append(right_half[0])
    else:
        right_parent = _create_parent_chunk(right_half, text, all_chunks, relationships, span_to_uuid)
        result.append(right_parent)

    return result


def _create_parent_chunk(children: List[Tuple], text: str, all_chunks: List,
                         relationships: List[Dict], span_to_uuid: Dict) -> Tuple:
    """Create a parent chunk for the given children."""
    # Get span boundaries
    start = min(child[1] for child in children)
    end = max(child[2] for child in children)
    parent_text = text[start:end]

    # Create parent chunk
    parent_chunk = Chunk(text=parent_text)
    all_chunks.append(parent_chunk)
    span_to_uuid[(start, end)] = parent_chunk.uuid

    # Add CONTAINS relationships to all children
    for child_uuid, _, _ in children:
        relationships.append({
            "parent": parent_chunk.uuid,
            "child": child_uuid,
            "type": "CONTAINS"
        })

    return parent_chunk.uuid, start, end


def _insert_chunks_and_relationships(connection, chunks: List, relationships: List[Dict]):
    """Insert chunks and their relationships into Neo4j database."""

    # Prepare chunk data for Cypher
    chunk_data = [
        {
            "uuid": chunk.uuid,
            "text": chunk.text,
            "type": chunk.type,
            "partition": chunk.partition,
            "created_at": chunk.created_at.isoformat()
        }
        for chunk in chunks
    ]

    # Separate relationships by type
    contains_rels = [r for r in relationships if r["type"] == "CONTAINS"]
    has_chunk_rels = [r for r in relationships if r["type"] == "HAS_CHUNK"]
    sibling_rels = [r for r in relationships if r["type"] == "NEXT_SIBLING"]

    with connection.session() as session:
        # Create all chunks
        session.run("""
            UNWIND $chunks AS c
            CREATE (:Chunk {
                uuid: c.uuid,
                text: c.text,
                type: c.type,
                partition: c.partition,
                created_at: datetime(c.created_at)
            })
        """, chunks=chunk_data)

        # Create CONTAINS relationships (tree structure)
        if contains_rels:
            session.run("""
                UNWIND $contains_rels AS rel
                MATCH (parent {uuid: rel.parent}), (child:Chunk {uuid: rel.child})
                CREATE (parent)-[:CONTAINS]->(child)
            """, contains_rels=contains_rels)

        # Create HAS_CHUNK relationships (direct access)
        if has_chunk_rels:
            session.run("""
                UNWIND $has_chunk_rels AS rel
                MATCH (parent {uuid: rel.parent}), (child:Chunk {uuid: rel.child})
                CREATE (parent)-[:HAS_CHUNK]->(child)
            """, has_chunk_rels=has_chunk_rels)

        # Create NEXT_SIBLING relationships
        if sibling_rels:
            session.run("""
                UNWIND $sibling_rels AS rel
                MATCH (a:Chunk {uuid: rel.parent}), (b:Chunk {uuid: rel.child})
                CREATE (a)-[:NEXT_SIBLING]->(b)
            """, sibling_rels=sibling_rels)
