from typing import List, Dict, Optional, Tuple
from uuid import uuid4

import stanza
from pydantic import BaseModel, Field


class Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    start_char: int
    end_char: int
    children: List[str] = Field(default_factory=list)
    parent: Optional[str] = None
    prev_sibling: Optional[str] = None
    next_sibling: Optional[str] = None


def build_chunks(text) -> Dict[str, Node]:
    nlp = stanza.Pipeline(lang='es', processors='tokenize')
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
        i = 0
        while i < len(current_level):
            left_id = current_level[i]
            right_id = current_level[i + 1] if (i + 1) < len(current_level) else None

            left_node = nodes[left_id]
            if right_id is None:
                # PROMOTE the leftover node to next level (do not create a single-child parent)
                # ensure parent's pointer remains None for now; it will get a parent if paired later
                next_level.append(left_id)
                i += 1
            else:
                right_node = nodes[right_id]
                parent_start = left_node.start_char
                parent_end = right_node.end_char
                parent = Node(start_char=parent_start, end_char=parent_end, children=[left_id, right_id])
                nodes[parent.id] = parent
                # wire parent <- children
                left_node.parent = parent.id
                right_node.parent = parent.id
                next_level.append(parent.id)
                i += 2

        # annotate siblings of the next level to maintain left-right traversal invariants
        annotate_siblings(next_level)
        current_level = next_level

    return nodes
