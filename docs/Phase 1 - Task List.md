## 📋 Epic 1: Database Foundation & CRUD Operations

_Priority: HIGH | Estimated: 1 week_

### Story 1.1: Database Connection & Entity Operations

**Goal**: Implement robust Neo4j connection and basic graph operations using existing Pydantic models

#### Tasks:

- [x] **1.1.1** Enhance `graph/db.py` with connection pooling and health checks
- [ ] **1.1.2** Implement entity CRUD operations for all 8 entity types using existing Pydantic models
- [ ] **1.1.3** Implement basic relationship CRUD operations (individual operations only)
- [ ] **1.1.4** Create Obsidian link resolution utility (check for `[[Link]]` patterns and match to existing entity IDs via frontmatter)

### Story 1.2: Basic Relationship Schema

**Goal**: Establish simple relationship framework for Phase 1

#### Tasks:

- [ ] **1.2.1** Define core specific relationship types (WORKS_ON, PARTICIPATES_IN, FEELS_ABOUT, RELATES_TO)
- [ ] **1.2.2** Implement generic RELATES_TO relationship with properties for relationship_type discovery
- [ ] **1.2.3** Create relationship storage and retrieval functions

---

## 🤖 Epic 2: Multi-Stage LLM Entity Extraction Pipeline

_Priority: HIGH | Estimated: 3-4 weeks_

### Story 2.1: Ollama Integration & Pipeline Foundation

**Goal**: Set up Ollama client and extraction pipeline infrastructure

#### Tasks:

- [ ] **2.1.1** Create Ollama client wrapper with model management, health checks, and error handling
- [ ] **2.1.2** Implement journal preprocessing pipeline (extract psychological data + create entity glossary from [[Links]])
- [ ] **2.1.3** Build extraction pipeline orchestrator with stage management and retry logic
- [ ] **2.1.4** Create pipeline state tracking and error recovery mechanisms

### Story 2.2: Stage 1 - Standalone Entity Identification & Property Hydration

**Goal**: Extract and hydrate standalone entities (Person, Project, Event, Resource)

#### Tasks:

- [ ] **2.2.1** Build Stage 1A: Entity identification prompts for Spanish text (find entities, reference known entities by ID from glossary)
- [ ] **2.2.2** Build Stage 1B: Property hydration prompts for each entity type (extract ALL properties from text for both new and existing entities)
- [ ] **2.2.3** Implement confidence scoring and validation for extracted entities
- [ ] **2.2.4** Add stage-level error handling and retry mechanisms

### Story 2.3: Stage 2 - Relational Entity Extraction (Multiple Passes)

**Goal**: Extract relational entities atomically with their relationships

#### Tasks:

- [ ] **2.3.1** Build Stage 2A: Feeling/Emotion relation extraction (Person/Event → Emotion with intensity, temporal context)
- [ ] **2.3.2** Build Stage 2B: Concept relation extraction (Person/Event → Abstract ideas, learnings, themes)
- [ ] **2.3.3** Implement relational entity validation (ensure target entities exist from Stage 1 + glossary)
- [ ] **2.3.4** Add atomic relationship property extraction (intensity, duration, context within single pass)

### Story 2.4: Stage 3 - Standalone Relationship Extraction

**Goal**: Extract remaining relationships between existing entities

#### Tasks:

- [ ] **2.4.1** Build relationship extraction for Person → Project (WORKS_ON)
- [ ] **2.4.2** Build relationship extraction for Person → Event (PARTICIPATES_IN)
- [ ] **2.4.3** Build generic relationship extraction (RELATES_TO with relationship_type property discovery)
- [ ] **2.4.4** Implement relationship confidence scoring and conflict detection

### Story 2.5: Psychological Data Integration & Pipeline Completion

**Goal**: Integrate structured psychological assessments and finalize processing

#### Tasks:

