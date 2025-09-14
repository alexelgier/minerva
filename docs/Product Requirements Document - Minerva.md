# Product Requirements Document: Minerva

## Local Journaling + Personal Knowledge Management System

### 1. Project Information

**Project Name:** Minerva  
**Language:** Spanish (journal entries, queries) with English UI  
**Programming Languages:** Python, Vue.js, TypeScript, Tailwind CSS  
**Date:** September 2025  
**Version:** 2.0 Enhanced Specification

#### Original Requirements Restatement

Minerva is a privacy-first local journaling and personal knowledge management system that processes daily Spanish journal entries through local LLM inference to extract entities and relationships, stores them in an encrypted knowledge graph, and provides a human-curated workflow for building personal insights over time. The system operates completely offline, integrates seamlessly with Obsidian workflows, and supports iterative enhancement from MVP entity extraction to advanced temporal reasoning and philosophical reflection capabilities.

### 2. Product Definition

#### 2.1 Product Goals

**Privacy-First Knowledge Extraction:** Enable completely local and offline processing of personal journal entries while maintaining absolute data sovereignty through encrypted storage and zero external network dependencies.

**Seamless Daily Workflow Integration:** Create a frictionless evening routine where journal submission automatically transitions into knowledge curation, allowing natural progression from writing to reflection without disrupting established habits.

**Human-Centered Curation Architecture:** Build a priority-based review system that keeps individual curation sessions manageable while ensuring steady progress through multi-day processing pipelines, preventing system overwhelm.

**Modular Intelligence Foundation:** Establish an extensible architecture that evolves from basic Spanish entity extraction using local Qwen3 models to sophisticated temporal reasoning, bilingual querying, and philosophical analysis frameworks.

#### 2.2 User Stories

**Daily Journal Processing Workflow** As a reflective journaler, I want to submit my completed Obsidian daily note with a single command that automatically opens my curation dashboard showing prioritized pending tasks, so that my transition from writing to knowledge building feels natural and manageable.

**Privacy-Conscious Personal Data Management**  
As a privacy-conscious individual, I want all my journal processing, entity extraction, relationship analysis, and knowledge graph storage to happen entirely within my encrypted Cryptomator vault using local computational resources, so that my personal reflections and psychological data never leave my direct control.

**Bilingual Knowledge Interaction** As a Spanish-thinking bilingual person, I want to write journal entries and queries in Spanish while interacting with a clean English interface, so that language barriers don't interfere with either my natural expression or my system interaction efficiency.

**Structured Psychological Data Integration** As a systematic self-tracker, I want my daily PANAS, BPNS, and Flourishing scores along with sleep timestamps to be automatically extracted and stored as temporal metadata in my knowledge graph, so that I can later analyze patterns between psychological well-being and life events without manual data entry.

**Intelligent Task Queue Management** As someone with limited processing resources, I want the system to schedule intensive LLM inference during designated time windows while keeping individual curation sessions short and focused, so that I can maintain progress without system interference during active computer use.

**Entity Evolution and Disambiguation** As a knowledge seeker building understanding over time, I want the system to intelligently merge information about people, concepts, and projects as they appear across multiple journal entries while maintaining aliases and preventing duplicates, so that my knowledge graph accurately reflects my evolving understanding rather than fragmenting information.

### 3. Technical Architecture

#### 3.1 System Overview

Minerva operates as a containerized Docker ecosystem with four primary components communicating through encrypted local channels. The Obsidian Plugin provides the user interface trigger and result integration. The Python Processing Engine handles LLM inference, entity extraction, and relationship analysis using local Ollama models. The Vue.js Curation Dashboard enables human-in-the-loop review and approval workflows. The Neo4j Knowledge Graph provides encrypted storage and temporal querying capabilities for the evolving personal knowledge base.

This architecture ensures complete data locality while supporting asynchronous processing that accommodates both immediate user interaction needs and resource-intensive background inference tasks. All components operate within the encrypted Cryptomator vault, maintaining privacy boundaries through filesystem-level encryption rather than application-level security measures.

