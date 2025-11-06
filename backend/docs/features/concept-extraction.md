# Concept Extraction Feature Documentation

## 🧠 Overview

The Concept Extraction feature implements a Zettelkasten-inspired system for extracting and managing abstract concepts from journal entries. It uses a two-pass approach with Retrieval Augmented Generation (RAG) to provide context-aware concept extraction.

## 🏗️ Architecture

### Two-Pass Extraction Process

#### Pass 1: Concept Mentions
- **Purpose**: Extract concepts mentioned in journal text
- **Processor**: `ConceptProcessor`
- **Prompt**: `ExtractConceptsPrompt`
- **Features**:
  - Identifies existing concepts (with UUIDs) and new concepts
  - Uses enhanced context system with 3 sections: [[Linked]] + RAG + Recent concepts
  - Automatically merges with existing concepts using LLM-based merging
  - Generates embeddings for all concepts
  - Extracts rich concept data: name, title, concept definition, analysis, source

#### Pass 2: Concept Feelings
- **Purpose**: Extract feelings about specific concepts
- **Processor**: `ConceptFeelingProcessor`
- **Prompt**: `ExtractConceptFeelingsPrompt`
- **Features**:
  - Links people to concepts they think/feel about
  - Only extracts when someone has a clear feeling about a concept
  - Creates Feeling entities with `concept_uuid` field

### Enhanced Context System & RAG

#### Three-Section Context System
The enhanced concept extraction uses a sophisticated context system with three distinct sections:

##### 1. [[Linked]] Concepts (Explicitly Mentioned)
- **Source**: Concepts explicitly linked in Obsidian vault
- **Processing**: Extracted from `obsidian_entities` during journal processing
- **Priority**: Highest - these are directly relevant to the current journal entry
- **Format**: `CONCEPTOS EXPLÍCITAMENTE MENCIONADOS:`

##### 2. RAG Concepts (Retrieval Augmented Generation)
- **Source**: Vector similarity search across knowledge base
- **Processing**: Uses Neo4j vector search with cosine similarity
- **Limit**: 10 most relevant concepts
- **Priority**: High - semantically related concepts
- **Format**: `CONCEPTOS RELACIONADOS DE TU BASE DE CONOCIMIENTO:`

##### 3. Recent Concepts (Temporal Relevance)
- **Source**: Concepts with recent mentions (last 30 days)
- **Processing**: Time-based filtering of concept mentions
- **Limit**: 10 most recent concepts
- **Priority**: Medium - contextually relevant recent concepts
- **Format**: Combined with RAG concepts in the same section

#### Concept Merging System
When a concept is identified as existing (has `existing_uuid`), the system automatically merges new information:

##### Merge Process
1. **LLM-Based Merging**: Uses `MergeConceptPrompt` for intelligent field combination
2. **Field Comparison**: Compares all concept fields (title, concept, analysis, source, summaries)
3. **Quality Preservation**: Prioritizes more specific/detailed information over generic content
4. **No Data Loss**: Combines complementary information from both sources
5. **Summary Regeneration**: Always regenerates summaries after merging

##### Merge Rules
- **Recent ≠ Better**: New information isn't automatically preferred
- **Specificity Wins**: More detailed information takes precedence
- **Complementary Addition**: Adds new information without losing existing details
- **Quality Focus**: Maintains high-quality, LLM-generated summaries

#### Neo4j Native Vector Search
- **Embeddings**: Generated from entity summaries (1024 dimensions)
- **Similarity**: Cosine similarity search
- **Indexes**: Auto-created for all entity types
- **Performance**: Fast similarity search across the knowledge base

## 📊 Data Models

### Concept Entity
```python
class Concept(Entity):
    name: str                    # Concept name
    title: str                   # Zettel title (capitalized)
    concept: str                 # Main concept definition/exposition
    analysis: str                # Zettel analysis content
    source: str | None           # Source reference
    summary_short: str           # Max 30 words
    summary: str                 # Max 100 words
    embedding: List[float]       # Vector embedding of summary
```

### Feeling Entity (Extended)
```python
class Feeling(Entity):
    name: str                    # Feeling description
    intensity: float             # 0.0 to 1.0
    duration: timedelta | None   # Feeling duration
    person_uuid: str | None      # Person experiencing feeling
    concept_uuid: str | None     # Concept being felt about
    summary_short: str           # Max 30 words
    summary: str                 # Max 100 words
    embedding: List[float]       # Vector embedding of summary
```

## 🔄 Processing Pipeline

