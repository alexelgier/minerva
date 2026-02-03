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
- **Quote Attribution**: Happens during the extraction and deduplication process:
  - When extracting concepts, quotes are linked to the concepts they form
  - During deduplication, if a concept is found to be a duplicate, its quote links are transferred to the existing concept
  - A quote can support multiple concepts (both existing and new)
  - The attribution is resolved as part of the extraction workflow, not as a separate process

**B3: Existing Graph Integrity**
- Relations between existing concepts remain unchanged
- Only new relations are created (existing→new and new→new)

**B4: Processing Status**
- Content node's `processed_date` field is set to the processing completion timestamp

## 2. Core Principles

### Quality Criteria

- **Priority**: Quality over speed/cost (chosen approach: thorough extraction with higher computational cost)
1. **Atomicity**: Each concept contains ONE clear, standalone idea (following Zettelkasten principles)
   - **Definition**: Each concept should be self-contained and express a complete thought
   - **Evaluation criteria**:
     - Can this concept be understood without reading other concepts?
     - Does it express exactly one idea (not zero, not multiple)?
     - Is it detailed enough to be meaningful but focused enough to be singular?
   - **Examples**:
     - ❌ **Too atomic**: "El ejercicio es bueno" (lacks substance)
     - ❌ **Not atomic**: "El ejercicio mejora la salud cardiovascular, reduce el estrés, ayuda a perder peso y mejora el sueño" (multiple ideas)
     - ✅ **Properly atomic**: "El ejercicio aeróbico regular mejora la salud cardiovascular al fortalecer el músculo cardíaco y reducir la presión arterial"
   - **Guidelines for LLM**:
     - Each concept should answer one specific question or explain one specific phenomenon
     - Include enough context to make the concept self-explanatory
     - Avoid lists of benefits/features - each should be its own concept
     - A concept should be linkable but not dependent on links to be understood
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

## 3. LangGraph Implementation Best Practices

This section outlines how the workflow adheres to LangGraph best practices for production-ready, reliable agent systems.

### 3.1 State Management

**State Schema Design:**
- Use `TypedDict` for type safety and IDE support
- Keep state minimal and focused - only include data needed for workflow execution
- Use `Annotated` types with reducers for list fields that need accumulation (e.g., `Annotated[list[ConceptProposal], operator.add]`)
- Separate concerns: workflow state vs. domain models

**State Structure:**
```python
from typing_extensions import TypedDict, Annotated
from typing import List, Dict, Optional, Set
import operator

class ConceptExtractionState(TypedDict):
    # Input
    content_uuid: str
    content: Optional[Content]
    quotes: List[Quote]
    
    # Processing state
    phase: Literal["extraction", "human_review", "commit"]
    iteration_count: int
    phase_1_iteration: int
    phase_2_iteration: int
    
    # Extraction results
    candidate_concepts: Annotated[List[Dict], operator.add]  # From Call 1.1a
    duplicate_detections: Annotated[List[Dict], operator.add]  # From Call 1.1b
    novel_concepts: Annotated[List[Dict], operator.add]
    existing_concepts_with_quotes: Annotated[List[Dict], operator.add]
    relations: Annotated[List[Dict], operator.add]
    
    # Quality assessment
    quality_assessment: Optional[Dict]
    critique_log: Annotated[List[Dict], operator.add]  # All critique iterations
    
    # Human review
    human_feedback: Optional[str]
    human_approved: bool
    
    # Errors and warnings
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]
```

**State Updates:**
- Nodes return partial state updates (only fields that change)
- State updates are atomic per superstep (all nodes in a superstep succeed or fail together)
- Use reducers for accumulating lists to avoid overwriting previous values

### 3.2 Checkpointing and Persistence

**Checkpointer Configuration:**
- **REQUIRED** for human-in-the-loop workflows (Phase 2)
- Use persistent checkpointer (e.g., `AsyncPostgresSaver`) in production
- Use `MemorySaver` only for development/testing
- Checkpointer saves state at every superstep automatically

