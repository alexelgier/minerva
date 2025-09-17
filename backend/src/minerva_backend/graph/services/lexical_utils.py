from itertools import zip_longest
from typing import List, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    start_char: int
    end_char: int
    children: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
    prev_sibling: Optional[str] = None
    next_sibling: Optional[str] = None


def build_chunks(text: str, nlp=None) -> Dict[str, Node]:
    # allow injecting a nlp pipeline for testing; lazily import stanza if needed
    if nlp is None:
        import stanza
        nlp = stanza.Pipeline(lang="es", processors="tokenize")

    sentences = nlp(text).sentences
    nodes: Dict[str, Node] = {}

    # create leaves in order
    leaves: List[str] = []
    for sent in sentences:
        start = int(sent.tokens[0].start_char)
        end = int(sent.tokens[-1].end_char)
        node = Node(start_char=start, end_char=end)
        nodes[node.id] = node
        leaves.append(node.id)

    if not leaves:
        return nodes

    def annotate_siblings(level_ids: List[str]) -> None:
        for i, nid in enumerate(level_ids):
            node = nodes[nid]
            node.prev_sibling = level_ids[i - 1] if i > 0 else None
            node.next_sibling = level_ids[i + 1] if i < len(level_ids) - 1 else None

    annotate_siblings(leaves)

    current_level = leaves
    # build parents bottom-up until single root
    while len(current_level) > 1:
        next_level: List[str] = []
        # pair neighbors: lefts = current_level[::2], rights = current_level[1::2]
        for left_id, right_id in zip_longest(current_level[::2], current_level[1::2], fillvalue=None):
            if right_id is None:
                # promote leftover
                next_level.append(left_id)
            else:
                lnode, rnode = nodes[left_id], nodes[right_id]
                parent = Node(start_char=lnode.start_char, end_char=rnode.end_char, children=[left_id, right_id])
                nodes[parent.id] = parent
                lnode.parent = parent.id
                rnode.parent = parent.id
                next_level.append(parent.id)

        annotate_siblings(next_level)
        current_level = next_level

    return nodes
