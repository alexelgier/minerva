# API Endpoints Documentation

## 🌐 Base URL
```
http://localhost:8000
```

## 📋 Authentication
Currently no authentication is required. All endpoints are publicly accessible.

## 🔧 System Reliability
The API uses Temporal workflows with custom serialization to ensure type safety and prevent data corruption during processing. All entity and relationship objects maintain their proper types throughout the pipeline.

## 🔗 Endpoints Overview

### Journal Management
- `POST /api/journal/submit` - Submit journal entry for processing
- `POST /api/journal/validate` - Validate journal entry format

### Pipeline Management
- `GET /api/pipeline/status/{workflow_id}` - Get pipeline status
- `GET /api/pipeline/all-pending` - Get all pending pipelines

### Curation Management
- `GET /api/curation/pending` - Get pending curation items
- `POST /api/curation/complete-entity/{journal_id}` - Complete entity curation
- `POST /api/curation/entity/{journal_id}/{entity_id}` - Handle entity curation action

### Health & Monitoring
- `GET /api/health` - System health check
- `GET /api/health/database` - Database health check

### Processing Control
- `POST /api/processing/control` - Control processing pipeline
- `GET /api/processing/status` - Get processing status

### Obsidian Integration
- `POST /api/obsidian/process-note` - Process Obsidian note
- `POST /api/obsidian/sync-zettels` - Sync Zettel files to database

---

## 📝 Detailed Endpoint Documentation

### Journal Management

#### Submit Journal Entry
```http
POST /api/journal/submit
Content-Type: application/json

{
  "entry_text": "Today I went to the park with John...",
  "entry_date": "2024-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Journal entry submitted successfully",
  "workflow_id": "workflow-uuid-123",
  "data": {
    "journal_id": "journal-uuid-456",
    "estimated_completion": "2024-01-15T18:00:00Z"
  }
}
```

**Error Responses:**
- `400` - Validation error (invalid date format, empty text)
- `422` - Processing error (LLM unavailable, database error)
- `500` - Internal server error

#### Validate Journal Format
```http
POST /api/journal/validate
Content-Type: application/json

{
  "text": "Journal entry text...",
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Journal entry format is valid"
}
```

### Pipeline Management

#### Get Pipeline Status
```http
GET /api/pipeline/status/{workflow_id}
```

**Response:**
```json
{
  "success": true,
  "workflow_id": "workflow-uuid-123",
  "status": {
    "stage": "ENTITY_PROCESSING",
    "created_at": "2024-01-15T10:00:00Z",
    "entities_extracted": 5,
    "relationships_extracted": 3,
    "error_count": 0
  }
}
```

**Pipeline Stages:**
- `SUBMITTED` - Journal entry received
- `ENTITY_PROCESSING` - Extracting entities
- `SUBMIT_ENTITY_CURATION` - Queuing entities for curation
- `WAIT_ENTITY_CURATION` - Waiting for human curation
- `RELATION_PROCESSING` - Extracting relationships
- `SUBMIT_RELATION_CURATION` - Queuing relationships for curation
- `WAIT_RELATION_CURATION` - Waiting for relationship curation
- `DB_WRITE` - Writing to knowledge graph
- `COMPLETED` - Processing complete
- `FAILED` - Processing failed

#### Get All Pending Pipelines
```http
GET /api/pipeline/all-pending
```

**Response:**
```json
{
  "success": true,
  "pending_pipelines": [
    {
      "workflow_id": "workflow-uuid-123",
      "journal_id": "journal-uuid-456",
      "stage": "WAIT_ENTITY_CURATION",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

### Curation Management

#### Get Pending Curation
```http
GET /api/curation/pending
```

**Response:**
```json
{
  "success": true,
  "pending_items": [
    {
      "journal_id": "journal-uuid-456",
      "journal_text": "Today I went to the park...",
      "entities": [
        {
          "id": "entity-uuid-789",
          "name": "John",
          "type": "Person",
          "summary": "A friend mentioned in the journal",
          "confidence": 0.95,
          "spans": [
            {
              "text": "John",
              "start_pos": 25,
              "end_pos": 29
            }
          ]
        }
      ]
    }
  ]
}
```

#### Complete Entity Curation
```http
POST /api/curation/complete-entity/{journal_id}
```

**Response:**
```json
{
  "success": true,
  "message": "Entity curation completed successfully"
}
```

#### Handle Entity Curation Action
```http
POST /api/curation/entity/{journal_id}/{entity_id}
Content-Type: application/json