#### 3.2 Data Flow Architecture

**Phase 1: Note Submission and Initial Processing** When a user completes their evening journal entry, the Obsidian plugin processes the note structure, separating free-text content from structured psychological assessment data. The free text undergoes preprocessing for Spanish language entity extraction, while structured data including PANAS scores, BPNS measures, Flourishing indices, and sleep timestamps are parsed programmatically and queued for direct knowledge graph integration.

**Phase 2: Entity Extraction and Queueing** The Python processing engine receives the preprocessed Spanish text and invokes the local Qwen3 model for entity extraction based on the defined schema including Person, Emotion, Event, Project, Concept, and Resource entities. Given the 30 second to 4 minute inference times on the target hardware, this process runs asynchronously during designated processing windows, with results queued for human curation along with confidence scores and contextual information.

**Phase 3: Human-in-the-Loop Entity Curation** The Vue.js dashboard presents extracted entities in priority order, with longest-pending items surfacing first to prevent backlog accumulation. Users review individual entity properties, approve accurate extractions, modify incomplete ones, and reject false positives. The interface provides detailed entity views showing all properties while maintaining workflow efficiency through keyboard shortcuts and bulk operations where appropriate.

**Phase 4: Relationship Extraction and Secondary Curation** Once entities are approved for a journal entry, the system performs a second LLM inference pass to identify relationships between approved entities and existing knowledge graph nodes. This relationship extraction considers temporal context and entity aliases to suggest meaningful connections that undergo a second human curation phase before final graph integration.

**Phase 5: Knowledge Graph Integration and Entity Evolution** Approved entities and relationships update the Neo4j knowledge graph through intelligent merging algorithms that handle entity disambiguation, property aggregation, and alias tracking. Person entities accumulate information additively across entries, while temporal entities like Events and Feelings maintain distinct occurrences with appropriate temporal linkages.

#### 3.3 Entity Schema Implementation

The system implements a carefully designed entity hierarchy that balances extraction accuracy with meaningful personal knowledge representation. Each entity type serves specific purposes in building temporal understanding of personal experiences and relationships.

**Person Entities** represent individuals in the user's life with properties including full_name for primary identification, occupation for contextual understanding, and birth_date for temporal reference. Person entities evolve additively across journal entries, accumulating new information while maintaining alias tracking to prevent duplication when individuals are referenced by nicknames, titles, or partial names.

**Feeling Entities** function as reified relationships connecting persons to emotions with specific temporal and intensity properties. These entities capture the user's emotional experiences toward people, events, or concepts with intensity ratings from 1-10, precise timestamps, and optional duration tracking. This approach enables sophisticated emotional pattern analysis while maintaining clear attribution and temporal context.

**Emotion, Event, Project, Concept, and Resource Entities** provide structured vocabulary for classifying and organizing different types of experiences and knowledge encountered in journal entries. Events capture specific occurrences with temporal, location, and duration properties. Projects track ongoing initiatives with status and progress metadata. Concepts represent atomic ideas for zettelkasten-style knowledge building. Resources manage external content consumption with status tracking and quote extraction.

**Daily Psychological Metrics** attach directly to journal entry nodes as properties rather than separate entities, enabling efficient querying of well-being patterns while maintaining clear temporal association with specific reflection periods. This design supports future correlation analysis between psychological measures and extracted entity patterns.

#### 3.4 Privacy and Security Architecture

**Network Isolation and Local Processing** The system operates with strict network isolation protocols, utilizing Docker container configurations that prevent external network access during processing phases. Ollama runs in offline mode with local model storage, eliminating any possibility of data transmission during inference operations. The Vue.js dashboard operates as a local web server without external resource dependencies, ensuring complete offline functionality.

**Filesystem Security and Encryption** All system components, including temporary processing files, logs, configuration data, and the Neo4j database, operate exclusively within the user's Cryptomator-encrypted vault. This approach provides transparent encryption and decryption through filesystem-level operations while maintaining normal application functionality. The system implements secure deletion protocols for temporary files and ensures no processing artifacts remain outside the encrypted boundary.

