# Processing Pipeline Documentation

## 🔄 Overview

The Minerva processing pipeline is a multi-stage system that extracts entities and relationships from journal entries using a combination of LLM processing and human curation. The pipeline uses Temporal for workflow orchestration and includes custom serialization handling to ensure type safety across all stages.

## 🏗️ Pipeline Architecture

```
Journal Entry
     │
     ▼
┌─────────────┐
│   Stage 1   │ ──► Entity Extraction (LLM)
│  Extract    │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Stage 2   │ ──► Entity Curation (Human)
│  Curate     │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Stage 3   │ ──► Feelings Extraction (LLM)
│  Feelings   │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Stage 4   │ ──► Relationship Extraction (LLM)
│  Relate     │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Stage 5   │ ──► Relations+Feelings Curation (Human)
│  Validate   │
└─────────────┘
     │
     ▼
┌─────────────┐
│   Stage 6   │ ──► Knowledge Graph Update
│   Store     │
└─────────────┘
```

## 🧩 Stage Details

### Stage 1: Entity Extraction

**Purpose**: Extract entities from journal text using LLM processing

**Components**:
- `ExtractionService`: Main orchestration service
- `EntityExtractionOrchestrator`: Coordinates entity processors
- `EntityProcessorStrategy`: Individual entity type processors
- `LLMService`: Interfaces with Ollama for text processing

**Process**:
1. Journal entry received via API
2. Text preprocessed and context prepared
3. Vector search retrieves relevant concepts from knowledge base (RAG)
4. LLM processes text for each entity type:
   - Person (people mentioned)
   - Concept (abstract ideas and concepts)
   - Event (activities/occurrences)
   - Project (ongoing initiatives)
   - Content (books, articles, etc.)
   - Consumable (resources being consumed)
   - Place (locations)
5. **Entity Conversion**: Raw LLM response objects converted to proper domain entities with UUID fields
6. Entities extracted with confidence scores and embeddings
7. **UUID Validation**: All entities validated to ensure they have proper UUID fields
8. Results queued for human curation

**Entity Processing Order**:
```python
processing_order = [
    'Person',         # People first
    'Concept',        # Concepts
    'Project',        # Projects
    'Consumable',     # Consumables
    'Content',        # Content
    'Event',          # Events
    'Place',          # Places
]
```

### Stage 2: Entity Curation

**Purpose**: Human validation and refinement of extracted entities

**Components**:
- `CurationManager`: Manages curation queue
- `CurationQueue`: SQLite database for curation data
- Frontend curation interface

**Process**:
1. Entities queued in curation database
2. Human curator reviews extracted entities
3. Entities can be:
   - Accepted as-is
   - Modified (name, summary, properties)
   - Deleted (false positives)
   - Added (missed entities)
4. Curation actions tracked in database
5. Curated entities proceed to relationship extraction

### Stage 3: Feelings Extraction

**Purpose**: Extract feelings using curated entities as context

**Components**:
- `ExtractionService.extract_feelings`: Main orchestration service
- `EmotionFeelingProcessor`: Extracts FeelingEmotion entities (person emotions)
- `ConceptFeelingProcessor`: Extracts FeelingConcept entities (person feelings about concepts)
- `LLMService`: Interfaces with Ollama for text processing

**Process**:
1. Uses curated entities from Stage 2 as context
2. LLM processes text for feelings:
   - FeelingEmotion (emotional states of people)
   - FeelingConcept (feelings about specific concepts)
3. Feelings extracted with confidence scores and embeddings
4. Results combined with relationships for unified curation

### Stage 4: Relationship Extraction

**Purpose**: Extract relationships between curated entities using LLM

**Components**:
- `RelationshipProcessor`: Processes general entity relationships
- `ConceptRelationProcessor`: Processes typed concept relationships
- `LLMService`: Analyzes entity pairs for relationships
- `SpanProcessingService`: Handles text span references

**Process**:
1. Curated entities analyzed for relationships
2. **General Relationships**: LLM processes entity pairs for general connections
3. **Concept Relations**: LLM processes concept pairs for typed relationships
4. Relationships extracted with context:
   - Relationship type (general or typed)
   - Confidence score
   - Text spans where relationship is mentioned
5. Relationships queued for human validation

