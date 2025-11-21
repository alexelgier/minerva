# Workflow Documentation

Detailed workflow documentation for both graphs in the zettel_agent module.

## Table of Contents

- [Quote Parse Graph Workflow](#quote-parse-graph-workflow)
- [Concept Extraction Graph Workflow](#concept-extraction-graph-workflow)
- [State Transitions](#state-transitions)
- [Error Recovery](#error-recovery)

---

## Quote Parse Graph Workflow

### Overview

The Quote Parse Graph processes markdown book notes and extracts quotes with metadata, storing them in Neo4j.

### Execution Flow

```
┌─────────────┐
│  __start__  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  read_file  │  Read markdown file from filesystem
└──────┬──────┘
       │
       ▼
┌─────────────┐
│make_summary │  Generate book summary using LLM
└──────┬──────┘
       │
       ▼
┌─────────────┐
│parse_quotes │  Extract quotes from "# Citas" section
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│get_or_create_    │  Get existing author or create new
│author            │  with web search enrichment
└──────┬───────────┘
       │
       ▼
┌─────────────┐
│ write_to_db │  Store book, quotes, and relationships
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   __end__   │
└─────────────┘
```

### Step-by-Step Details

#### Step 1: Read File

**Node:** `read_file`

**Input:**
- `file_path`: Path to markdown file

**Process:**
- Reads file content asynchronously
- Stores content in state

**Output:**
- `file_content`: Full markdown content

**Error Handling:**
- File not found → Exception
- Permission error → Exception

#### Step 2: Make Summary

**Node:** `make_summary`

**Input:**
- `file_content`: Markdown content
- `title`: Book title
- `author`: Book author

**Process:**
- Sends content to LLM (Gemini 2.5 Flash Lite)
- Requests summary (100 words) and short summary (30 words)
- Uses structured output (SummaryResponse)

**Output:**
- `summary`: Detailed summary
- `summary_short`: Short summary

**LLM Prompt:**
```
You are a helpful assistant that generates summaries for a book from the notes the user has taken about the book.
Book title: {title}
Book author: {author}
Here are the notes the user has taken about the book:
{file_content}
---
Generate a summary and a short summary of the book.
```

#### Step 3: Parse Quotes

**Node:** `parse_quotes`

**Input:**
- `file_content`: Markdown content
- `title`: Book title
- `author`: Book author
- `summary`: Book summary
- `summary_short`: Short summary

**Process:**
- Finds "# Citas" section
- Extracts quotes by section
- Parses page references
- Creates Content object
- Creates Quote objects

**Output:**
- `book`: Content object
- `quotes`: List of Quote objects
- `sections`: List of section names

**Quote Format:**
```markdown
# Citas

## Section Name

Quote text here

123

Another quote

124-125
```

**Parsing Logic:**
- Split by "## Section Name" headers
- Split quotes by blank lines
- Extract page references (numbers at end)
- Minimum quote length: 20 characters

#### Step 4: Get or Create Author

**Node:** `get_or_create_author`

**Input:**
- `author`: Author name
- `title`: Book title

**Process:**
- Searches for existing Person by name (case-insensitive)
- If found: Returns existing author (assumed to be well-formed)
- If not found:
  1. Enriches author information with web search using Gemini's Google Search tool
  2. Creates Person with enriched data (or basic data if enrichment fails)
- Stores Person in state

**Output:**
- `parsed_author`: Person object

**Person Creation (if author doesn't exist):**
- First attempts web search enrichment
- Creates with enriched data if available, otherwise uses basic data:
```python
Person(
    name=author,
    summary=enriched_summary or f"Author of {title}",
    summary_short=enriched_summary_short or f"Author of {title}",
    occupation=enriched_occupation or "Author"
)
```

**Web Search Enrichment:**
- Uses Gemini's built-in Google Search tool (grounding)
- Automatically searches for author biography information
- Synthesizes comprehensive summary, short summary, and occupation
- Only enriches newly created authors (existing authors are returned as-is)

#### Step 5: Write to Database

**Node:** `write_to_db`

**Input:**
- `book`: Content object
- `parsed_author`: Person object
- `quotes`: List of Quote objects

**Process:**
1. Create Content node in Neo4j
2. Create AUTHORED_BY relationship
3. Create Quote nodes with embeddings (via Neo4jVector)
4. Create QUOTED_IN relationships

**Output:**
- `book`: Content object
- `content_uuid`: UUID of created Content

**Embedding Generation:**
- Uses Neo4jVector (langchain-neo4j)
- Automatically generates embeddings
- Stores in quote_embeddings_index

---

## Concept Extraction Graph Workflow

### Overview

The Concept Extraction Graph extracts atomic concepts from quotes using a sophisticated 3-phase workflow with LLM self-improvement and human review.

### Execution Flow

```
Phase 1: LLM Self-Improvement Loop
┌─────────────────────────────┐
│check_content_processed      │  Verify content not already processed
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│load_content_quotes          │  Load all quotes for content
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│extract_candidate_concepts   │  LLM extracts candidate concepts
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│detect_duplicates_all        │  Semantic search + LLM duplicate detection
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│generate_relation_queries    │  Generate search queries for relations
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│search_relation_candidates   │  Vector search for relation candidates
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│create_relations_all         │  LLM determines relations
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│self_critique                │  LLM validates against quality checklist
└──────────────┬──────────────┘
               │
               ├─────────────────┐
               │                 │
               ▼                 │
┌─────────────────────────────┐ │
│refine_extraction            │ │  LLM refines based on critique
└──────────────┬──────────────┘ │
               │                 │
               └─────────────────┘ (loop until quality passes or max iterations)
               │
               ▼
┌─────────────────────────────┐
│present_for_review           │  Generate report and interrupt for human
└──────────────┬──────────────┘

Phase 2: Human Review Loop
               │
               ├─────────────────┐
               │                 │
               ▼                 │
┌─────────────────────────────┐ │
│incorporate_feedback         │ │  LLM incorporates human feedback
└──────────────┬──────────────┘ │
               │                 │
               └─────────────────┘ (loop until approval or max iterations)
               │
               ▼
┌─────────────────────────────┐
│create_concepts_db           │  Create Concept nodes in Neo4j
└──────────────┬──────────────┘

Phase 3: Commit to Database
               │
               ▼
┌─────────────────────────────┐
│create_relations_db          │  Create bidirectional concept relations
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│create_supports_relations    │  Create SUPPORTS relations (quotes → concepts)
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│create_obsidian_files        │  Generate Obsidian zettel markdown files
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│update_processed_date        │  Mark content as processed
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│         __end__             │
└─────────────────────────────┘
```

### Phase 1: LLM Self-Improvement Loop

#### Step 1.1: Check Content Processed

**Node:** `check_content_processed`

**Purpose:** Verify content hasn't been processed already.

**Input:**
- `content_uuid`: UUID of the content to process
- `user_suggestions`: Optional freeform text suggestions (from input state, passed through)

**Process:**
- Load Content node by UUID
- Check `processed_date` field
- Exit early if already processed

**Output:**
- `content`: Content object (if not processed)
- `warnings`: Warning if already processed
- `phase`: "end" if already processed

#### Step 1.2: Load Content Quotes

**Node:** `load_content_quotes`

**Purpose:** Load all quotes for the content.

**Process:**
- Query Neo4j for quotes linked to content
- Exclude embeddings (performance)
- Store in state

**Output:**
- `quotes`: List of Quote objects
- `phase`: "extraction" (if quotes found)

#### Step 1.3: Extract Candidate Concepts

**Node:** `extract_candidate_concepts`

**Purpose:** Extract candidate concepts from quotes (Call 1.1a).

**LLM:** Gemini 2.5 Pro

**Process:**
1. Format quotes with IDs
2. Include user suggestions if provided
3. Send to LLM with extraction prompt
4. Parse structured response (CandidateConceptsResponse)
5. Store candidate concepts

**Input:**
- `quotes`: List of Quote objects
- `content`: Content object
- `user_suggestions`: Optional freeform text suggestions (from input state)

**Output:**
- `candidate_concepts`: List of candidate concept dicts
- `warnings`: Unattributed quotes (if any)

**LLM Prompt:**
- System: Zettelkasten expert role, atomicity guidelines, Spanish output
- User: Content info, all quotes, user suggestions (if provided), extraction instructions

**Quality Criteria:**
- Atomicity (one idea per concept)
- Spanish language
- Quote attribution
- User suggestions considered when provided

#### Step 1.4: Detect Duplicates

**Node:** `detect_duplicates_all`

**Purpose:** Detect duplicate concepts (Call 1.1b).

**Process:**
For each candidate concept:
1. Generate embedding (title + concept text)
2. Vector search for similar concepts (top 50, threshold 0.7)
3. LLM determines if duplicate
4. Separate novel from duplicates

**Output:**
- `novel_concepts`: Non-duplicate concepts
- `existing_concepts_with_quotes`: Duplicates with quote transfers
- `duplicate_detections`: All detection results

**LLM Prompt:**
- System: Duplicate detection guidelines
- User: Candidate concept, similar existing concepts

**Duplicate Criteria:**
- Semantic equivalence (not just textual similarity)
- Same core idea, even if expressed differently

#### Step 1.5: Generate Relation Queries

**Node:** `generate_relation_queries`

**Purpose:** Generate search queries for finding related concepts (Call 1.1c).

**LLM:** Gemini 2.5 Flash

**Process:**
1. Format novel concepts
2. Send to LLM with relation types
3. Generate 2 queries per relation type per concept
4. Store queries

**Output:**
- `relation_queries`: List of query dicts per concept

**Relation Types:**
- GENERALIZES, SPECIFIC_OF
- PART_OF, HAS_PART
- OPPOSES, SIMILAR_TO, RELATES_TO

#### Step 1.6: Search Relation Candidates

**Node:** `search_relation_candidates`

**Purpose:** Vector search for relation candidates (Call 1.1d).

**Process:**
1. For each query, generate embedding
2. Vector search concepts (top 10, threshold 0.7)
3. Deduplicate results
4. Store candidate pool

**Output:**
- `relation_candidates`: Pool of candidate concepts

**Note:** This is vector search, not LLM call.

#### Step 1.7: Create Relations

**Node:** `create_relations_all`

**Purpose:** Determine relations between concepts (Call 1.1e).

**LLM:** Gemini 2.5 Pro

**Process:**
For each novel concept:
1. Compare with other novel concepts
2. Compare with relation candidates
3. LLM determines relations
4. Store relations

**Output:**
- `relations`: List of relation dicts

**LLM Prompt:**
- System: Relation determination guidelines
- User: Target concept, other novels, candidates, relation types

#### Step 1.8: Self-Critique

**Node:** `self_critique`

**Purpose:** Validate extraction against quality checklist (Call 1.2).

**LLM:** Gemini 2.5 Pro

**Process:**
1. Format extraction results
2. Include user suggestions if provided
3. Send to LLM with quality checklist
4. Parse structured response (SelfCritiqueResponse)
5. Store assessment

**Input:**
- `novel_concepts`: List of novel concepts
- `existing_concepts_with_quotes`: List of existing concepts with quotes
- `relations`: List of relations
- `quotes`: List of quotes
- `user_suggestions`: Optional freeform text suggestions (from input state)

**Output:**
- `quality_assessment`: Quality assessment dict
- `critique_log`: Critique entry

**Quality Criteria:**
- Atomicity
- Distinctness
- Quote coverage
- Relation accuracy
- Language
- Edge cases
- User suggestions considered when provided

#### Step 1.9: Refine Extraction

**Node:** `refine_extraction`

**Purpose:** Refine extraction based on critique (Call 1.3).

**LLM:** Gemini 2.5 Pro

**Process:**
1. Format current extraction and critique
2. Include user suggestions if provided
3. Send to LLM for refinement
4. Parse structured response (RefinementResponse)
5. Update extraction

**Input:**
- `novel_concepts`: Current novel concepts
- `existing_concepts_with_quotes`: Current existing concepts with quotes
- `relations`: Current relations
- `quality_assessment`: Quality assessment from critique
- `user_suggestions`: Optional freeform text suggestions (from input state)

**Output:**
- `novel_concepts`: Refined concepts
- `relations`: Refined relations
- `existing_concepts_with_quotes`: Refined attributions

**Loop Control:**
- Continues if quality doesn't pass
- Max 10 iterations
- Exits to Phase 2 when quality passes

### Phase 2: Human Review Loop

#### Step 2.1: Present for Review

**Node:** `present_for_review`

**Purpose:** Generate report and interrupt for human review.

**Process:**
1. Generate comprehensive report:
   - New concepts
   - Relations
   - Existing concepts with quotes
   - Critique log
2. Call `interrupt()` to pause execution
3. Wait for human feedback

**Output:**
- Empty dict (execution paused)

**Report Contents:**
- All novel concepts with details
- All relations with explanations
- Quote attributions
- Quality assessment
- Critique log

**Resume:**
- Human provides feedback via LangGraph API
- State updated with `human_feedback` or `human_approved`
- Execution resumes

#### Step 2.2: Incorporate Feedback

**Node:** `incorporate_feedback`

**Purpose:** Incorporate human feedback into extraction (Call 2.3).

**LLM:** Gemini 2.5 Pro

**Process:**
1. Format current extraction and feedback
2. Send to LLM for incorporation
3. Parse structured response (FeedbackIncorporationResponse)
4. Update extraction

**Output:**
- `novel_concepts`: Revised concepts
- `relations`: Revised relations
- `existing_concepts_with_quotes`: Revised attributions

**Loop Control:**
- Continues if not approved
- Max 20 iterations
- Exits to Phase 3 when approved

### Phase 3: Commit to Database

#### Step 3.1: Create Concepts

**Node:** `create_concepts_db`

**Purpose:** Create Concept nodes in Neo4j.

**Process:**
1. For each novel concept:
   - Create Concept object
   - Generate summary fields
   - Create in Neo4j
   - Store UUID mapping (temp_id → uuid)

**Output:**
- `created_concept_uuids`: List of {temp_id, uuid} mappings

#### Step 3.2: Create Relations

**Node:** `create_relations_db`

**Purpose:** Create bidirectional concept relations.

**Process:**
1. Resolve temp IDs to UUIDs
2. For each relation:
   - Resolve source and target UUIDs
   - Create bidirectional relation
   - Handle both novel and existing concepts

**Output:**
- Empty dict

**Relation Creation:**
- Uses `create_concept_relation()`
- Automatically creates bidirectional pairs

#### Step 3.3: Create SUPPORTS Relations

**Node:** `create_supports_relations`

**Purpose:** Create SUPPORTS relations from quotes to concepts.

**Process:**
1. For novel concepts:
   - Resolve concept UUID
   - Create SUPPORTS for each source quote
2. For existing concepts:
   - Create SUPPORTS for transferred quotes

**Output:**
- Empty dict

#### Step 3.4: Create Obsidian Files

**Node:** `create_obsidian_files`

**Purpose:** Generate Obsidian zettel markdown files.

**Process:**
1. For each novel concept:
   - Resolve concept relations
   - Resolve concept names
   - Generate frontmatter
   - Generate content
   - Write file to "08 - Ideas" directory

**Output:**
- `created_files`: List of file paths

**File Format:**
- YAML frontmatter with metadata
- Markdown content with sections
- Concept links in Conexiones section

#### Step 3.5: Update Processed Date

**Node:** `update_processed_date`

**Purpose:** Mark content as processed.

**Process:**
1. Update Content node
2. Set `processed_date` to current timestamp

**Output:**
- `phase`: "end"

---

## State Transitions

### Quote Parse Graph

**Linear State Flow:**
```
Initial → file_content → summary → quotes → author → content_uuid → End
```

**No loops or conditionals.**

### Concept Extraction Graph

**Phase Transitions:**
```
extraction → human_review → commit → end
```

**Phase 1 Loop:**
```
extract → critique → [refine → critique] → human_review
```

**Phase 2 Loop:**
```
present → [incorporate → present] → commit
```

**Termination Conditions:**
- Phase 1: Quality passes OR max iterations (10)
- Phase 2: Human approval OR max iterations (20)
- Any phase: Critical errors

---

## Error Recovery

### Error Types

**1. Transient Errors:**
- Network issues
- Rate limits
- **Recovery:** Automatic retry (LangChain)

**2. LLM Errors:**
- Parsing failures
- Invalid responses
- **Recovery:** Store in state, continue or exit

**3. Database Errors:**
- Connection failures
- Query errors
- **Recovery:** Exception handling, state updates

**4. User Errors:**
- Invalid input
- Missing data
- **Recovery:** Early exit, error message

### Checkpointing

**Automatic Checkpointing:**
- State saved at every superstep
- Can resume from last checkpoint
- Successful nodes cached

**Resume After Error:**
1. Identify last successful checkpoint
2. Review state
3. Fix issue
4. Resume from checkpoint

### Error Accumulation

**Pattern:**
- Errors stored in state
- Warnings stored in state
- Continue processing if possible
- Report all errors at end

---

## See Also

- [API Reference](API.md) - Complete API documentation
- [Architecture Documentation](ARCHITECTURE.md) - Technical architecture
- [Developer Guide](DEVELOPER.md) - Extension guide