**Data Flow Security Boundaries** Communication between system components occurs through encrypted local channels with clearly defined data transfer protocols. The Obsidian plugin accesses journal files through standard filesystem operations within the encrypted vault. The Python processing engine receives data through secure local APIs with input validation and sanitization. The curation dashboard operates through localhost connections with session-based authentication to prevent unauthorized access to personal data.

**Audit and Monitoring Capabilities** The system maintains comprehensive audit logs of all processing activities, user interactions, and system state changes without logging sensitive content. These logs enable debugging and system optimization while preserving privacy through content-neutral event tracking. Users can monitor system activity through dashboard indicators showing processing status, queue lengths, and recent activity summaries.

### 4. User Experience Design

#### 4.1 Obsidian Integration Workflow

**Journal Submission Interface** The Obsidian plugin integrates seamlessly into the existing journal workflow through a command palette entry labeled "Minerva: Process Today's Journal" that appears after journal completion. This command analyzes the current daily note structure, validates the presence of both free-text content and completed psychological assessments, and queues the entry for processing while providing immediate user feedback about submission success and estimated processing timeline.

**Processing Status Integration**  
The plugin maintains a sidebar panel showing real-time processing status for submitted entries, pending curation tasks, and recently completed knowledge graph updates. This panel provides quick access to the curation dashboard and displays summary statistics about personal knowledge graph growth, creating visibility into the system's ongoing value generation without overwhelming the writing interface.

**Results Integration and Note Enhancement** Upon completion of the full processing pipeline, the plugin automatically updates the original journal note with YAML frontmatter containing links to extracted entities, relationship summaries, and knowledge graph integration metadata. This enhancement provides immediate value by connecting daily reflections to broader knowledge patterns while maintaining the original journal content integrity.

#### 4.2 Curation Dashboard Experience

**Priority-Based Task Queue Interface** The Vue.js dashboard opens with a comprehensive overview showing all pending curation tasks organized by priority, with longest-pending items prominently featured to prevent backlog accumulation. The interface provides clear visual indicators for different task types including entity review, relationship approval, and integration confirmation, enabling users to understand their curation workload at a glance.

**Individual Entity Review Workflow** During entity curation, the dashboard presents a split-view interface showing the original Spanish journal text context alongside extracted entity details with all properties visible for review. Users can approve accurate extractions with a single click, modify properties through inline editing capabilities, or reject false positives with optional feedback for system improvement. The interface maintains context awareness by highlighting relevant text passages that influenced each entity extraction.

**Relationship Curation and Graph Preview** The relationship review interface displays proposed connections between entities with visual graph previews showing how new relationships integrate into the existing knowledge structure. Users can approve, modify, or reject relationship suggestions while viewing confidence scores and contextual evidence. The interface provides entity search capabilities for manual relationship creation when the automated extraction misses important connections.

**Session Management and Progress Tracking** The dashboard implements intelligent session management that allows users to complete partial curation sessions while maintaining progress state across multiple interactions. Users can approve any number of items per session, with clear indicators showing completion progress for individual journal entries and overall system state. The interface provides session summaries showing accomplishments and remaining tasks to maintain motivation and progress awareness.

#### 4.3 Processing Schedule Management

**Automated Processing Windows** The system implements configurable processing schedules with a default morning window from 6 AM to 12 PM for automated LLM inference tasks. During these windows, the system processes queued journal entries and relationship extraction tasks while monitoring system resource usage to prevent interference with other applications. Users receive notifications when processing completes and curation tasks become available.

**Manual Processing Control** Users can initiate ad-hoc processing sessions through dashboard controls that specify custom time windows such as "process for the next 4 hours" for immediate results when desired. The system provides a global processing toggle to completely disable automated inference during critical work periods or system maintenance activities.

**Resource-Aware Queue Management** The task queue implementation monitors system resource usage and adapts processing intensity based on available computational capacity and user activity patterns. The system pauses intensive operations when user interaction is detected and resumes during idle periods, ensuring responsive system performance while maintaining steady progress through processing pipelines.

