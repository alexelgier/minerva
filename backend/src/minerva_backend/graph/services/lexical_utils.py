from typing import Dict, List, Tuple
from intervaltree import IntervalTree

from minerva_backend.graph.db import Neo4jConnection
from minerva_backend.graph.models.documents import Chunk, JournalEntry


class SpanIndex:
    def __init__(self):
        self.tree = IntervalTree()

    def add_span(self, start: int, end: int, chunk_uuid: str):
        # IntervalTree uses [start, end), so end is exclusive
        self.tree[start:end] = chunk_uuid

    def add_span_batch(self, spans_dict: Dict[Tuple[int, int], str]):
        for span, uuid in spans_dict.items():
            self.tree[span[0]:span[1]] = uuid

    def query_containing(self, start: int, end: int) -> list[str]:
        """
        Return all chunk_uuids whose spans fully contain [start, end).
        """
        matches = self.tree.envelop(start, end)
        return [iv.data for iv in matches]

    def __len__(self):
        return len(self.tree)

    def __iter__(self):
        for iv in self.tree:
            yield (iv.begin, iv.end), iv.data


def build_and_insert_lexical_tree(connection: Neo4jConnection, journal_entry: JournalEntry, nlp=None) -> SpanIndex | None:
    """
    Build a lexical tree from a JournalEntry's text and insert it into the database.

    Args:
        connection: Neo4jConnection
        journal_entry: JournalEntry object (already in DB)
        nlp: Optional Stanza pipeline for testing

    Returns:
        Dict[Tuple[int, int], str]: Mapping from (start_char, end_char) spans to chunk UUIDs
    """
    text = journal_entry.entry_text
    if not text:
        return None

    result = SpanIndex()

    # Initialize span mapping with journal entry (full text span)
    span_to_uuid = {(0, len(text)): journal_entry.uuid}

    # Allow injecting a nlp pipeline for testing; lazily import stanza if needed
    if nlp is None:
        import stanza
        nlp = stanza.Pipeline(lang="es", processors="tokenize", download_method=None)

    doc = nlp(text)
    if not doc.sentences:
        return span_to_uuid

    # Create sentence chunks
    sentence_chunks = []
    for sent in doc.sentences:
        start = int(sent.tokens[0].start_char)
        end = int(sent.tokens[-1].end_char)
        chunk = Chunk(text=text[start:end])
        sentence_chunks.append((chunk, start, end))
        span_to_uuid[(start, end)] = chunk.uuid

    # Build balanced binary tree
    all_chunks = []
    relationships = []

    # Add all sentence chunks to our collections
    all_chunks.extend([chunk for chunk, _, _ in sentence_chunks])

    # Build tree and get root
    if sentence_chunks:
        root_chunk, root_start, root_end = _build_balanced_tree(
            sentence_chunks, text, all_chunks, relationships, span_to_uuid
        )

        # Connect root to journal entry
        relationships.append({
            "parent": journal_entry.uuid,
            "child": root_chunk.uuid,
            "type": "CONTAINS"
        })

        # Add HAS_CHUNK relationships from journal entry to every chunk
        for chunk in all_chunks:
            relationships.append({
                "parent": journal_entry.uuid,
                "child": chunk.uuid,
                "type": "HAS_CHUNK"
            })

    try:
        print(f"Inserting {len(all_chunks)} chunks and {len(relationships)} relationships")
        _insert_chunks_and_relationships(connection, all_chunks, relationships)
    except Exception as e:
        print(f"Error inserting chunks: {e}")
        raise

    return span_to_uuid


