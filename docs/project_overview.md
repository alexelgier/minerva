# Project Minerva: AI Assistant Analysis

This document provides a comprehensive analysis of the Minerva project, designed for an AI assistant to understand its architecture, components, and data flow.

## 1. Project Summary

**Purpose**: Minerva is a personal knowledge management system designed to process journal entries, manage Obsidian vaults, and extract concepts from books. It extracts structured information (entities and relationships) from unstructured text and builds a personal knowledge graph.

**Main Functionality**:
- **Journal Submission**: Users can submit daily journal entries via a REST API.
- **Automated Processing Pipeline**: Each entry undergoes a multi-stage, durable workflow that includes entity extraction, relationship extraction, and integration into a graph database.
- **Human-in-the-Loop Curation**: The pipeline includes mandatory steps for human review and correction of the AI-extracted entities and relationships to ensure high data quality.
- **Knowledge Graph Storage**: All structured data is stored in a Neo4j graph database, allowing for complex queries and analysis of the interconnected information from the journals.
- **Agent Assistance**: LangGraph-based agents provide intelligent assistance for Obsidian vault management, file operations, and concept extraction.
- **Desktop Application**: Native desktop app for interacting with agents, managing tasks, and viewing files.

**Target Users**: Individuals who practice journaling, use Obsidian for note-taking, read books, and want to gain deeper insights by structuring content into a queryable and interconnected knowledge base.

## 2. Technology Stack

- **Backend**:
    - **Language**: Python 3.12+
    - **Framework**: FastAPI
    - **Workflow Engine**: Temporal.io
    - **Database Driver**: `neo4j` (for Neo4j), `aiosqlite` (for curation queue)
    - **Data Modeling**: Pydantic
    - **Web Server**: Uvicorn
- **Frontend**:
    - **Legacy**: Vue.js SPA (in `frontend/`)
    - **Desktop**: Next.js 15 + Tauri 2 (in `minerva-desktop/`)
- **Agents**:
    - **Framework**: LangGraph
    - **Agent Library**: deepagents
    - **LLM**: Google Gemini 2.5 Pro/Flash
    - **Embeddings**: Ollama (mxbai-embed-large)
- **Database**:
    - **Primary**: Neo4j (Graph Database)
    - **Secondary**: SQLite (for managing the curation queue)
- **DevOps**:
    - **Containerization**: Docker, Docker Compose

## 3. File/Folder Structure

The backend source code is organized as follows:

```
backend/src/minerva_backend/
├── api/
│   └── main.py       # Defines the FastAPI application, all REST API endpoints, and application lifespan events.
├── graph/
│   ├── db.py           # Manages the connection pool and sessions for the Neo4j database.
│   ├── models/
│   │   ├── base.py       # Contains Pydantic base classes for graph Nodes and Edges.
│   │   ├── documents.py  # Defines document models like `JournalEntry`.
│   │   ├── entities.py   # Defines entity models like `Person`, `Emotion`, etc.
│   │   └── relations.py  # Defines relationship (edge) models like `MENTIONS`.
│   ├── repositories/
│   │   ├── base.py       # An abstract base class for repositories, defining common CRUD operations.
│   │   └── *.py          # Concrete repository implementations for each entity and document type (e.g., `PersonRepository`).
│   └── services/
│       └── knowledge_graph_service.py # Service layer for complex graph operations that may involve multiple repositories.
└── processing/
    ├── curation_manager.py # Manages the human-in-the-loop curation queue using an SQLite database.
    └── temporal_orchestrator.py # Defines the Temporal workflow, activities, and the main orchestrator class.
```

## 4. Key Components

- **FastAPI Application (`api/main.py`)**: This is the main web service component. It exposes all REST endpoints for interacting with the system, including submitting journals, checking pipeline status, and handling curation tasks. It integrates the `PipelineOrchestrator` and `CurationManager`.

- **PipelineOrchestrator (`processing/temporal_orchestrator.py`)**: The entry point for the data processing pipeline. Its primary role is to initiate the `JournalProcessingWorkflow` in Temporal when a new journal is submitted.

- **JournalProcessingWorkflow (`processing/temporal_orchestrator.py`)**: The core of the system's business logic. It's a Temporal workflow that defines the multi-stage process for handling a journal entry: entity extraction, entity curation, relationship extraction, relationship curation, and finally writing to the knowledge graph. Its stateful and durable nature is critical for handling the long-running waits for human curation.

- **CurationManager (`processing/curation_manager.py`)**: Manages the human-in-the-loop workflow steps. It uses a separate SQLite database to store curation tasks. When the AI extracts entities or relationships, the workflow submits them here and then pauses. The `CurationManager` provides methods for the API to retrieve these tasks for a human reviewer and to receive the corrected data.

- **Neo4jConnection (`graph/db.py`)**: A singleton class that manages the connection to the Neo4j database, providing sessions to the repositories for executing queries.

- **Repositories (`graph/repositories/`)**: A collection of classes implementing the Repository design pattern. Each class (e.g., `PersonRepository`, `JournalEntryRepository`) is responsible for all database operations (CRUD, specialized queries) for a specific type of node or document in the Neo4j graph. This abstracts the data access logic from the rest of the application.

- **Pydantic Models (`graph/models/`)**: These classes define the strict schema for all data structures (nodes, edges) used in the application. They are used for data validation in the API, in the database layer, and throughout the processing pipeline.

## 5. Data Flow

The data processing follows a well-defined, sequential pipeline orchestrated by Temporal:

