# Minerva Backend Architecture Overview

## 🏗️ System Architecture

Minerva is a personal knowledge management system that processes journal entries to extract entities and relationships, building a comprehensive knowledge graph.

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Obsidian      │    │   External      │
│   (Vue.js)      │    │   Plugin        │    │   Services      │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Minerva Backend       │
                    │     (FastAPI)             │
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
┌───────▼────────┐    ┌──────────▼──────────┐    ┌─────────▼─────────┐
│  Processing     │    │   Knowledge Graph   │    │   Temporal        │
│  Pipeline       │    │   (Neo4j)           │    │   Workflows       │
│  + Quote/       │    └─────────────────────┘    │   Journal, Quote, │
│  Concept/Inbox   │                               │   Concept, Inbox  │
└─────────────────┘                               └───────────────────┘
```

## 🔄 Data Flow

### 1. Journal Entry Submission
```
Journal Entry → API Validation → Temporal Workflow Queue
```

### 2. Entity Extraction Pipeline
```
Journal Text → LLM Processing → Entity Extraction → Curation Queue
```

### 3. Knowledge Graph Construction
```
Curated Entities → Relationship Extraction → Neo4j Storage
```

## 🧩 Component Details

### API Layer (`api/`)
- **FastAPI** application with dependency injection
- **Routers**: Journal, Pipeline, Curation, Health, Processing
- **Error Handling**: Custom exception hierarchy with structured responses
- **CORS**: Configured for frontend integration

### Processing Layer (`processing/`)
- **Extraction Service**: Orchestrates entity extraction using LLM
- **Temporal Orchestrator**: Manages long-running workflows (journal, quote parsing, concept extraction, inbox classification)
- **Curation Manager**: Handles human-in-the-loop validation (journal entities/relations, quote items, concept items, inbox items, notifications)
- **LLM Service**: Interfaces with Ollama for text processing
- **Quote Parsing Workflow**: Parse quotes from markdown, submit for curation, write to Neo4j
- **Concept Extraction Workflow**: Extract concepts from content quotes, submit for curation, write to Neo4j
- **Inbox Classification Workflow**: Classify inbox notes with LLM, submit for curation, execute moves

### Knowledge Graph (`graph/`)
- **Neo4j Database**: Stores entities and relationships
- **Repository Pattern**: Data access layer for different entity types
- **Services**: Business logic for graph operations
- **Models**: Pydantic models for type safety

### Configuration (`config.py`)
- **Environment-based**: Settings loaded from environment variables
- **Pydantic Settings**: Type validation and defaults
- **Dependency Injection**: Centralized service configuration

## 🔧 Key Technologies

- **FastAPI**: Web framework with automatic API documentation
- **Neo4j**: Graph database for knowledge storage
- **Temporal**: Workflow orchestration for long-running processes
- **Ollama**: Local LLM for entity extraction
- **Pydantic**: Data validation and serialization
- **Dependency Injector**: Inversion of control container

## 📊 Entity Types

The system extracts and manages these entity types:

- **Person**: People mentioned in journal entries
- **Feeling**: Emotional states and experiences
- **Emotion**: Specific emotions with intensity levels
- **Event**: Activities and occurrences
- **Project**: Ongoing initiatives and goals
- **Content**: Books, articles, videos, etc.
- **Consumable**: Resources being consumed
- **Place**: Locations and places
- **Concept**: Abstract ideas and concepts

## 🔄 Processing Workflows

### Journal Processing (8-stage pipeline)
1. **Entity Extraction** — LLM extracts entities; queued for curation
2. **Human Curation** — User reviews entities in Curation UI (Queue)
3. **Relationship Extraction** — LLM extracts relationships; queued for curation
4. **Relationship Curation** — User reviews relationships
5. **Knowledge Graph Update** — Validated data stored in Neo4j

### Quote Parsing (Temporal)
1. Scan markdown file → parse quotes + LLM summary → submit to curation DB
2. User reviews quotes in Curation UI (Quotes) → approve/reject
3. Workflow writes approved quotes to Neo4j (Content, Quote, Person, QUOTED_IN, AUTHORED_BY)
4. Notifications emitted (workflow_started, curation_pending, workflow_completed)

### Concept Extraction (Temporal)
1. Load content and quotes from Neo4j → LLM extracts concepts/relations → submit to curation DB
2. User reviews concepts and relations in Curation UI (Concepts)
3. Workflow writes approved concepts to Neo4j (Concept, SUPPORTS, relations)
4. Notifications emitted at key stages

### Inbox Classification (Temporal)
1. Scan inbox folder → LLM suggests target folder per note → submit to curation DB
2. User reviews classifications in Curation UI (Inbox) → accept/reject
3. Workflow moves files to target folders
4. Notifications emitted at key stages

### Notifications
- Stored in curation SQLite (`notifications` table); workflow_type, notification_type (workflow_started, curation_pending, workflow_completed, workflow_failed)
- API: `GET /api/curation/notifications`, `POST /api/curation/notifications/{id}/read`, `POST /api/curation/notifications/{id}/dismiss`
- Curation UI includes a Notifications panel and unread badge in the header

## 🛡️ Error Handling

- **Custom Exceptions**: Structured error responses
- **Retry Logic**: Built into Temporal workflows
- **Logging**: Comprehensive logging throughout the system
- **Health Checks**: System status monitoring

## 🔒 Security Considerations

- **CORS Configuration**: Restricted to known origins
- **Input Validation**: Pydantic models validate all inputs
- **Error Sanitization**: Sensitive data filtered from error responses
- **Local Processing**: LLM runs locally, no external API calls

## 📈 Scalability

- **Temporal Workflows**: Handle long-running processes asynchronously
- **Repository Pattern**: Easy to swap data storage backends
- **Dependency Injection**: Loose coupling enables testing and modification
- **Modular Design**: Components can be scaled independently