{
  "action": "modify",
  "entity_data": {
    "name": "John Smith",
    "summary": "Updated summary"
  }
}
```

**Actions:**
- `accept` - Accept entity as-is
- `modify` - Modify entity properties
- `delete` - Remove entity
- `add` - Add new entity

### Health & Monitoring

#### System Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": "2024-01-15T10:00:00Z",
  "services": {
    "database": "healthy",
    "temporal": "healthy",
    "llm": "healthy"
  }
}
```

#### Database Health Check
```http
GET /api/health/database
```

**Response:**
```json
{
  "success": true,
  "database_status": "healthy",
  "neo4j_connected": true,
  "curation_db_connected": true
}
```

### Processing Control

#### Control Processing Pipeline
```http
POST /api/processing/control
Content-Type: application/json

{
  "action": "start",
  "schedule_time": "2024-01-15T06:00:00Z"
}
```

**Actions:**
- `start` - Start processing pipeline
- `stop` - Stop processing pipeline
- `pause` - Pause processing pipeline
- `resume` - Resume processing pipeline

#### Get Processing Status
```http
GET /api/processing/status
```

**Response:**
```json
{
  "success": true,
  "status": "running",
  "next_processing_time": "2024-01-16T06:00:00Z",
  "active_workflows": 3
}
```

### Obsidian Integration

#### Process Obsidian Note
```http
POST /api/obsidian/process-note
Content-Type: application/json

{
  "note_path": "/path/to/note.md"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Note /path/to/note.md queued for processing",
  "workflow_id": "placeholder"
}
```

#### Sync Zettel Files
```http
POST /api/obsidian/sync-zettels
Content-Type: application/json
```

**Response:**
```json
{
  "success": true,
  "message": "Zettel sync completed successfully",
  "result": {
    "total_files": 25,
    "parsed": 24,
    "created": 5,
    "updated": 8,
    "unchanged": 11,
    "errors": 1,
    "errors_list": ["Error processing file.md: LLM service unavailable"],
    "missing_concepts": ["Concept A", "Concept B"],
    "broken_notes": ["corrupted.md"],
    "relations_created": 15,
    "relations_updated": 3,
    "relations_deleted": 2,
    "self_connections_removed": 2,
    "inconsistent_relations": ["Concept C: Self-connection found"]
  }
}
```

**Features:**
- **Smart Field Comparison**: Only updates concepts when core content changes
- **LLM-Only Summaries**: All summaries are LLM-generated, no fallbacks
- **Performance Optimized**: Skips unchanged concepts to save resources
- **Relation Cleanup**: Automatically removes orphaned relations from database
- **Comprehensive Tracking**: Detailed statistics for all operations

---

## 🚨 Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "context": {
      "field": "additional context"
    }
  }
}
```

### Error Codes

- `VALIDATION_ERROR` - Request validation failed
- `RESOURCE_NOT_FOUND` - Requested resource not found
- `SERVICE_UNAVAILABLE` - External service unavailable
- `PROCESSING_ERROR` - Processing operation failed
- `INTERNAL_ERROR` - Unexpected internal error

---

## 📊 Rate Limiting

Currently no rate limiting is implemented. Consider implementing rate limiting for production use.

## 🔒 CORS

CORS is configured to allow requests from:
- `http://localhost:3000` (Development frontend)
- `http://localhost:5173` (Vite development server)

## 📈 Performance

- **Response Time**: Most endpoints respond within 100ms
- **Processing Time**: Journal processing takes 2-10 minutes depending on content
- **Concurrent Requests**: System can handle multiple concurrent journal submissions
- **Database**: Neo4j optimized for graph operations

## 🧪 Testing

Use the provided test data and examples to test the API:

```bash
# Test journal submission
curl -X POST http://localhost:8000/api/journal/submit \
  -H "Content-Type: application/json" \
  -d '{"entry_text": "Test journal entry", "entry_date": "2024-01-15"}'

# Test health check
curl http://localhost:8000/api/health
```