### 5. Implementation Specifications

#### 5.1 Technology Stack and Dependencies

**Backend Processing Engine (Python)** The core processing component utilizes Python with Ollama integration for local LLM inference, specifically targeting the Qwen3-4B-Instruct model for Spanish language entity extraction. The engine implements asynchronous processing queues using Celery for task management, SQLite for processing state persistence, and custom natural language processing pipelines optimized for Spanish journal content analysis.

**Frontend Curation Interface (Vue.js)** The dashboard application builds on Vue.js 3 with TypeScript support for type safety and Tailwind CSS for responsive styling. The interface utilizes Pinia for state management, Vue Router for navigation between curation views, and custom components optimized for rapid entity review workflows with keyboard shortcut support for efficient user interaction.

**Knowledge Graph Storage (Neo4j)** The graph database implements custom schemas for the defined entity types with encrypted storage configuration for privacy compliance. The system utilizes Neo4j's temporal data handling capabilities for tracking entity evolution over time and implements custom algorithms for entity disambiguation, relationship scoring, and knowledge graph querying optimized for personal knowledge management use cases.

**Containerization and Deployment (Docker)** The complete system deploys through Docker Compose configurations that manage component communication, resource allocation, and security boundaries while ensuring all data remains within the encrypted vault filesystem. Container configurations implement network isolation, resource limits appropriate for the target hardware, and automated backup procedures for critical data persistence.

#### 5.2 Performance Optimization Strategies

**LLM Inference Optimization** Given the 30 second to 4 minute inference times for entity extraction on the target hardware, the system implements intelligent batching strategies that group similar processing tasks and optimize model loading to minimize overhead between inference operations. The processing engine maintains warm model instances during processing windows while gracefully releasing resources during idle periods.

**Memory Management and Resource Efficiency** The system implements careful memory management for large journal datasets with streaming processing for entity extraction, efficient caching for frequently accessed knowledge graph nodes, and garbage collection optimization to prevent memory leaks during extended processing sessions. Database query optimization ensures responsive dashboard performance even with growing knowledge graphs.

**User Experience Responsiveness** Despite intensive backend processing requirements, the user interface remains highly responsive through asynchronous communication patterns, optimistic updates for user interactions, and intelligent preloading of likely-needed data. The dashboard provides immediate feedback for all user actions while processing operations continue in the background.

#### 5.3 Data Persistence and Backup Strategy

**Encrypted Knowledge Graph Storage** The Neo4j database operates with full encryption at rest using database-level security features combined with filesystem encryption through Cryptomator integration. This dual-layer approach ensures data security while maintaining query performance and backup compatibility.

**Automated Backup and Versioning** The system implements automated daily backups of the complete knowledge graph with versioning capabilities that enable point-in-time recovery and change tracking. Backup files maintain the same encryption standards as the primary database while providing efficient differential backup strategies to minimize storage overhead.

**Processing State Persistence** All processing queues, curation states, and user preferences persist through system restarts with transaction logging that ensures no data loss during processing pipeline interruptions. The system maintains processing audit trails that enable debugging and progress tracking across extended multi-day processing cycles.

### 6. Success Metrics and Validation

#### 6.1 Technical Performance Indicators

**Processing Accuracy and Reliability** The system targets greater than 85% entity extraction accuracy for Spanish journal text with less than 1% failure rate for the complete end-to-end processing workflow. Processing reliability encompasses successful handling of varying journal entry lengths, consistent entity schema compliance, and robust error recovery for processing interruptions.

**System Responsiveness and Resource Efficiency** Individual curation sessions complete in less than 5 minutes on average for typical journal entries, with dashboard response times under 2 seconds for all user interactions. The system maintains efficient resource usage during background processing while ensuring responsive performance during active user sessions.

**Data Integrity and Privacy Compliance** The system achieves 100% local operation with zero external network communication during normal operations, verified through network monitoring and audit logging. All data persistence occurs exclusively within encrypted storage boundaries with comprehensive audit trails for debugging and optimization purposes.