**Concept Relation Types**:
- `GENERALIZES/SPECIFIC_OF`: Hierarchical relationships
- `PART_OF/HAS_PART`: Compositional relationships
- `SUPPORTS/SUPPORTED_BY`: Evidential relationships
- `OPPOSES`: Oppositional relationships
- `SIMILAR_TO`: Similarity relationships
- `RELATES_TO`: General relationships

### Stage 5: Relations+Feelings Curation

**Purpose**: Human validation of extracted relationships and feelings

**Components**:
- `CurationManager`: Manages relationship curation
- Frontend curation interface

**Process**:
1. Relationships and feelings queued for human review
2. Human curator validates both relationships and feelings
3. Items can be:
   - Accepted as-is
   - Modified (type, strength, context for relations; intensity, duration for feelings)
   - Deleted (false positives)
   - Added (missed relationships or feelings)
4. Validated items proceed to storage

### Stage 6: Knowledge Graph Update

**Purpose**: Store validated entities and relationships in Neo4j

**Components**:
- `KnowledgeGraphService`: Manages graph operations
- `Neo4jConnection`: Database connection
- Entity repositories for each type

**Process**:
1. Validated entities stored in Neo4j
2. Entity properties and metadata saved
3. Relationships created between entities
4. Feelings stored as reified relations (connected to Person and optionally Concept)
5. Entity-Document relationships established
6. Text spans linked to entities
7. Processing complete

## ⚙️ Temporal Workflow

The pipeline is orchestrated using Temporal workflows for reliability and scalability.

### Workflow Definition
```python
@workflow.defn(name="JournalProcessing")
class JournalProcessingWorkflow:
    async def run(self, journal_entry: JournalEntry) -> PipelineState:
        # Stage 1-2: Entity Extraction
        entities = await workflow.execute_activity(
            PipelineActivities.extract_entities,
            args=[journal_entry]
        )
        
        # Stage 3: Submit for curation
        await workflow.execute_activity(
            PipelineActivities.submit_entity_curation,
            args=[journal_entry, entities]
        )
        
        # Stage 4: Wait for curation
        curated_entities = await workflow.execute_activity(
            PipelineActivities.wait_for_entity_curation,
            args=[journal_entry]
        )
        
        # Stage 5: Feelings extraction
        feelings = await workflow.execute_activity(
            PipelineActivities.extract_feelings,
            args=[journal_entry, curated_entities]
        )
        
        # Stage 6: Relationship extraction
        relationships = await workflow.execute_activity(
            PipelineActivities.extract_relationships,
            args=[journal_entry, curated_entities]
        )
        
        # Stage 7: Submit relationships and feelings for curation
        combined_items = feelings + relationships
        await workflow.execute_activity(
            PipelineActivities.submit_relationship_curation,
            args=[journal_entry, combined_items]
        )
        
        # Stage 8: Wait for relationship curation
        curated_items = await workflow.execute_activity(
            PipelineActivities.wait_for_relationship_curation,
            args=[journal_entry]
        )
        
        # Stage 9: Write to knowledge graph
        await workflow.execute_activity(
            PipelineActivities.write_to_knowledge_graph,
            args=[journal_entry, curated_entities, curated_items]
        )
```

### Retry Policies
- **LLM Activities**: 5 retries with exponential backoff
- **Database Operations**: 3 retries with linear backoff
- **Curation Activities**: No retries (human-dependent)

### Timeouts
- **Entity Extraction**: 60 minutes maximum
- **Relationship Extraction**: 60 minutes maximum
- **Curation Wait**: 7 days maximum
- **Database Write**: 10 minutes maximum

## 🧠 Vector Search and Concept Extraction

### Vector Search Implementation

**Purpose**: Enable semantic search and retrieval-augmented generation (RAG) for concept extraction

**Components**:
- `Neo4jConnection`: Native vector search capabilities
- `BaseRepository`: Vector search methods for all entities
- `ConceptRepository`: Specialized concept RAG functionality
- `LLMService`: Embedding generation

**Features**:
- **Embedding Generation**: All entities and relations have embeddings based on summary content
- **Vector Indexes**: Neo4j native vector indexes for fast similarity search
- **RAG for Concepts**: Retrieve relevant concepts for LLM context during extraction
- **Similarity Search**: Find similar entities using cosine similarity

**Process**:
1. Entity summaries are embedded using LLM service
2. Embeddings stored in Neo4j with vector indexes
3. During concept extraction, relevant concepts retrieved via vector search
4. Retrieved concepts provided as context to LLM for better extraction

