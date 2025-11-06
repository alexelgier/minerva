# Database Schema Documentation

## 🗄️ Neo4j Graph Database

Minerva uses Neo4j as its primary database to store entities and relationships in a graph structure.

### Node Types

#### Base Node Properties
All nodes inherit these base properties:
- `uuid`: Unique identifier (string)
- `created_at`: Timestamp of creation (datetime)
- `updated_at`: Timestamp of last update (datetime)
- `partition`: Graph partition type (DOMAIN)
- `embedding`: Vector embedding of summary content (float array)

#### Entity Nodes

##### Person
```cypher
(:Person {
  name: string,
  type: "Person",
  summary_short: string,  // Max 30 words
  summary: string,        // Max 100 words
  name_embedding: [float] // Optional vector embedding
})
```

##### Feeling
```cypher
(:Feeling {
  name: string,
  type: "Feeling", 
  summary_short: string,
  summary: string,
  intensity: float,       // 0.0 to 1.0
  valence: float,         // -1.0 to 1.0
  arousal: float,         // 0.0 to 1.0
  concept_uuid: string,   // UUID of concept (for concept feelings)
  embedding: [float]      // Vector embedding of summary
})
```

##### Emotion
```cypher
(:Emotion {
  name: string,
  type: "Emotion",
  summary_short: string,
  summary: string,
  emotion_type: string,   // From EmotionType enum
  intensity: float,       // 0.0 to 1.0
  name_embedding: [float]
})
```

##### Event
```cypher
(:Event {
  name: string,
  type: "Event",
  summary_short: string,
  summary: string,
  start_date: date,       // Optional
  end_date: date,         // Optional
  duration: duration,     // Optional timedelta
  name_embedding: [float]
})
```

##### Project
```cypher
(:Project {
  name: string,
  type: "Project",
  summary_short: string,
  summary: string,
  status: string,         // From ProjectStatus enum
  start_date: date,       // Optional
  end_date: date,         // Optional
  name_embedding: [float]
})
```

##### Content
```cypher
(:Content {
  name: string,
  type: "Content",
  summary_short: string,
  summary: string,
  resource_type: string,  // From ResourceType enum
  status: string,         // From ResourceStatus enum
  name_embedding: [float]
})
```

##### Consumable
```cypher
(:Consumable {
  name: string,
  type: "Consumable",
  summary_short: string,
  summary: string,
  resource_type: string,  // From ResourceType enum
  status: string,         // From ResourceStatus enum
  name_embedding: [float]
})
```

##### Place
```cypher
(:Place {
  name: string,
  type: "Place",
  summary_short: string,
  summary: string,
  name_embedding: [float]
})
```

##### Concept
```cypher
(:Concept {
  name: string,
  type: "Concept",
  title: string,              // Zettel title
  concept: string,            // Main concept definition/exposition
  analysis: string,           // Zettel analysis content
  source: string,             // Source reference
  summary_short: string,
  summary: string,
  embedding: [float]          // Vector embedding of summary
})
```

#### Document Nodes

##### Journal Entry
```cypher
(:JournalEntry {
  uuid: string,
  type: "JournalEntry",
  entry_text: string,
  entry_date: date,
  created_at: datetime,
  partition: "LEXICAL"
})
```

##### Span
```cypher
(:Span {
  uuid: string,
  type: "Span",
  text: string,
  start_pos: integer,
  end_pos: integer,
  created_at: datetime,
  partition: "LEXICAL"
})
```

### Relationship Types

#### Concept Relations (Typed)
```cypher
(:Concept)-[:GENERALIZES {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:SPECIFIC_OF {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:PART_OF {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:HAS_PART {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:SUPPORTS {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:SUPPORTED_BY {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:OPPOSES {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:SIMILAR_TO {summary: string, summary_short: string}]->(:Concept)
(:Concept)-[:RELATES_TO {summary: string, summary_short: string}]->(:Concept)
```

#### General Entity Relationships
```cypher
(:Entity)-[:RELATED_TO {summary: string}]->(:Entity)
```

#### Entity-Document Relationships
```cypher
(:Entity)-[:MENTIONED_IN]->(:JournalEntry)
(:Entity)-[:EXTRACTED_FROM]->(:Span)
```

#### Span Relationships
```cypher
(:Span)-[:PART_OF]->(:JournalEntry)
```

### Indexes

#### Entity Indexes
```cypher
CREATE INDEX entity_name_index FOR (e:Entity) ON (e.name);
CREATE INDEX entity_type_index FOR (e:Entity) ON (e.type);
CREATE INDEX entity_uuid_index FOR (e:Entity) ON (e.uuid);
```

