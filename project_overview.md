# Project Minerva: AI Assistant Analysis

This document provides a comprehensive analysis of the Minerva project, designed for an AI assistant to understand its architecture, components, and data flow.

## 1. Project Summary

**Purpose**: Minerva is a personal knowledge management system designed to process journal entries. It extracts structured information (entities and relationships) from unstructured text and builds a personal knowledge graph.

**Main Functionality**:
- **Journal Submission**: Users can submit daily journal entries via a REST API.
- **Automated Processing Pipeline**: Each entry undergoes a multi-stage, durable workflow that includes entity extraction, relationship extraction, and integration into a graph database.
- **Human-in-the-Loop Curation**: The pipeline includes mandatory steps for human review and correction of the AI-extracted entities and relationships to ensure high data quality.
- **Knowledge Graph Storage**: All structured data is stored in a Neo4j graph database, allowing for complex queries and analysis of the interconnected information from the journals.

**Target Users**: Individuals who practice journaling and want to gain deeper insights from their entries by structuring the content into a queryable and interconnected knowledge base.

## 2. Technology Stack

- **Backend**:
    - **Language**: Python 3.11+
    - **Framework**: FastAPI
    - **Workflow Engine**: Temporal.io
    - **Database Driver**: `neo4j` (for Neo4j), `aiosqlite` (for curation queue)
    - **Data Modeling**: Pydantic
    - **Web Server**: Uvicorn
- **Frontend**:
    - **Language**: JavaScript
    - **Framework**: Vue.js
    - **Build Tool**: Vite
- **Database**:
    - **Primary**: Neo4j (Graph Database)
    - **Secondary**: SQLite (for managing the curation queue)
- **DevOps**:
    - **Containerization**: Docker, Docker Compose

## 3. File/Folder Structure