### Concept Extraction

**Purpose**: Extract abstract concepts and ideas from journal entries using Zettelkasten methodology

**Components**:
- `ConceptProcessor`: Extracts concept mentions from text
- `ConceptFeelingProcessor`: Extracts feelings about specific concepts
- `ExtractConceptsPrompt`: LLM prompt for concept extraction
- `ExtractConceptFeelingsPrompt`: LLM prompt for concept feelings

**Three-Pass Approach**:
1. **Pass 1 - Concept Mentions**: Extract concepts mentioned in text
   - Identifies existing concepts (with UUIDs) and new concepts
   - Uses enhanced context system: [[Linked]] + RAG + Recent concepts
   - Automatically merges with existing concepts using LLM-based merging
   - Generates embeddings for all concepts
   - Extracts rich concept data: name, title, concept definition, analysis, source

2. **Pass 2 - Concept Feelings**: Extract feelings about concepts
   - Links people to concepts they think/feel about
   - Only extracts when someone has a clear feeling about a concept
   - Creates Feeling entities with `concept_uuid` field

3. **Pass 3 - Concept Relations**: Extract relationships between concepts
   - Uses LLM to identify typed relationships between concepts
   - Creates bidirectional relationships automatically
   - Supports 9 different relation types for precise connections
   - Validates relations for consistency and removes invalid ones

**Zettelkasten Integration**:
- Syncs Zettel files from Obsidian vault
- Two-stage parsing: section extraction → relation parsing
- Parses Zettel template structure (Concepto, Análisis, Conexiones, Fuente)
- Maintains bidirectional sync between Obsidian and database
- Uses typed relation syntax: `- RELATION_TYPE: [[Concept]]` for concept connections
- **Smart Field Comparison**: Only updates concepts when core content changes
- **LLM-Only Summaries**: All summaries are LLM-generated, no fallbacks allowed
- **Performance Optimized**: Skips unchanged concepts to save resources
- **Standardized Frontmatter**: All YAML keys use centralized constants for consistency

### Field Comparison & Update Logic

The Zettelkasten sync process implements intelligent field comparison to optimize performance:

#### Core Content Fields (Compared for Changes)
- `concept` - Main concept content from "Concepto" section
- `analysis` - Analysis content from "Análisis" section  
- `source` - Source information from "Fuente" section
- `title` - Concept title (derived from filename)

#### LLM-Generated Fields (Not Compared)
- `summary` - Always LLM-generated, regenerated when content changes
- `summary_short` - Always LLM-generated, regenerated when content changes
- `embedding` - Always regenerated when summary changes

#### Update Behavior
1. **Content Changed**: Updates core fields + regenerates summaries via LLM
2. **Content Unchanged**: Skips update entirely (no unnecessary LLM calls)
3. **LLM Required**: System fails fast if no LLM service is available
4. **No Fallbacks**: No fallback summary generation - LLM is mandatory

#### Performance Benefits
- **Efficiency**: Only updates concepts that actually changed
- **Resource Savings**: Avoids unnecessary database writes and LLM calls
- **Quality**: All summaries are high-quality and LLM-generated
- **Reliability**: Fails fast rather than using poor fallback summaries

## 🔑 Entity UUID Handling

### Overview
The processing pipeline ensures all entities have proper UUID fields before entering the curation phase. This prevents `AttributeError` issues and maintains data consistency.

### Entity Conversion Process
1. **LLM Response Objects**: Raw Pydantic models from LLM responses (e.g., `Person`, `Feeling`, `ConceptMention`)
2. **Domain Entity Conversion**: Converted to proper domain entities that inherit from `Node` class
3. **UUID Generation**: Domain entities automatically have UUID fields from `Node` base class
4. **Validation**: Final safety check ensures all entities have UUID fields

### Implementation Details
```python
# Entity conversion in base.py
if hydration_func:
    hydrated_entity = await hydration_func(journal_entry, canonical_name)
else:
    # Convert LLM entity to domain entity
    entity_kwargs = llm_entity.model_dump()
    entity_kwargs['name'] = canonical_name
    entity_class = self.entity_repositories[entity_type].entity_class
    hydrated_entity = entity_class(**entity_kwargs)

# Final safety check
if not hasattr(hydrated_entity, 'uuid'):
    hydrated_entity.uuid = str(uuid4())
```