#### 6.2 User Experience Success Measures

**Workflow Integration Effectiveness** Users successfully integrate journal processing into their evening routines with minimal workflow disruption, measured through adoption rates and sustained usage patterns over time. The system maintains user engagement through manageable curation session lengths and clear progress indicators that prevent overwhelming backlog accumulation.

**Knowledge Discovery and Insight Generation** The evolving knowledge graph successfully captures meaningful patterns in personal experiences, relationships, and psychological well-being as evidenced by user-reported insights and system-generated pattern recognition. The temporal tracking capabilities provide valuable perspectives on personal growth and relationship evolution over time.

**System Reliability and User Confidence** Users maintain confidence in the system's privacy protection and data security through transparent operation indicators and successful recovery from any processing errors. The modular architecture supports iterative feature enhancement without disrupting established workflows or requiring significant user relearning.

## 7. Implementation Roadmap

### Phase 1: Core MVP Foundation

**Essential Processing Pipeline** establishes the fundamental workflow from Spanish journal entries to curated knowledge graph through local LLM inference. This phase implements entity extraction using Qwen3 models for all six entity types, human curation interface for entity approval and modification, basic relationship extraction between approved entities, and Neo4j knowledge graph storage with essential entity schemas.

**Minimal User Interface** develops a simple web-based curation dashboard for reviewing extracted entities and relationships, approving or rejecting LLM suggestions, and manual entity creation when needed. The interface prioritizes functionality over aesthetics, focusing on efficient entity review workflows that prevent processing bottlenecks while maintaining data quality through human oversight.

### Phase 2: Data Management and Reliability

**Entity Evolution and Deduplication** implements intelligent entity merging algorithms that handle person aliases across journal entries, additive property updates for evolving entities, and disambiguation workflows for potential duplicates. This phase establishes temporal metadata integration for psychological assessments and develops robust data persistence patterns that support system reliability and recovery.

**Enhanced Relationship Processing** expands relationship extraction capabilities with advanced relationship types, temporal context awareness, and relationship evolution tracking. The processing pipeline gains sophisticated relationship suggestion algorithms that consider historical patterns while maintaining human curation for relationship approval and manual creation of missed connections.

### Phase 3: User Experience and Integration

**Streamlined Workflow Integration** develops the Obsidian plugin for seamless journal submission, automated processing queue management with configurable scheduling, and results integration back into original journal notes. This phase implements Docker containerization for system deployment and establishes encrypted storage protocols within Cryptomator vaults for complete privacy compliance.

**Advanced Curation Interface** replaces basic web interface with Vue.js dashboard featuring keyboard shortcuts, batch operations, session management, and progress tracking. The interface gains search and filtering capabilities, entity relationship visualization, and processing status monitoring that enables efficient management of growing knowledge graphs.

### Phase 4: Intelligence and Analysis

**Pattern Recognition and Insights** implements temporal reasoning capabilities that identify patterns in personal experiences, psychological metric correlations with life events, and automated insight generation based on knowledge graph analysis. This phase develops natural language querying in Spanish for knowledge exploration and establishes foundation algorithms for personal pattern discovery.

**Knowledge Graph Analytics** adds sophisticated querying capabilities including multi-dimensional analysis, entity centrality measures, relationship strength analysis, and temporal pattern visualization. The system gains export capabilities for knowledge graph data and develops automated backup and versioning systems for long-term data preservation.

### Phase 5: Advanced Features and Extensibility

**Psychological and Philosophical Analysis** implements specialized processing modules for existentialist theme identification, meaning-making pattern analysis, and creative writing prompt generation based on personal knowledge patterns. This phase develops advanced temporal reasoning for life narrative construction and establishes frameworks for philosophical reflection support.

**System Maturation and Enhancement** focuses on performance optimization for large knowledge graphs, advanced security features for data protection, API development for future extensibility, and comprehensive documentation for system maintenance. The architecture gains plugin support for custom analysis modules and establishes foundation for community-contributed enhancements.