**Thread Management:**
- Each workflow execution uses a unique `thread_id` in config
- Thread ID allows resuming interrupted workflows
- State persists across sessions, enabling long-running workflows

**Implementation:**
```python
from langgraph.checkpoint.postgres import AsyncPostgresSaver

checkpointer = AsyncPostgresSaver.from_conn_string(connection_string)
graph = builder.compile(checkpointer=checkpointer)

# Invoke with thread_id
config = {"configurable": {"thread_id": str(uuid.uuid4())}}
result = graph.invoke(initial_state, config=config)
```

### 3.3 Human-in-the-Loop (HITL)

**Interrupt Mechanism:**
- Use `interrupt()` function to pause execution at Phase 2
- State is automatically checkpointed before interrupt
- Human can inspect state, provide feedback, then resume

**Implementation Pattern:**
```python
from langgraph.graph import interrupt

def present_for_review(state: ConceptExtractionState):
    # Prepare comprehensive report
    report = generate_report(state)
    
    # Pause execution - state is saved
    interrupt({"action": "human_review", "report": report})
    
    # Execution resumes here after human provides feedback
    return {"human_feedback": state.get("human_feedback")}
```

**Resume Workflow:**
- Human reviews report via UI/API
- Human provides feedback or approval
- Workflow resumes from interrupt point with updated state
- No need to re-run previous steps (checkpointed state is used)

### 3.4 Parallel Execution

**Superstep Model:**
- LangGraph executes nodes in "supersteps" (Bulk Synchronous Parallel model)
- Nodes in the same superstep run in parallel
- All nodes in a superstep must complete before next superstep begins
- Updates from parallel nodes are atomic - all succeed or all fail

**Parallel Node Execution:**
- Use fan-out pattern: one node routes to multiple parallel nodes
- Use fan-in pattern: multiple parallel nodes route to one node
- Parallel nodes should be independent (no shared mutable state)

**Implementation for Call 1.1b (Duplicate Detection):**
```python
# Fan-out: Route to parallel duplicate detection nodes
def route_to_duplicate_detection(state: ConceptExtractionState):
    candidate_concepts = state["candidate_concepts"]
    return [f"detect_duplicate_{i}" for i in range(len(candidate_concepts))]

# Parallel nodes (executed in same superstep)
def detect_duplicate_0(state: ConceptExtractionState):
    # Process candidate_concepts[0]
    return {"duplicate_detections": [result_0]}

def detect_duplicate_1(state: ConceptExtractionState):
    # Process candidate_concepts[1]
    return {"duplicate_detections": [result_1]}

# Fan-in: Aggregate results
def aggregate_duplicate_detections(state: ConceptExtractionState):
    # All duplicate_detections are already in state (accumulated via reducer)
    return {"novel_concepts": filter_novels(state["duplicate_detections"])}
```

### 3.5 Error Handling

**Error Handling Strategy by Error Type:**