#### Document Indexes
```cypher
CREATE INDEX journal_date_index FOR (j:JournalEntry) ON (j.entry_date);
CREATE INDEX journal_uuid_index FOR (j:JournalEntry) ON (j.uuid);
```

### Constraints

#### Unique Constraints
```cypher
CREATE CONSTRAINT entity_uuid_unique FOR (e:Entity) REQUIRE e.uuid IS UNIQUE;
CREATE CONSTRAINT journal_uuid_unique FOR (j:JournalEntry) REQUIRE j.uuid IS UNIQUE;
```

## 🗃️ SQLite Curation Database

The system uses SQLite for managing the curation queue and temporary data.

### Tables

#### curation_queue
```sql
CREATE TABLE curation_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id TEXT NOT NULL,
    journal_text TEXT NOT NULL,
    entities_json TEXT NOT NULL,  -- JSON array of entities
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending'  -- pending, in_progress, completed
);
```

#### curation_actions
```sql
CREATE TABLE curation_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journal_id TEXT NOT NULL,
    entity_id TEXT,
    action_type TEXT NOT NULL,  -- add, modify, delete
    entity_data TEXT,           -- JSON of entity data
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🔄 Data Flow

### 1. Entity Creation
1. Journal entry processed by LLM
2. Entities extracted and stored in Neo4j
3. Entity-Document relationships created
4. Spans created for text references

### 2. Relationship Creation
1. Curated entities analyzed for relationships
2. Relationships created between entities
3. Relationship metadata stored

### 3. Curation Process
1. Entities queued in SQLite curation database
2. Human curator reviews and modifies entities
3. Changes tracked in curation_actions table
4. Final entities written to Neo4j

## 🛠️ Database Operations

### Common Queries

#### Find all entities for a journal entry
```cypher
MATCH (j:JournalEntry {uuid: $journal_id})-[:MENTIONED_IN]-(e:Entity)
RETURN e
```

#### Find relationships between entities
```cypher
MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
WHERE e1.uuid = $entity1_id AND e2.uuid = $entity2_id
RETURN r
```

#### Get entity by name
```cypher
MATCH (e:Entity {name: $entity_name})
RETURN e
```

### Performance Considerations

- **Indexes**: Created on frequently queried properties
- **Constraints**: Ensure data integrity
- **Partitioning**: Separate lexical and domain data
- **Embeddings**: Vector similarity search capabilities

### Vector Indexes

Neo4j native vector indexes enable fast similarity search across all entity types:

```cypher
// Vector indexes for all entity types
CREATE VECTOR INDEX person_embeddings_index FOR (n:Person) ON (n.embedding)
CREATE VECTOR INDEX feeling_embeddings_index FOR (n:Feeling) ON (n.embedding)
CREATE VECTOR INDEX concept_embeddings_index FOR (n:Concept) ON (n.embedding)
CREATE VECTOR INDEX emotion_embeddings_index FOR (n:Emotion) ON (n.embedding)
CREATE VECTOR INDEX event_embeddings_index FOR (n:Event) ON (n.embedding)
CREATE VECTOR INDEX project_embeddings_index FOR (n:Project) ON (n.embedding)
CREATE VECTOR INDEX content_embeddings_index FOR (n:Content) ON (n.embedding)
CREATE VECTOR INDEX consumable_embeddings_index FOR (n:Consumable) ON (n.embedding)
CREATE VECTOR INDEX place_embeddings_index FOR (n:Place) ON (n.embedding)
CREATE VECTOR INDEX relation_embeddings_index FOR (n:Relation) ON (n.embedding)
CREATE VECTOR INDEX concept_relation_embeddings_index FOR (n:ConceptRelation) ON (n.embedding)
```

**Index Configuration**:
- **Dimensions**: 1024 (standard embedding size)
- **Similarity Function**: Cosine similarity
- **Auto-created**: During database initialization

**Usage**:
```cypher
// Vector similarity search
CALL db.index.vector.queryNodes('concept_embeddings_index', 5, $query_embedding)
YIELD node, score
WHERE score >= 0.7
RETURN node, score
ORDER BY score DESC
```

## 🔧 Maintenance

### Regular Tasks
- Monitor database size and performance
- Update indexes as query patterns change
- Clean up orphaned nodes and relationships
- Backup both Neo4j and SQLite databases

### Monitoring
- Track query performance
- Monitor memory usage
- Check for constraint violations
- Validate data integrity