1.  **Submission**: A user sends a `POST` request with journal text to the `/api/journal/submit` endpoint.
2.  **Workflow Initiation**: The FastAPI application receives the request, creates a `JournalEntry` object, and calls `orchestrator.submit_journal()`. This starts a new `JournalProcessingWorkflow` instance in Temporal, passing the journal entry as input. The workflow's unique ID is returned to the user.
3.  **Stage 1: Entity Extraction**: The workflow executes the `extract_entities` activity. An AI model (logic not shown, but implied) processes the text and returns a list of potential entities (e.g., `Person`, `Emotion`).
4.  **Stage 2: Entity Curation**:
    - The workflow calls the `submit_entity_curation` activity, which passes the extracted entities to the `CurationManager`. The manager saves them to the SQLite queue as a pending task.
    - The workflow then enters a waiting state by calling `wait_for_entity_curation`. It will remain paused until it receives a signal that curation is complete.
5.  **Human Intervention**: A human reviewer fetches the pending task via the `/api/curation/entities/{journal_id}` endpoint, reviews the entities, and submits the corrected version through `POST /api/curation/entities/{journal_id}/complete`.
6.  **Workflow Resumption**: The completion endpoint calls `curation_manager.complete_entity_curation`, which updates the task in SQLite and signals the waiting Temporal workflow, passing back the curated entities.
7.  **Stage 3 & 4: Relationship Extraction & Curation**: The workflow, now active again, proceeds to the `extract_relationships` activity, using the curated entities as context. This is followed by another `submit/wait` cycle for relationship curation, identical to the entity curation loop.
8.  **Stage 5: Graph Integration**: Once relationship curation is complete, the workflow calls the `write_to_knowledge_graph` activity. This activity uses the `KnowledgeGraphService` and various repositories (`JournalEntryRepository`, `PersonRepository`, etc.) to save the journal entry and all its curated entities and relationships as nodes and edges in the Neo4j database.
9.  **Completion**: The workflow finishes. The entire process is durable and can be monitored at any time using the `/api/pipeline/status/{workflow_id}` endpoint.

## 6. Configuration

While explicit configuration files are not provided, the setup can be inferred from the code:

- **Neo4j Connection**: `graph/db.py` contains default connection parameters (`uri`, `user`, `password`). In a production environment, these would likely be supplied via environment variables.
- **Temporal Connection**: `processing/temporal_orchestrator.py` connects to `localhost:7233`. This would be configured via environment variables in production.
- **Curation Database**: The path to the SQLite database (`curation.db`) used by `CurationManager` is hardcoded but would ideally be a configurable setting.
- **Web Server**: The FastAPI application is run by an ASGI server like Uvicorn, which is configured via command-line arguments for host, port, etc.

## 7. Dependencies

- **`fastapi`**: The core web framework for building the REST API.
- **`uvicorn`**: The ASGI server used to run the FastAPI application.
- **`temporalio`**: The client library for interacting with a Temporal service, used to define and execute workflows and activities.
- **`neo4j`**: The official Python driver for connecting to and querying the Neo4j graph database.
- **`aiosqlite`**: An asynchronous library for interacting with the SQLite database used by the `CurationManager`.
- **`pydantic`**: Used extensively for data modeling, validation, and serialization/deserialization of API requests/responses and database models.

## 8. Entry Points

There are two main processes that need to be run for the application to be fully functional:

1.  **API Server**: The FastAPI application is the main entry point for user interaction. It is started from `api/main.py`.
    ```bash
    uvicorn minerva_backend.api.main:backend_app --host 0.0.0.0 --port 8000
    ```
2.  **Temporal Worker**: A separate process that hosts the workflow and activity implementations. This worker connects to the Temporal server, polls for tasks, and executes the processing logic. It is started by running the `processing/temporal_orchestrator.py` script.
    ```bash
    python -m minerva_backend.processing.temporal_orchestrator
    ```

## 9. API/Interfaces

The core REST API endpoints are defined in `backend/src/minerva_backend/api/main.py`:

- **Journal Processing**:
    - `POST /api/journal/submit`: Submits a new journal entry to start the processing pipeline.
    - `GET /api/pipeline/status/{workflow_id}`: Retrieves the current stage and status of a specific workflow.
    - `GET /api/pipeline/all-pending`: Gets a list of all pipelines that are currently pending action.

- **Curation**:
    - `GET /api/curation/pending`: Gets a list of all journal entries awaiting either entity or relationship curation.
    - `GET /api/curation/entities/{journal_id}`: Fetches a specific entity curation task.
    - `POST /api/curation/entities/{journal_id}/complete`: Submits results for an entity curation task.
    - `GET /api/curation/relationships/{journal_id}`: Fetches a specific relationship curation task.
    - `POST /api/curation/relationships/{journal_id}/complete`: Submits results for a relationship curation task.

- **System**:
    - `GET /api/health`: A simple health check endpoint.

## 10. Notable Patterns

- **Repository Pattern**: The application cleanly separates data access logic from business logic by using repositories for all interactions with the Neo4j database. This makes the code more modular, testable, and easier to maintain.

- **Durable Workflows (Temporal)**: The choice of Temporal.io is a key architectural decision. It allows the complex, multi-day process (waiting for human input) to be modeled as a single, cohesive workflow. Temporal handles the state persistence, retries, and timeouts, which would be very complex to manage manually.

- **Human-in-the-Loop**: The design explicitly incorporates mandatory human review steps into the automated pipeline. This is a pragmatic approach to building a high-quality knowledge graph, acknowledging the current limitations of AI in understanding nuanced, personal text.

- **Separation of Concerns**: The project is well-structured. The `api` module handles web concerns, `processing` handles business logic and orchestration, and `graph` handles data persistence. This makes the system easier to understand and evolve.

- **Async Everywhere**: The use of `async` and `await` in both the FastAPI endpoints and the Temporal activities ensures that the application is non-blocking and can handle I/O-bound operations (like database calls and API requests) efficiently.