1. **Transient Errors** (network issues, rate limits, timeouts):
   - Use `RetryPolicy` on nodes
   - Automatic retry with exponential backoff
   - Only failing branches are retried (successful nodes don't re-run)

2. **LLM-Recoverable Errors** (parsing failures, tool errors):
   - Catch exception in node
   - Store error in state
   - Route back to LLM node to adjust approach

3. **User-Fixable Errors** (missing information, unclear instructions):
   - Use `interrupt()` to pause
   - Present error to human
   - Resume after human provides input

4. **Unexpected Errors** (bugs, system failures):
   - Let exception bubble up
   - Checkpointer saves state before failure
   - Can resume from last successful checkpoint

**Retry Policy Implementation:**
```python
from langgraph.types import RetryPolicy

# Add retry policy to nodes with transient failures
builder.add_node(
    "semantic_search",
    semantic_search_node,
    retry_policy=RetryPolicy(
        max_attempts=3,
        initial_interval=1.0,
        backoff_factor=2.0
    )
)
```

**Error Handling in Nodes:**
```python
def llm_extraction_node(state: ConceptExtractionState):
    try:
        result = llm.invoke(prompt)
        return {"candidate_concepts": parse_result(result)}
    except ParsingError as e:
        # Store error, route back to LLM with error context
        return {
            "errors": [f"Parsing error: {str(e)}"],
            "needs_retry": True
        }
```

### 3.6 Recursion Limits and Loop Control

**Recursion Limits:**
- Set `recursion_limit` in config to prevent infinite loops
- LangGraph raises `GraphRecursionError` when limit exceeded
- Catch and handle gracefully (present current state to user)

**Implementation:**
```python
from langgraph.errors import GraphRecursionError

try:
    result = graph.invoke(
        initial_state,
        config={"recursion_limit": 50, "configurable": {"thread_id": thread_id}}
    )
except GraphRecursionError:
    # Get last checkpointed state
    last_state = graph.get_state(config)
    return {"error": "Recursion limit reached", "last_state": last_state}
```

**Loop Termination:**
- Use conditional edges to route to END when termination condition met
- Track iteration count in state
- Explicitly check limits in routing functions

### 3.7 Node Design Principles

**Single Responsibility:**
- Each node should do ONE thing well
- Avoid side effects (use tasks for side effects)
- Make nodes independently testable

**Determinism and Idempotency:**
- Nodes should be deterministic (same input → same output)
- Wrap non-deterministic operations (random, time, external APIs) in `@task`
- Tasks are cached in checkpointer - won't re-run on resume

**State Updates:**
- Nodes return partial state updates (only changed fields)
- Use reducers for accumulating lists
- Don't mutate state directly (return new values)

### 3.8 Streaming and Observability

**Streaming:**
- Use `graph.stream()` for real-time updates
- Stream modes: `"values"`, `"updates"`, `"messages"`
- Keep users engaged during long-running workflows

**LangSmith Integration:**
- Automatic tracing when LangSmith API key configured
- Visualize execution paths, state transitions
- Monitor performance, token usage, costs

### 3.9 Configuration Parameters

**Workflow Configuration:**
- **Embedding Model**: `mxbai-embed-large:latest` (suitable for Spanish content)
- **Semantic Search Top-K**: 50 (configurable, can be tuned based on performance)
- **Language Handling**: Quotes can be in any language; all concepts must be in Spanish
- **LLM Retries**: Handled by LangChain framework (automatic retries with exponential backoff)
- **Max Concurrency**: Set in config when invoking (default: unlimited, but can limit for rate limiting)
- **Recursion Limits**: Phase 1: 10 supersteps, Phase 2: 20 supersteps (includes human wait time)

**Transactionality:**
- Database-Obsidian sync: Use compensation pattern (not true transactions)
- Phase 3 operations: Create DB records first, then Obsidian files
- If Obsidian fails: Mark DB records for cleanup, log error
- Recovery: Background job to sync missing Obsidian files from DB

## 4. Iterative Extraction Workflow

### Overview
The workflow uses an iterative refinement approach with two main phases:
1. **LLM Self-Improvement Loop**: Autonomous extraction and self-critique until quality standards are met
2. **Human Review Loop**: Human-guided refinement until explicit approval

**LangGraph Architecture:**
- Uses StateGraph (Graph API) for explicit control flow
- Checkpointer required for HITL (Phase 2)
- Parallel execution for independent operations (Call 1.1b, 1.1e)
- Conditional edges for loop control and routing

### 4.1 Phase 1: LLM Self-Improvement Loop

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

### 4.2 Phase 2: Human Review Loop

**Step 2.1: Present Comprehensive Report**

**Implementation**: Use `interrupt()` to pause execution and present report to human.

```python
def present_for_review(state: ConceptExtractionState):
    report = generate_comprehensive_report(state)
    
    # Pause execution - state is automatically checkpointed
    interrupt({
        "action": "human_review",
        "report": report,
        "extraction_summary": summarize_extraction(state)
    })
    
    # Execution resumes here after human provides feedback
    return {}
```

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

**Implementation**: Human provides feedback via UI/API, which updates state and resumes workflow.

Human reviewer has two options:

- **Approve**: Accept the entire extraction as-is and proceed to Phase 3
- **Provide Feedback**: Submit free-form text feedback describing desired changes
  - Feedback can address any aspect: concepts, relations, quote attributions
  - Examples: "Concept 2 is too broad, split it", "Merge concepts 3 and 5", "Add relation between X and Y", "Quote 7 should support concept 1"
  - LLM will interpret feedback and generate a revised proposal

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

### 4.3 Phase 3: Commit to Database

**Step 3.1: Create Graph Elements**
- Create new Concept nodes in database
- Create new relations (with automatic bidirectional pairs)
- Create SUPPORTS relations from quotes to concepts

**Step 3.2: Create Obsidian Notes**
- Create markdown file for each new concept in `08 - Ideas/` directory (Zettels)
- Follow the established Obsidian template structure:
  
  **Frontmatter** (YAML):
  ```yaml
  ---
  entity_id: [UUID]
  entity_type: Concept
  short_summary: [30 words max, LLM-generated]
  summary: [100 words max, LLM-generated]
  concept_relations:
    GENERALIZES: [UUID1, UUID2]
    PART_OF: [UUID3]
    # ... other relations with UUIDs
  ---
  ```
  
  **Content Structure**:
  ```markdown
  # [Title]
  
  ## Concepto
  [Core concept content - what the concept IS]
  
  ## Análisis  
  [Personal analysis, insights, and understanding]
  
  ## Conexiones
  - GENERALIZES: [[Concept Name 1]], [[Concept Name 2]]
  - PART_OF: [[Concept Name 3]]
  - OPPOSES: 
  - SIMILAR_TO: 
  - RELATES_TO: 
  [All 9 relation types listed, even if empty]
  
  ## Fuente
  [Source reference, if applicable (Source quotes in this case)]
  ```

- Resolve concept UUIDs to names for Obsidian `[[links]]` in Conexiones section
- Maintain bidirectional consistency between frontmatter (UUIDs) and Conexiones (names)

**Step 3.3: Update Processing Status**
- Set Content node's `processed_date` to current timestamp

### 4.4 Workflow Safeguards

**Loop Limits (Recursion Limits):**
- Phase 1 (Self-Improvement): Maximum 10 supersteps (includes all iterations)
  - Each iteration = 1 superstep (extraction → critique → refinement)
  - Hard limit prevents infinite loops
  - If limit reached: Present latest iteration to user, allow manual approval
- Phase 2 (Human Review): Maximum 20 supersteps (includes human wait time)
  - Each human feedback cycle = 1 superstep
  - Human wait time doesn't count toward limit (execution paused)
  - If limit reached: Abort process, save current state for manual review

**Convergence:**
- Phase 1: LLM self-improvement should converge based on quality checklist
  - Track quality improvement across iterations
  - Exit early if quality passes before max iterations
- Phase 2: Human feedback should guide convergence
  - Quality checklist still considered, but human intent takes precedence
  - Human can explicitly approve even if quality issues remain

**Quality Over Speed:**
- No time pressure to complete quickly
- Iterations continue until quality standards are met or limits reached
- Human approval is the ultimate quality gate
- Checkpointing allows pausing/resuming without losing progress

**Error Recovery & Resilience:**
- **Checkpointing**: Automatic at every superstep
  - State saved before each node execution
  - Can resume from any checkpoint after failure
  - Successful nodes in failed superstep are cached (won't re-run)
- **Retry Policies**: Applied to nodes with transient failures
  - Semantic search: 3 retries with exponential backoff
  - LLM calls: Handled by LangChain (automatic retries)
  - Database operations: 3 retries with linear backoff
- **Error Handling Strategy**:
  - Transient errors: Automatic retry via RetryPolicy
  - LLM errors: Store in state, route back to LLM for adjustment
  - User-fixable errors: Interrupt for human input
  - Unexpected errors: Log, save state, allow manual recovery
- **Database-Obsidian Sync** (Compensation Pattern):
  - Phase 3: Create DB records first, then Obsidian files
  - If Obsidian fails: Mark DB records with `obsidian_sync_pending=True`
  - Background job syncs missing Obsidian files from DB
  - If DB fails: No Obsidian files created (clean failure)
  - Recovery: Manual sync job can repair inconsistencies

## 5. Glossary

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

## 6. Relation Types

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

## 7. LLM Call Specifications

This section details each LLM call in the workflow, specifying exact inputs and expected outputs.

### Call 1.1a: Extract Candidate Concepts with Source Quotes

**Purpose**: Extract all meaningful atomic concepts from quotes, linking each concept to the quotes that formed it.

**Inputs**:
- **Quotes**: List of all quotes from the content node
  - Each quote should include: `quote_id`, `quote_text`, `content_id` (for context)
- **Content Metadata**: Basic info about the source content (title, author, category) for context
- **Quality Guidelines**: Atomicity principles, language requirements (Spanish), examples

**Output Structure**:
```python
{
  "candidate_concepts": [
    {
      "concept_id": "temp_1",  # Temporary ID for tracking
      "title": "Título del concepto en español",
      "concept": "Contenido del concepto...",  # Core concept description
      "analysis": "Análisis personal...",  # LLM-generated analysis
      "source_quote_ids": ["quote_1", "quote_3", "quote_7"],  # Quotes that formed this concept
      "rationale": "Why this concept was extracted from these quotes"
    }
  ],
  "unattributed_quotes": ["quote_5"],  # Quotes that don't form any concept (if any)
  "extraction_notes": "Any observations about the extraction process"
}
```

**Notes**:
- Duplicate detection is handled separately in Call 1.1b, so existing concepts are not provided as context here
- The `analysis` field is generated by the LLM during extraction
- Output includes only quote IDs, not full quote text 

---

### Call 1.1b: Duplicate Detection (per candidate concept)

**Purpose**: Determine if each candidate concept is a duplicate of an existing concept.

**Inputs**:
- **Candidate Concept**: One concept from 1.1a (title, concept, analysis)
- **Similar Existing Concepts**: Top 50 concepts from semantic search
  - Each should include: `concept_uuid`, `title`, `summary_short`, `summary`

**Output Structure**:
```python
{
  "candidate_concept_id": "temp_1",
  "is_duplicate": true,
  "existing_concept_uuid": "uuid_123",  # If duplicate
  "existing_concept_name": "Nombre del concepto existente",  # If duplicate
  "confidence": 0.95,  # How confident is this duplicate detection?
  "reasoning": "Explanation of why it's a duplicate or not",
  "quote_ids_to_transfer": ["quote_1", "quote_3", "quote_7"]  # Quotes to attribute to existing concept
}
```

**Execution Strategy**:
- One LLM call per candidate concept
- **Parallel Execution**: Use LangGraph's parallel node execution (fan-out/fan-in pattern)
  - Fan-out: Route to multiple parallel nodes (one per candidate concept)
  - All parallel nodes execute in same superstep (atomic success/failure)
  - Fan-in: Aggregate results from all parallel nodes
  - Alternative: Use `@task` decorator in Functional API for simpler parallel execution
- Each call is independent and can run concurrently
- Results accumulated in state using list reducer (operator.add)

**Notes**:
- The LLM determines if a concept is a duplicate (no fixed threshold)
- Only `title` and `summary_short` are provided for existing concepts (no relations or other metadata)

---

### Call 1.1c: Generate Relation Search Queries

**Purpose**: Generate semantic search queries to find existing concepts that might relate to novel concepts.

**Inputs**:
- **Novel Concepts**: List of concepts that passed duplicate detection (title, concept, analysis)
- **Relation Types**: All 9 relation types with descriptions
- **Existing Concept Examples**: (Optional?) Sample existing concepts to understand the graph structure

**Output Structure**:
```python
{
  "concept_queries": [
    {
      "concept_id": "temp_1",
      "relation_queries": {
        "GENERALIZES": [
          "query 1 for finding concepts this generalizes",
          "query 2 for finding concepts this generalizes"
        ],
        "SPECIFIC_OF": [
          "query 1 for finding more general concepts",
          "query 2 for finding more general concepts"
        ],
        "PART_OF": [
          "query 1 for finding parent systems",
          "query 2 for finding parent systems"
        ],
        "HAS_PART": [
          "query 1 for finding components",
          "query 2 for finding components"
        ],
        "OPPOSES": [
          "query 1 for finding opposing concepts",
          "query 2 for finding opposing concepts"
        ],
        "SIMILAR_TO": [
          "query 1 for finding similar concepts",
          "query 2 for finding similar concepts"
        ],
        "RELATES_TO": [
          "query 1 for finding related concepts",
          "query 2 for finding related concepts"
        ],
        "SUPPORTS": [],  # Usually not used for concept-to-concept
        "SUPPORTED_BY": []  # Usually not used for concept-to-concept
      }
    }
  ]
}
```

**Notes**:
- Generate exactly 2 queries per relation type for each novel concept
- All 9 relation types are considered for all concepts (no skipping)
- Queries should be in Spanish since concepts are in Spanish

---

### Call 1.1d: Semantic Search for Relation Candidates

**Note**: This is NOT an LLM call - it's a vector search operation.

**Process**:
- Execute all queries from 1.1c against concept embeddings
- Deduplicate results
- Return pool of candidate concepts

**Output**: List of existing concept UUIDs with their metadata (title, summary_short)

**Note**: This is not an LLM call - it's a vector search operation executed after Call 1.1c

---

### Call 1.1e: Create Relations (per novel concept)

**Purpose**: Determine which relations should exist for a single novel concept, considering both other novel concepts and existing concepts.

**Execution Strategy**:
- One LLM call per novel concept
- **Parallel Execution**: Use LangGraph's parallel node execution (fan-out/fan-in pattern)
  - Fan-out: Route to multiple parallel nodes (one per novel concept)
  - All parallel nodes execute in same superstep (atomic success/failure)
  - Fan-in: Aggregate results from all parallel nodes
  - Alternative: Use `@task` decorator in Functional API for simpler parallel execution
- Each call is independent and can run concurrently
- Results accumulated in state using list reducer (operator.add)

**Inputs** (per call):
- **Target Novel Concept**: The concept for which relations are being determined (title, concept, analysis, concept_id)
- **Other Novel Concepts**: All other novel concepts (for new→new relation detection)
  - Each includes: `concept_uuid`, `title`, `summary_short`
- **Existing Concept Candidates**: Pool of existing concepts from Step 1.1d (configurable, default 50)
  - Each includes: `concept_uuid`, `title`, `summary_short`
- **Relation Type Definitions**: Descriptions of all 9 relation types

**Output Structure** (per call):
```python
{
  "target_concept_id": "temp_1",
  "relations": [
    {
      "target_concept_id": "uuid_456",  # Can be temp ID (novel) or UUID (existing)
      "target_is_novel": false,
      "relation_type": "GENERALIZES",  # Forward relation type
      "explanation": "Why this relation exists",
      "confidence": 0.85
    },
    {
      "target_concept_id": "temp_2",  # Another novel concept
      "target_is_novel": true,
      "relation_type": "PART_OF",
      "explanation": "Why this relation exists",
      "confidence": 0.90
    }
  ],
  "relation_notes": "Any observations about relation creation for this concept"
}
```

**Notes**:
- Confidence scores are included for each relation (no fixed threshold - LLM decides)
- No limit on number of relations per concept
- Relations are determined by comparing the target concept against:
  - All other novel concepts (for new→new relations)
  - The pool of existing concept candidates (for existing→new relations)

---

### Call 1.2: Self-Critique

**Purpose**: Validate the extraction against quality checklist and identify issues.

**Inputs**:
- **Extraction Results**: Complete output from Step 1.1
  - Novel concepts with quote attributions
  - Existing concepts with new quote attributions
  - Relations created
- **Quality Checklist**: All criteria (atomicity, distinctness, quote coverage, relation accuracy, language, edge cases)
- **Original Quotes**: All quotes for reference

**Output Structure**:
```python
{
  "quality_assessment": {
    "atomicity": {
      "passes": false,
      "issues": [
        {
          "concept_id": "temp_2",
          "issue": "Contains multiple ideas: X and Y",
          "severity": "high"
        }
      ]
    },
    "distinctness": {
      "passes": true,
      "issues": []
    },
    "quote_coverage": {
      "passes": false,
      "issues": [
        {
          "quote_id": "quote_5",
          "issue": "Quote not attributed to any concept",
          "severity": "medium"
        }
      ]
    },
    "relation_accuracy": {
      "passes": true,
      "issues": []
    },
    "language": {
      "passes": true,
      "issues": []
    },
    "edge_cases": {
      "passes": true,
      "issues": []
    }
  },
  "overall_passes": false,
  "critique_summary": "Overall assessment and key issues to address",
  "improvement_suggestions": [
    "Split concept temp_2 into two separate concepts",
    "Review quote_5 to determine if it should support an existing concept"
  ]
}
```


**Notes**:
- Critique should be as detailed as necessary to guide the refinement step
- Should suggest specific fixes and actionable improvements
- Overall confidence score is not included (not useful for decision-making)

---

### Call 1.3: Refinement

**Purpose**: Refine the extraction based on self-critique.

**Inputs**:
- **Current Extraction**: Complete extraction from Step 1.1
- **Critique**: Output from Call 1.2
- **Original Quotes**: All quotes for reference
- **Quality Checklist**: For reference during refinement

**Output Structure**:
```python
{
  "refined_extraction": {
    # Same structure as Step 1.1 output
    "novel_concepts": [...],
    "existing_concepts_with_quotes": [...],
    "relations": [...]
  },
  "refinement_notes": "Summary of refinement process and key changes made"
}
```

**Notes**:
- Refinement addresses all issues from the critique comprehensively (not iteratively)
- Critique should not suggest contradictory changes (if it does, that's a quality issue to address)
- No iteration tracking needed

---

### Call 2.3: Incorporate Human Feedback

**Purpose**: Update extraction based on human feedback.

**Inputs**:
- **Current Extraction**: Latest extraction proposal (from Phase 1 or previous iteration)
- **Human Feedback**: Free-form text feedback
- **Quality Checklist**: To ensure feedback incorporation maintains quality
- **Original Quotes**: For reference
- **Extraction History**: (Optional?) Previous iterations for context

**Output Structure**:
```python
{
  "revised_extraction": {
    # Same structure as Step 1.1 output
    "novel_concepts": [...],
    "existing_concepts_with_quotes": [...],
    "relations": [...]
  },
  "feedback_interpretation": "How the LLM interpreted the human feedback",
  "unresolved_feedback": "Any feedback that couldn't be addressed (if any)",
  "questions_for_human": "Any clarifications needed (if any)"
}
```

**Notes**:
- If feedback is ambiguous, LLM should make its best guess (no clarification requests)
- No quality checklist validation - human feedback takes precedence
- If feedback contradicts quality principles, user's intent is followed (user knows best) 