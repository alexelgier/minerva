# Concept Extraction Workflow - Design Document

## 1. Problem Statement

### Goal
Transform a content node with its associated quotes into a structured knowledge graph by:
1. Extracting novel atomic concepts from the quotes (new ideas not present in the existing knowledge graph)
2. Creating proper relations between new concepts and existing concepts
3. Attributing quotes to relevant concepts (existing and/or new) via SUPPORTS relations

**Novelty Definition**: A concept is novel if it represents a semantically distinct idea not present in the existing knowledge graph. Paraphrases or reformulations of existing concepts are NOT considered novel - novelty is determined by semantic equivalence, not textual similarity.

### Start State (A)
- **Existing Knowledge Graph**: 0 to thousands of Concept nodes with typed relations between them (GENERALIZES, SPECIFIC_OF, PART_OF, HAS_PART, SUPPORTS, SUPPORTED_BY, OPPOSES, SIMILAR_TO, RELATES_TO)
- **Content Node**: A single Content node to be processed
  - Has a `processed_date` field that is empty/null if not processed yet
  - If `processed_date` is already set, the workflow should not process it (content already processed)
- **Quotes**: Multiple Quote nodes related to the Content node, unprocessed (haven't been analyzed yet - no SUPPORTS relations to concepts yet)

### End State (B)

**B1: New Concepts (0+)**
- 0 or more new Concept nodes created from the quotes
- New concepts may have relations to other concepts (existing or new), but relations are not required - concepts can exist disconnected from the graph
- When relations are created:
  - Relations between new concepts and existing concepts (existing→new and new→existing)
  - Relations between new concepts (new→new)
  - Bidirectional relations are created automatically according to existing project rules (see Relation Types section)
- Edge case: 0 new concepts only if:
    - No novel concepts (semantically distinct ideas not in the graph) can be extracted from the quotes
- Note: Even if quotes support existing concepts, novel concepts may still exist in those quotes

**B2: Quote Attributions**
- Quotes have SUPPORTS relations to concepts (existing and/or new)
- A quote can support multiple concepts (any mix: existing, new, or both)
- Most quotes should support at least one concept, but unconceptual quotes (quotes that don't support any concept) are possible, though rare
- **Independence Principle**: Quote attribution and concept extraction are independent processes:
  - A quote can support existing concepts AND contribute to new concept formation simultaneously
  - Supporting an existing concept does not preclude a quote from being part of a new concept
  - Forming a new concept from quotes does not preclude those quotes from supporting existing concepts

**B3: Existing Graph Integrity**
- Relations between existing concepts remain unchanged
- Only new relations are created (existing→new and new→new)

**B4: Processing Status**
- Content node's `processed_date` field is set to the processing completion timestamp

## 2. Core Principles

### Quality Criteria

- **Priority**: Quality over speed/cost
1. **Atomicity**: Each concept contains ONE clear, standalone idea (following Zettelkasten principles - each concept should be understandable and meaningful on its own, representing a single coherent thought)
2. **Distinctness**: New concepts are semantically distinct from existing concepts (avoid duplicates - paraphrases are not novel)
3. **Completeness**: 
   - All meaningful concepts are extracted from the quotes (determined by LLM and Human-in-the-Loop during processing)
   - All relevant quote attributions are made (quotes are connected to all concepts they support)
   - New concepts are related to other concepts when appropriate (but relations are not mandatory - disconnected concepts are acceptable)
4. **Accuracy**: Relations and attributions are semantically correct and meaningful (correctly represent the actual relationships between concepts and quotes)

### Constraints

- Existing concept relations cannot be modified
- All relations must use the defined relation types (GENERALIZES, SPECIFIC_OF, PART_OF, HAS_PART, SUPPORTS, SUPPORTED_BY, OPPOSES, SIMILAR_TO, RELATES_TO)
- Bidirectional relation creation follows existing project rules (see Relation Types section below)
- Concepts must be in Spanish (as per current system requirement)
- Process must handle edge cases gracefully:
  - 0 quotes in content
  - 0 existing concepts in knowledge graph
  - All quotes are unconceptual (don't support any concept)
  - All quotes can be attributed to existing concepts but no novel concepts exist
  - Very large number of quotes (hundreds/thousands)
  - Content already processed (processed_date is set) - workflow should exit early without processing
- **Human-in-the-Loop (HITL)**: The LLM and human reviewer determine concept meaningfulness and validate extraction quality during the process

## 3. Iterative Extraction Workflow

### Overview
The workflow uses an iterative refinement approach with two main phases:
1. **LLM Self-Improvement Loop**: Autonomous extraction and self-critique until quality standards are met
2. **Human Review Loop**: Human-guided refinement until explicit approval

### Phase 1: LLM Self-Improvement Loop

**Inputs:**
- Content node with quotes to process
- Existing knowledge graph (all concepts and relations)
- Quality checklist criteria

**Process:**

**Step 1.1: Initial Extraction (Multi-Call Process)**

This step is broken down into multiple LLM calls for clarity and manageability:

**Call 1.1a: Extract Candidate Concepts with Source Quotes**
- Input:
  - System prompt + extraction instructions
  - All quotes from content node
- Output:
  - List of candidate concepts
  - Each concept explicitly linked to source quote IDs that formed it
- Purpose: Extract all meaningful atomic concepts from quotes with implicit quote→concept attribution

**Call 1.1b: Duplicate Detection (per candidate concept)**
- For each candidate concept from 1.1a:
  - Perform semantic search on summary_short embeddings → retrieve top 50 similar existing concepts
  - LLM compares candidate against retrieved concepts (using title + summary_short)
  - LLM determines: Is this a duplicate? If yes, which existing concept?
- Result:
  - **Novel concepts**: Kept as-is with their quote links
  - **Duplicate concepts**: Replaced with existing concept, quote links transferred to existing concept
- Note: Quote attribution to existing concepts happens automatically through this deduplication process

**Call 1.1c: Generate Relation Search Queries**
- Input:
  - Novel concepts only (duplicates already filtered out)
  - Available relation types (GENERALIZES, OPPOSES, PART_OF, etc.)
- Output:
  - For each novel concept: 2+ search queries per relation type
  - Queries designed to find existing concepts that might have specific relation types with the new concept
- Purpose: Generate targeted queries for finding relation candidates (since semantic similarity alone won't identify OPPOSES, PART_OF, etc.)

**Call 1.1d: Semantic Search for Relation Candidates**
- Execute all search queries from 1.1c against existing concept embeddings
- Deduplicate results across all queries
- Result: Pool of ~50-100 existing concepts that are candidates for relations with novel concepts

**Call 1.1e: Create Relations**
- Input:
  - Novel concepts
  - Relation candidate pool from 1.1d
- Output:
  - Relations between concepts (existing→new, new→new)
  - Each relation includes: source concept, relation type, target concept, explanation
- Purpose: Create meaningful typed relations between concepts
- Note: Relations are not mandatory - concepts can exist disconnected from the graph

**Summary of Step 1.1 Outputs:**
- Novel concepts (with quote attributions)
- Existing concepts with new quote attributions (via deduplication)
- Relations between concepts
- Extraction rationale/reasoning

**Step 1.2: Self-Critique**
- LLM validates extraction against quality checklist:
  - ✓ **Atomicity**: Each concept contains one clear, standalone idea
  - ✓ **Distinctness**: New concepts are semantically distinct from existing concepts (no duplicates)
  - ✓ **Quote Coverage**: All meaningful quotes are attributed to at least one concept
  - ✓ **Relation Accuracy**: Relations are semantically correct and meaningful
  - ✓ **Language**: All concepts are in Spanish
  - ✓ **Edge Case Handling**: Unattributed quotes, disconnected concepts are properly noted
- LLM generates detailed critique identifying issues and improvements

**Step 1.3: Refinement**
- LLM refines extraction based on self-critique
- Updates concepts, relations, and quote attributions
- Documents changes made

**Step 1.4: Loop Decision**
- **Continue loop if**: Quality checklist has failures AND loop count < max iterations (suggested: 3-5)
- **Exit to Phase 2 if**: Quality checklist passes OR max iterations reached

**Outputs:**
- Refined extraction proposal
- Self-critique log (all iterations)
- Quality validation results

### Phase 2: Human Review Loop

**Step 2.1: Present Comprehensive Report**

Human receives detailed report containing:

1. **New Concepts**
   - Concept text/description (in Spanish)
   - Rationale for creation
   - Source quotes that led to concept formation

2. **Relations**
   - All new relations (existing→new, new→new)
   - Relation type and direction
   - Explanation for each relation

3. **Quote Attributions**
   - Which quotes support which concepts (existing and/or new)
   - Quotes supporting multiple concepts highlighted

4. **Edge Cases & Warnings**
   - Unattributed quotes (if any) with explanation
   - Disconnected concepts (no relations)
   - Any other anomalies or concerns

5. **LLM Reasoning Log**
   - Self-critique iterations
   - Key decisions and trade-offs
   - Confidence assessment

**Step 2.2: Human Feedback**

Human provides free-form text critique with granular control options:

- **Approve All**: Accept entire extraction as-is
- **Approve Specific Items**: Accept certain concepts/relations while rejecting others
- **Reject/Modify Specific Items**: 
  - Mark concepts as too granular/too broad
  - Flag incorrect relations
  - Request rewording or merging
  - Add missing concepts or relations
- **Reject All**: Reject entire extraction with rationale (e.g., "too granular overall", "missing key concepts", "wrong semantic level")

**Step 2.3: LLM Incorporation**
- LLM processes human feedback
- LLM also considers quality checklist criteria when incorporating feedback
- Updates extraction accordingly
- Generates new proposal with changes documented

**Step 2.4: Loop Decision**
- **Continue loop if**: Human has not approved AND iteration count < hard limit (suggested: 5-10)
- **Exit to Phase 3 if**: Human explicitly approves
- **Abort process if**: Hard limit reached (iteration count >= hard limit)

**Outputs:**
- Human-approved extraction (ready for Phase 3 commit)
  - New concepts to create
  - New relations to create
  - Quote-to-concept SUPPORTS relations to create

### Phase 3: Commit to Database

**Step 3.1: Create Graph Elements**
- Create new Concept nodes in database
- Create new relations (with automatic bidirectional pairs)
- Create SUPPORTS relations from quotes to concepts

**Step 3.2: Create Obsidian Notes**
- Create markdown file for each new concept in `Zettels/` directory
- Include frontmatter with `entity_id`, `entity_type`, `short_summary`, `summary`, and `concept_relations` (UUID-based)
- Include markdown sections: `# Title`, `## Concepto`, `## AnÃ¡lisis`, `## Conexiones` (with Obsidian `[[Concept Name]]` links), `## Fuente`
- Resolve concept UUIDs to names for Obsidian links in Conexiones section

**Step 3.3: Update Processing Status**
- Set Content node's `processed_date` to current timestamp

### Workflow Safeguards

**Loop Limits:**
- Phase 1 (Self-Improvement): 2 iterations maximum
- Phase 2 (Human Review): 5 iterations maximum

**Convergence:**
- Phase 1: LLM self-improvement should converge based on quality checklist
- Phase 2: Human feedback should guide convergence, but quality checklist should still be taken into account
- If hard limit is reached for Phase 1: User should be presented with latest iteration
- If hard limit is reached for Phase 2: The process should be aborted

**Quality Over Speed:**
- No time pressure to complete quickly
- Iterations continue until quality standards are met or limits reached
- Human approval is the ultimate quality gate

## 4. Glossary

- **Atomic Concept**: A concept containing ONE clear, standalone idea that is understandable without the original context (following Zettelkasten atomicity principle - each concept represents a single coherent thought)
- **Novel Concept**: A semantically distinct idea not present in the existing knowledge graph. Paraphrases or reformulations of existing concepts are NOT novel - novelty is determined by semantic equivalence
- **SUPPORTS Relation**: A relation from a Quote to a Concept indicating that the quote provides evidence, clarification, or elaboration for that concept
- **Unprocessed Quote**: A quote that hasn't been analyzed yet (no SUPPORTS relations to concepts yet)
- **Unconceptual Quote**: A quote that doesn't support any concept (rare edge case)
- **Concept Relations**: Typed relations between Concept nodes:
  - **Asymmetric**: GENERALIZES/SPECIFIC_OF, PART_OF/HAS_PART, SUPPORTS/SUPPORTED_BY (bidirectional pairs - creating A→B automatically creates B→A with reverse type)
  - **Symmetric**: OPPOSES, SIMILAR_TO, RELATES_TO (bidirectional by nature - same type in both directions)
- **Quality Checklist**: Set of criteria the LLM validates against during self-critique (atomicity, distinctness, quote coverage, relation accuracy, language, edge case handling)
- **Self-Critique**: LLM's autonomous evaluation of its own extraction against quality checklist
- **Human-in-the-Loop (HITL)**: Human reviewer who provides feedback and approval during Phase 2 of the workflow

## 5. Relation Types

The system uses 9 relation types with automatic bidirectional creation rules (as defined in the project's `RELATION_MAP`):

### Asymmetric Relations (with automatic reverse)
- **GENERALIZES** ↔ **SPECIFIC_OF**: General concept that encompasses specific instances
- **PART_OF** ↔ **HAS_PART**: Component that belongs to a larger system
- **SUPPORTS** ↔ **SUPPORTED_BY**: Concept that provides evidence for another

### Symmetric Relations (same type in both directions)
- **OPPOSES**: Concepts that are in direct opposition
- **SIMILAR_TO**: Concepts that are related but distinct
- **RELATES_TO**: General relationship (catchall)

**Bidirectional Creation Rules**: When a relation A→B is created:
- For asymmetric relations: The reverse relation B→A is automatically created with the corresponding reverse type
- For symmetric relations: The same relation type is used in both directions
- These rules are implemented in the existing project infrastructure and should be followed