### Fallback Mechanisms
- **Primary**: Proper domain entity conversion using repository entity classes
- **Secondary**: Error handling for entity class lookup failures
- **Tertiary**: Defensive UUID generation in curation manager
- **Final**: Safety check before entity processing

### Benefits
- **Reliability**: Prevents UUID-related errors in curation pipeline
- **Consistency**: All entities follow the same data model
- **Robustness**: Multiple fallback mechanisms handle edge cases
- **Maintainability**: Clear separation between LLM objects and domain entities

## 🔧 Configuration

### Processing Settings
```python
# Default processing times
default_processing_start: str = "06:00"
default_processing_end: str = "12:00"

# Status polling
max_status_poll_attempts: int = 10
status_poll_interval: float = 0.2
```

### LLM Configuration
- **Model**: Ollama local model
- **Caching**: Enabled for repeated requests
- **Timeout**: 30 seconds per request
- **Retries**: 3 attempts per request

## 📊 Monitoring

### Pipeline Status
- **SUBMITTED**: Journal entry received
- **ENTITY_PROCESSING**: Entity extraction in progress
- **SUBMIT_ENTITY_CURATION**: Entities queued for curation
- **WAIT_ENTITY_CURATION**: Waiting for human curation
- **RELATION_PROCESSING**: Relationship extraction in progress
- **SUBMIT_RELATION_CURATION**: Relationships queued for curation
- **WAIT_RELATION_CURATION**: Waiting for relationship curation
- **DB_WRITE**: Writing to knowledge graph
- **COMPLETED**: Processing complete
- **FAILED**: Processing failed

### Metrics
- Processing time per stage
- Entity extraction accuracy
- Relationship extraction accuracy
- Human curation time
- Error rates and types

## 🛠️ Error Handling

### Retry Logic
- **Transient Errors**: Automatic retry with backoff
- **Permanent Errors**: Fail fast with error reporting
- **Human Errors**: Manual intervention required

### Error Types
- **LLM Errors**: Model unavailable, timeout, parsing errors
- **Database Errors**: Connection issues, constraint violations
- **Validation Errors**: Invalid data format, missing required fields
- **Serialization Errors**: Object type preservation issues (handled by custom data converter)
- **Curation Errors**: Human input validation failures

### Recovery
- **Checkpointing**: Workflow state saved at each stage
- **Resume**: Failed workflows can be resumed from last checkpoint
- **Manual Intervention**: Human operators can fix issues and retry

## 🔄 Temporal Serialization System

### Custom Data Converter
The pipeline uses a custom Temporal data converter to ensure proper serialization/deserialization of complex objects:

#### EntityMapping Serialization
- **Type Preservation**: Domain entities maintain their proper types through Temporal serialization
- **UUID Safety**: Ensures `entity.uuid` is always accessible (no more `'dict' object has no attribute 'uuid'` errors)
- **Existing Infrastructure**: Leverages `ENTITY_TYPE_MAP` and `entity.type` fields for type reconstruction

#### RelationSpanContextMapping Serialization
- **Relation Types**: Properly handles both `Relation` and `ConceptRelation` types
- **Context Preservation**: Maintains `RelationshipContext` objects with proper field validation
- **Span Handling**: Ensures `Span` objects maintain correct `LexicalType` values

#### Key Features
- **Fail-Fast Design**: Raises `RuntimeError` on configuration errors instead of silent failures
- **DateTime Handling**: Custom `DateTimeEncoder` properly serializes datetime objects
- **Type Safety**: Guarantees that all objects maintain their expected types throughout the pipeline

### Serialization Flow
```
EntityMapping/RelationSpanContextMapping
    ↓ (Custom Payload Converter)
JSON with Type Information
    ↓ (Temporal Serialization)
Binary Payload
    ↓ (Temporal Deserialization)
JSON with Type Information
    ↓ (Custom Payload Converter)
Proper Domain Objects
```

## 🔄 Scalability

### Horizontal Scaling
- **Temporal Workers**: Multiple workers can process different journal entries
- **Database Sharding**: Neo4j can be clustered for large datasets
- **LLM Scaling**: Multiple Ollama instances for parallel processing

### Performance Optimization
- **Caching**: LLM responses cached to avoid reprocessing
- **Batch Processing**: Multiple entities processed together
- **Async Operations**: Non-blocking I/O throughout pipeline
- **Connection Pooling**: Database connections reused efficiently