- [ ] **2.5.1** Attach PANAS, BPNS, Flourishing scores and sleep data as temporal metadata to journal entries
- [ ] **2.5.2** Create extraction result validation and quality checks
- [ ] **2.5.3** Implement pipeline completion notifications and result queuing for curation

---

## 🔄 Epic 3: Processing Queue & Task Management

_Priority: MEDIUM | Estimated: 1-2 weeks_

### Story 3.1: 6-Stage Pipeline Task Queue System

**Goal**: Manage the complete journal processing workflow with proper state tracking

#### Tasks:

- [ ] **3.1.1** Implement FIFO task queue with persistence and crash recovery
- [ ] **3.1.2** Define 6-stage pipeline states (SUBMITTED → ENTITY_PROCESSING → ENTITY_CURATION → RELATION_PROCESSING → RELATION_CURATION → DB_WRITE)
- [ ] **3.1.3** Create stage-level retry mechanisms with fallback to pipeline restart
- [ ] **3.1.4** Implement pipeline state persistence for crash recovery

### Story 3.2: User-Configurable Processing Windows

**Goal**: Allow users to control when intensive processing occurs

#### Tasks:

- [ ] **3.2.1** Create processing window configuration (start time, end time, days of week)
- [ ] **3.2.2** Implement processing scheduler that respects user-defined windows
- [ ] **3.2.3** Add manual processing controls (start/stop, process now, pause for X hours)
- [ ] **3.2.4** Create processing status monitoring and user notifications

### Story 3.3: Single-Threaded LLM Resource Management

**Goal**: Manage single LLM inference capacity with proper queuing

#### Tasks:

- [ ] **3.3.1** Implement single-threaded LLM call management (one inference at a time)
- [ ] **3.3.2** Create LLM task queue with proper serialization of extraction stages
- [ ] **3.3.3** Add system activity detection to pause processing during active user sessions
- [ ] **3.3.4** Implement graceful processing interruption and resumption

### Story 3.4: Processing Metrics and Monitoring

**Goal**: Track processing performance and provide visibility into system activity

#### Tasks:

- [ ] **3.4.1** Create processing metrics (queue lengths, processing times, success/failure rates)
- [ ] **3.4.2** Implement API endpoints for real-time queue status and pipeline progress
- [ ] **3.4.3** Add processing history and audit logging for debugging
- [ ] **3.4.4** Create dashboard indicators for processing activity and system health

---

## 🎨 Epic 4: Basic Curation Web Interface

_Priority: MEDIUM | Estimated: 3-4 weeks_

### Story 4.0: Curation Backend & Queue Management

**Goal**: Create persistent curation state management system using FastAPI + SQLite

#### Tasks:

- [ ]  **4.0.1** Design SQLite schema for curation queue (journal_entries table with JSON columns for entities/relationships)
- [ ]  **4.0.2** Implement curation queue models and database operations (create, read, update status)
- [ ]  **4.0.3** Create FastAPI endpoints for curation operations (get pending items, update status, batch operations)
- [ ]  **4.0.4** Add curation state management (pending → accepted/rejected transitions)
- [ ]  **4.0.5** Implement pipeline integration (trigger next processing stage when journal entry batch fully curated)
- [ ]  **4.0.6** Add curation queue persistence and recovery mechanisms

### Story 4.1: Vue.js Dashboard Foundation & General Queue View

**Goal**: Create dashboard foundation with home/landing General Queue View

#### Tasks:

- [ ]  **4.1.1** Set up Vue 3 + TypeScript + Tailwind project with Pinia state management and Vue Router
- [ ]  **4.1.2** Create responsive dashboard layout with navigation between queue/entity/relation views
- [ ]  **4.1.3** Connect to backend API with HTTP client and reactive data fetching
- [ ]  **4.1.4** Build General Queue View (home/landing) showing all pending curation tasks with FIFO/date sorting
- [ ]  **4.1.5** Implement task grouping by journal entry with progress indicators (X of Y entities completed)

