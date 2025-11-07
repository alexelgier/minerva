# Project Minerva: AI-Powered Personal Knowledge Graph

## 1. Project Summary

**Purpose:** Minerva is a personal knowledge management system designed to transform unstructured text, primarily from daily journal entries (from Obsidian), into a structured knowledge graph.

**Problem Solved:** It helps users uncover hidden connections, patterns, and insights within their personal data over time. It automates the tedious process of identifying key entities (people, projects, concepts) and their relationships, creating a queryable and analyzable second brain.

## 2. Key Features / Components

-   **Backend API (`FastAPI`):** A robust REST API for submitting journal entries, managing the processing pipeline, and handling human-in-the-loop curation tasks.
-   **Processing Pipeline (`Temporal.io`):** A durable, multi-stage workflow that orchestrates the entire lifecycle of a journal entry:
    1.  **Entity Extraction:** Uses an LLM to identify key entities.
    2.  **Entity Curation:** Queues extracted entities for optional human review.
    3.  **Relationship Extraction:** Uses an LLM to identify relationships between curated entities.
    4.  **Relationship Curation:** Queues extracted relationships for optional human review.
    5.  **Graph Ingestion:** Persists the final, curated data into the knowledge graph.
-   **Knowledge Graph (`Neo4j`):** The core data store, modeling entities as nodes and relationships as edges. A repository pattern provides structured access to the graph data.
-   **Curation Manager (`SQLite`):** A lightweight system that manages the queue for human-in-the-loop validation of entities and relationships, ensuring data quality.
-   **LLM Service (`Ollama`):** Integrates with local language models via Ollama for all NLP tasks, ensuring privacy and control.
-   **Obsidian Integration:** A service to resolve wiki-links within journal entries, connecting unstructured notes to the structured knowledge graph.
-   **minerva-desktop (`Tauri + Next.js`):** A native desktop application for interacting with LangGraph agents, providing real-time chat, task management, and file operations.
-   **minerva_agent (`LangGraph`):** A deep agent for Obsidian vault assistance, providing file operations, search capabilities, task planning, and subagent delegation.
-   **zettel (`LangGraph`):** An agent system for processing book quotes and extracting atomic concepts (Zettels) using Zettelkasten methodology.

## 3. Architecture / Tech Stack

-   **Backend:** Python 3.12+, FastAPI
-   **Orchestration:** Temporal.io
-   **Databases:**
    -   **Primary:** Neo4j (Graph Database)
    -   **Curation Queue:** SQLite
-   **AI/ML:** 
    -   Ollama for local LLM inference (backend)
    -   Google Gemini for agent reasoning (agents)
-   **Infrastructure:** Docker, Docker Compose
-   **Frontend:** 
    -   Vue.js SPA (legacy, in `frontend/`)
    -   Next.js + Tauri desktop app (`minerva-desktop/`)
-   **Agents:**
    -   LangGraph for agent orchestration
    -   deepagents for agent capabilities
-   **Core Libraries:** Pydantic (data modeling), `dependency-injector` (DI)

## 4. Data Model / Entities

The knowledge graph consists of nodes and edges.

-   **Core Nodes:**
    -   **`JournalEntry`:** Represents a single day's journal text.
    -   **`Entity`:** A generic type for recognized concepts. Sub-types include:
        -   `Person`, `Emotion`, `Feeling`, `Event`, `Project`, `Concept`, `Resource`.
    -   **Time Nodes:** `Year`, `Month`, `Day` nodes create a time tree for chronological navigation.

-   **Core Edges (Relationships):**
    -   **`MENTIONS`:** An `Entity` is mentioned in a `JournalEntry`.
    -   **`RELATED_TO` (generic):** Represents relationships between different entities, extracted by the LLM.

## 5. Current Status

> **🎉 Version 0.2.0 Milestone**: Minerva is now usable for the first time! With minerva-desktop and minerva-agent working together, users can interact with their Obsidian vault through a native desktop application. While functionality is still limited, the core system is functional end-to-end.

-   **Implemented:**
    -   The complete backend API for journal submission and curation.
    -   The full 6-stage Temporal pipeline is functional.
    -   LLM-based extraction for entities and relationships.
    -   Neo4j integration with a repository pattern for all major entity types.
    -   A working curation queue system.
    -   Basic Obsidian link resolution.
    -   **minerva-desktop: Native desktop application for agent interaction (NOW FUNCTIONAL)**.
    -   **minerva_agent: Deep agent for Obsidian vault assistance (NOW FUNCTIONAL)**.
    -   **End-to-end integration: Desktop app can connect to and interact with agents**.
    -   zettel: Quote parsing and concept extraction agents.
-   **In Progress / Planned:**
    -   Enhanced graph visualization in desktop app.
    -   Refinement of LLM prompts for higher accuracy.
    -   Advanced concept linking and relationship discovery.

## 6. Future Plans / Next Steps

-   **Graph Analytics:** Implement graph algorithms (e.g., centrality, community detection) to surface key insights automatically.
-   **Semantic Search:** Add vector embedding capabilities to journal entries and entities for advanced, meaning-based search.
-   **Enhanced Visualization:** Create a rich, interactive frontend to explore the knowledge graph visually.
-   **Broader Data Sources:** Expand beyond journals to ingest data from other sources like books, articles, and notes.