### 1. Journal Entry Processing
```
Journal Entry
     │
     ▼
┌─────────────┐
│ Enhanced    │ ──► [[Linked]] + RAG + Recent concepts
│  Context    │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Pass 1     │ ──► Extract concept mentions + merge existing
│ Concepts    │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Pass 2     │ ──► Extract concept feelings
│ Feelings    │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Pass 3     │ ──► Extract concept relations
│ Relations   │
└─────────────┘
     │
     ▼
┌─────────────┐
│  Storage    │ ──► Save to Neo4j with embeddings
│  & Index    │
└─────────────┘
```

### 2. Processing Order
```python
processing_order = [
    "Person",         # People first (needed for emotions and concept feelings)
    "Concept",        # Concepts (needed for concept feelings and relations)
    "Feeling",        # Emotions (require person context)
    "FeelingConcept", # Concept feelings (require person and concept context)
    "Project",        # Projects
    "Consumable",     # Consumables
    "Content",        # Content
    "Event",          # Events
    "Place",          # Places
]

# Relationship extraction order
relationship_order = [
    "ConceptRelation", # Concept relations (typed relationships between concepts)
    "Relation",        # General entity relationships
]
```

## 🗂️ Zettelkasten Integration

### Obsidian Vault Sync
- **Directory**: `Zettels/` (configurable)
- **Format**: Markdown with frontmatter
- **Template**: Standardized Zettel structure
- **Sync**: Bidirectional between Obsidian and database

### Zettel Template
```markdown
---
entity_id: generated-uuid
entity_type: Concept
short_summary: Brief concept description (LLM-generated)
summary: Detailed concept description (LLM-generated)
aliases: ["Alternative Name 1", "Alternative Name 2"]
concept_relations:
  GENERALIZES: ["uuid1", "uuid2"]
  PART_OF: ["uuid3"]
---

# Concept Title

## Concepto
Brief description of the concept here.

## Análisis
Detailed analysis and personal understanding of the concept.

## Conexiones
- GENERALIZES: [[Specific Concept 1]], [[Specific Concept 2]]
- SPECIFIC_OF: [[General Concept]]
- PART_OF: [[Larger System]]
- HAS_PART: [[Component 1]], [[Component 2]]
- SUPPORTS: [[Supported Concept]]
- SUPPORTED_BY: [[Supporting Concept]]
- OPPOSES: [[Opposing Concept]]
- SIMILAR_TO: [[Similar Concept 1]], [[Similar Concept 2]]
- RELATES_TO: [[Related Concept]]

## Fuente
Source of the concept (book, article, etc.)
```

**Important Notes:**
- `short_summary` and `summary` fields are **always LLM-generated** and never fallback to basic text
- The system **requires** an LLM service to be available for Zettel sync
- If no LLM service is available, the sync will fail with a clear error message
- These fields are automatically updated when concept content changes
- All frontmatter keys use standardized constants (see [Frontmatter Constants](frontmatter-constants.md))

### Connection Syntax
- **Format**: `- RELATION_TYPE: [[Concept Name]]`
- **Processing**: Two-stage parsing (raw extraction → relation parsing)
- **Bidirectional**: Links work in both directions
- **Typed Relations**: 9 different relation types for precise connections

## 🔄 Smart Field Comparison & Updates

### Field Comparison Logic

The system implements intelligent field comparison to optimize sync performance and ensure data consistency:

#### Core Content Fields (Compared)
- `concept` - The main concept content from "Concepto" section
- `analysis` - The analysis content from "Análisis" section  
- `source` - The source information from "Fuente" section
- `title` - The concept title (derived from filename)

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

## 🧪 Testing

### Test Coverage
- **Unit Tests**: 100% coverage for all components (277 tests total)
- **Mocking**: Proper isolation from external dependencies
- **Edge Cases**: Comprehensive error handling tests
- **Zero Warnings**: Clean test suite with no deprecation warnings

### Test Categories
1. **ConceptProcessor Tests**: 6 tests covering extraction logic + enhanced context
2. **ConceptFeelingProcessor Tests**: 7 tests covering feeling extraction
3. **ConceptRelationProcessor Tests**: 9 tests covering concept relation extraction
4. **MergeConceptPrompt Tests**: 8 tests covering concept merging functionality
5. **Enhanced Context Tests**: 9 tests covering three-section context system
6. **ConceptRelation Models Tests**: 13 tests covering ConceptRelationType and ConceptRelation
7. **Vector Search Tests**: 4 tests covering RAG functionality
8. **Integration Tests**: Full pipeline testing

## 🚀 Usage

