# Project Minerva: AI Assistant Analysis

This document provides a comprehensive analysis of the Minerva project, designed for an AI assistant to understand its architecture, components, and data flow.

## 1. Project Summary

**Purpose**: Minerva is a personal knowledge management system designed to process journal entries. It extracts structured information (entities and relationships) from unstructured text and builds a knowledge graph.

**Main Functionality**:
- **Journal Submission**: Users can submit daily journal entries via an API.
- **Automated Processing Pipeline**: Each entry undergoes a multi-stage pipeline that includes entity extraction, relationship extraction, and integration into a graph database.
- **Human-in-the-Loop Curation**: The pipeline includes steps for human review and correction of the extracted entities and relationships to ensure data quality.
- **Knowledge Graph Storage**: All data is stored in a Neo4j graph database, allowing for complex queries and analysis of the interconnected information from the journals.

**Target Users**: Individuals who practice journaling and want to gain deeper insights from their entries by structuring the content into a queryable knowledge base.

## 2. Technology Stack

- **Backend**:
    - **Language**: Python
    - **Framework**: FastAPI
    - **Workflow Engine**: Temporal.io
    - **Database Driver**: `neo4j` (for Neo4j)
    - **ORM/Data Modeling**: Pydantic (inferred from FastAPI usage)
- **Frontend**:
    - **Language**: JavaScript
    - **Framework**: Vue.js
    - **Build Tool**: Vite
- **Database**:
    - **Primary**: Neo4j (Graph Database)
    - **Secondary**: SQLite (for managing the curation queue)
- **DevOps**:
    - **Containerization**: Docker (`docker-compose.yml`)

## 3. File/Folder Structure