### Story 4.2: Entity Curation Interface (Split View)

**Goal**: Enable users to review and curate extracted entities with journal context

#### Tasks:

- [ ]  **4.2.1** Create entity curation view with left-right split layout (Spanish journal text | Entity details)
- [ ]  **4.2.2** Implement entity property editing with real-time validation and confidence score display
- [ ]  **4.2.3** Add Accept/Reject/Modify actions with immediate persistence to curation backend
- [ ]  **4.2.4** Build navigation between entities within the same journal entry batch

### Story 4.3: Relationship Curation Interface (Split View)

**Goal**: Enable users to review and curate extracted relationships with journal context

#### Tasks:

- [ ]  **4.3.1** Create relationship curation view with left-right split layout (Spanish journal text | Relationship details)
- [ ]  **4.3.2** Display relationship properties, confidence scores, and linked entity information
- [ ]  **4.3.3** Add Accept/Reject/Modify actions for relationships with immediate persistence to curation backend
- [ ]  **4.3.4** Build navigation between relationships within the same journal entry batch

### Story 4.4: Persistent Curation State Management

**Goal**: Maintain curation progress across browser sessions without losing user decisions

#### Tasks:

- [ ]  **4.4.1** Implement immediate persistence of Accept/Reject actions to curation backend
- [ ]  **4.4.2** Create curation state tracking (pending, accepted, rejected)
- [ ]  **4.4.3** Build session recovery that restores exact curation progress on dashboard reload
- [ ]  **4.4.4** Add processing stage blocker logic (next stage waits until ALL entities/relations in batch are accepted/rejected)
- [ ]  **4.4.5** Implement simple discard behavior for unsaved modifications when leaving without accepting

### Story 4.5: Processing Integration & Status Monitoring

**Goal**: Connect curation workflow to processing pipeline and provide system visibility

#### Tasks:

- [ ]  **4.5.1** Create real-time processing status indicators showing current pipeline stages
- [ ]  **4.5.2** Implement automatic queue refresh when new curation tasks become available
- [ ]  **4.5.3** Add completion notifications when journal entry batches are fully curated
- [ ]  **4.5.4** Build processing pipeline integration (trigger next stage when batch curation complete)
- [ ]  **4.5.5** Create error handling and retry mechanisms for failed curation API calls

---

## ✅ Acceptance Criteria for Phase 1 Completion

### Core Functionality

- [ ] System can process Spanish journal entries end-to-end
- [ ] All 6 entity types are accurately extracted with >85% precision
- [ ] Entities are successfully stored in Neo4j with proper schemas
- [ ] Web interface allows complete entity curation workflow
- [ ] Basic relationships are extracted and can be reviewed
- [ ] Processing happens asynchronously without blocking UI

### Technical Requirements

- [ ] All components run locally with no external network calls
- [ ] FastAPI backend is fully functional with comprehensive endpoints
- [ ] Vue.js dashboard provides intuitive curation interface
- [ ] Neo4j database properly stores entities and relationships
- [ ] Processing pipeline handles errors gracefully
- [ ] System maintains audit logs of all operations

### Quality Standards

- [ ] Entity extraction accuracy >85% on test journal entries
- [ ] Dashboard responds <2 seconds for all user interactions
- [ ] Processing completes within expected timeframes (30s-4min per entry)
- [ ] No data loss during processing pipeline
- [ ] Proper error handling and user feedback throughout

---

## 📊 Progress Tracking

**Overall Phase 1 Progress**: 0% (0/6 epics completed)

### Epic Progress:

- **Epic 1**: Database Foundation & CRUD Operations - 0%
- **Epic 2**: LLM Entity Extraction Pipeline - 0%
- **Epic 3**: Processing Queue & Task Management - 0%
- **Epic 4**: Basic Curation Web Interface - 0%
- **Epic 5**: Basic Relationship Extraction - 0%
- **Epic 6**: API Enhancement & Integration - 0%