def _build_balanced_tree(nodes: List[Tuple], text: str, all_chunks: List,
                         relationships: List[Dict], span_to_uuid: Dict) -> Tuple:
    """
    Build a balanced binary tree from a list of (chunk, start, end) tuples.
    Returns the root (chunk, start, end).
    """
    if len(nodes) == 1:
        return nodes[0]

    if len(nodes) == 2:
        # Create parent for the pair
        left_chunk, left_start, left_end = nodes[0]
        right_chunk, right_start, right_end = nodes[1]

        # Create parent chunk spanning both children
        parent_start = min(left_start, right_start)
        parent_end = max(left_end, right_end)
        parent_text = text[parent_start:parent_end]
        parent_chunk = Chunk(text=parent_text)

        all_chunks.append(parent_chunk)
        span_to_uuid[(parent_start, parent_end)] = parent_chunk.uuid

        # Create relationships
        relationships.extend([
            {"parent": parent_chunk.uuid, "child": left_chunk.uuid, "type": "CONTAINS"},
            {"parent": parent_chunk.uuid, "child": right_chunk.uuid, "type": "CONTAINS"},
            {"parent": left_chunk.uuid, "child": right_chunk.uuid, "type": "NEXT_SIBLING"}
        ])

        return parent_chunk, parent_start, parent_end

    # Split into two halves and recursively build subtrees
    mid = len(nodes) // 2
    left_nodes = nodes[:mid]
    right_nodes = nodes[mid:]

    left_root = _build_balanced_tree(left_nodes, text, all_chunks, relationships, span_to_uuid)
    right_root = _build_balanced_tree(right_nodes, text, all_chunks, relationships, span_to_uuid)

    # Create parent for the two subtrees
    left_chunk, left_start, left_end = left_root
    right_chunk, right_start, right_end = right_root

    parent_start = min(left_start, right_start)
    parent_end = max(left_end, right_end)
    parent_text = text[parent_start:parent_end]
    parent_chunk = Chunk(text=parent_text)

    all_chunks.append(parent_chunk)
    span_to_uuid[(parent_start, parent_end)] = parent_chunk.uuid

    # Create relationships
    relationships.extend([
        {"parent": parent_chunk.uuid, "child": left_chunk.uuid, "type": "CONTAINS"},
        {"parent": parent_chunk.uuid, "child": right_chunk.uuid, "type": "CONTAINS"},
        {"parent": left_chunk.uuid, "child": right_chunk.uuid, "type": "NEXT_SIBLING"}
    ])

    return parent_chunk, parent_start, parent_end


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

    # Separate relationships by type for better debugging
    contains_rels = [r for r in relationships if r["type"] == "CONTAINS"]
    sibling_rels = [r for r in relationships if r["type"] == "NEXT_SIBLING"]
    has_chunk_rels = [r for r in relationships if r["type"] == "HAS_CHUNK"]

    print(f"Creating {len(chunks)} chunks")
    print(f"Creating {len(contains_rels)} CONTAINS relationships")
    print(f"Creating {len(sibling_rels)} NEXT_SIBLING relationships")
    print(f"Creating {len(has_chunk_rels)} HAS_CHUNK relationships")

    with connection.session() as session:
        # Create all chunks
        result = session.run("""
            UNWIND $chunks AS c
            CREATE (:Chunk {
                uuid: c.uuid,
                text: c.text,
                type: c.type,
                partition: c.partition,
                created_at: datetime(c.created_at)
            })
        """, chunks=chunk_data)

        print(f"Chunks created: {result.consume().counters.nodes_created}")

        # Create CONTAINS relationships (tree structure)
        if contains_rels:
            result = session.run("""
                UNWIND $contains_rels AS rel
                MATCH (parent)
                WHERE parent.uuid = rel.parent
                MATCH (child:Chunk)
                WHERE child.uuid = rel.child
                CREATE (parent)-[:CONTAINS]->(child)
            """, contains_rels=contains_rels)
            print(f"CONTAINS relationships created: {result.consume().counters.relationships_created}")

        # Create HAS_CHUNK relationships (direct access)
        if has_chunk_rels:
            result = session.run("""
                UNWIND $has_chunk_rels AS rel
                MATCH (parent)
                WHERE parent.uuid = rel.parent
                MATCH (child:Chunk)
                WHERE child.uuid = rel.child
                CREATE (parent)-[:HAS_CHUNK]->(child)
            """, has_chunk_rels=has_chunk_rels)
            print(f"HAS_CHUNK relationships created: {result.consume().counters.relationships_created}")

        # Create NEXT_SIBLING relationships
        if sibling_rels:
            result = session.run("""
                UNWIND $sibling_rels AS rel
                MATCH (a:Chunk)
                WHERE a.uuid = rel.parent
                MATCH (b:Chunk)
                WHERE b.uuid = rel.child
                CREATE (a)-[:NEXT_SIBLING]->(b)
            """, sibling_rels=sibling_rels)
            print(f"NEXT_SIBLING relationships created: {result.consume().counters.relationships_created}")
