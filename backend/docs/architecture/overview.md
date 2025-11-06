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
└─────────────────┘    └─────────────────────┘    └───────────────────┘
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
- **Temporal Orchestrator**: Manages long-running workflows
- **Curation Manager**: Handles human-in-the-loop validation
- **LLM Service**: Interfaces with Ollama for text processing

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

## 🔄 Processing Workflow

### Stage 1: Entity Extraction
1. Journal entry received via API
2. LLM processes text to extract entities
3. Entities queued for human curation

### Stage 2: Human Curation
1. User reviews and validates extracted entities
2. Entities can be modified, added, or removed
3. Curated entities proceed to relationship extraction

### Stage 3: Relationship Extraction
1. LLM analyzes curated entities for relationships
2. Relationships queued for human validation
3. User reviews and validates relationships

### Stage 4: Knowledge Graph Update
1. Validated entities and relationships stored in Neo4j
2. Graph structure updated with new knowledge
3. Processing complete

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