### Basic Concept Extraction
```python
# Extract concepts from journal entry
concepts = await concept_processor.process(extraction_context)

# Each concept includes:
# - name: "existentialism"
# - title: "Existentialism" 
# - concept: "A philosophical concept that emphasizes individual existence"
# - analysis: "Philosophical concept about existence"
# - source: "Sartre, Being and Nothingness"
# - existing_uuid: "uuid-123" (if concept already exists)
# - embedding: [0.1, 0.2, ...]
```

### Concept Feelings Extraction
```python
# Extract feelings about concepts
feelings = await concept_feeling_processor.process(extraction_context)

# Each feeling includes:
# - person_uuid: "person-123"
# - concept_uuid: "concept-456"
# - intensity: 0.8
# - duration: timedelta(minutes=30)
# - summary: "Feeling inspired by existentialism"
```

### Concept Relation Extraction
```python
# Extract relations between concepts
concept_relations = await concept_relation_processor.process(extraction_context)

# Each relation includes:
# - source_uuid: "concept-123"
# - target_uuid: "concept-456" 
# - type: "GENERALIZES" (from ConceptRelationType enum)
# - summary_short: "Concept relation: GENERALIZES"
# - summary: "Concept relation between concept-123 and concept-456"
```

### Vector Search
```python
# Find similar concepts
similar_concepts = await concept_repository.vector_search(
    query_text="philosophy of existence",
    limit=5,
    threshold=0.7
)
```

## ⚙️ Configuration

### Environment Variables
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Obsidian Configuration
OBSIDIAN_VAULT_PATH=/path/to/vault
ZETTEL_DIRECTORY=Zettels
```

### Vector Search Settings
```python
# Embedding dimensions
EMBEDDING_DIMENSIONS = 1024

# Similarity threshold
DEFAULT_SIMILARITY_THRESHOLD = 0.7

# RAG context limit
DEFAULT_RAG_LIMIT = 5
```

## 🔧 API Endpoints

### Concept Extraction
```http
POST /api/v1/extract/concepts
Content-Type: application/json

{
  "journal_entry": {
    "text": "I was thinking about existentialism today...",
    "date": "2025-09-29"
  }
}
```

### Vector Search
```http
POST /api/v1/concepts/search
Content-Type: application/json

{
  "query": "philosophy of existence",
  "limit": 5,
  "threshold": 0.7
}
```

### Obsidian Sync
```http
POST /api/v1/obsidian/sync-zettels
```

## 📈 Performance

### Metrics
- **Extraction Speed**: ~2-3 seconds per journal entry
- **Vector Search**: <100ms for similarity queries
- **RAG Context**: ~500ms for context retrieval
- **Embedding Generation**: ~1-2 seconds per concept

### Optimization
- **Caching**: LLM responses cached to avoid reprocessing
- **Batch Processing**: Multiple concepts processed together
- **Async Operations**: Non-blocking I/O throughout pipeline
- **Connection Pooling**: Database connections reused efficiently

## 🛠️ Troubleshooting

### Common Issues

#### No Concepts Extracted
- **Check**: Journal text contains abstract concepts
- **Verify**: LLM service is running and accessible
- **Debug**: Check extraction logs for errors

#### Poor RAG Context
- **Check**: Vector indexes are created
- **Verify**: Embeddings are generated correctly
- **Debug**: Check similarity threshold settings

#### Obsidian Sync Issues
- **Check**: Vault path is correct and accessible
- **Verify**: Zettel files follow template format
- **Debug**: Check file permissions and format

### Debug Commands
```python
# Check vector indexes
await neo4j_connection.ensure_vector_indexes()

# Test embedding generation
embedding = await llm_service.generate_embedding("test text")

# Verify concept extraction
concepts = await concept_processor.process(context)
print(f"Extracted {len(concepts)} concepts")
```

## 🔮 Future Enhancements

### Planned Features
1. **Concept Clustering**: Group related concepts automatically
2. **Concept Evolution**: Track how concepts change over time
3. **Concept Networks**: Visualize concept relationships
4. **Advanced RAG**: Multi-modal context retrieval
5. **Concept Templates**: Standardized concept structures

### Integration Opportunities
1. **Knowledge Graphs**: Export to external knowledge bases
2. **AI Assistants**: Use concepts for better AI responses
3. **Research Tools**: Academic concept management
4. **Learning Systems**: Adaptive concept learning

## 📚 References

- [Zettelkasten Method](https://zettelkasten.de/)
- [Neo4j Vector Search](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Retrieval Augmented Generation](https://arxiv.org/abs/2005.11401)
- [Concept Extraction Techniques](https://www.aclweb.org/anthology/2020.acl-main.1/)
