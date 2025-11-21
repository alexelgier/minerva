"""
Concept Extraction Workflow - LangGraph Implementation

Implements the 3-phase concept extraction workflow:
- Phase 1: LLM Self-Improvement Loop - Autonomous extraction and self-critique
- Phase 2: Human Review Loop (HITL) - Human-guided refinement with feedback
- Phase 3: Commit to Database and Obsidian - Persistence and file generation

The workflow extracts atomic concepts (Zettels) from book quotes, performs
duplicate detection, discovers relations, validates quality, and commits results
to Neo4j and Obsidian.

See Also:
    - [API Reference](../docs/API.md) - Complete API documentation
    - [Workflows Documentation](../docs/WORKFLOWS.md) - Detailed workflow documentation
    - [Architecture Documentation](../docs/ARCHITECTURE.md) - Technical architecture
"""

from __future__ import annotations

import operator
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Set
from typing_extensions import TypedDict, Annotated

from langchain.chat_models import init_chat_model
from langchain_ollama import OllamaEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.types import interrupt
from pydantic import BaseModel, Field

from minerva_models import Content, Concept, Quote

from zettel_agent.db import (
    get_neo4j_connection_manager,
    find_content_by_uuid,
    find_quotes_by_content,
    find_concept_by_uuid,
    vector_search_concepts,
    create_concept,
    create_concept_relation,
    create_supports_relation,
    update_content_processed_date,
    get_unprocessed_quotes_by_supports,
)
from zettel_agent.obsidian_utils import create_zettel_file


# ============================================================================
# State Schema
# ============================================================================

class ConceptExtractionState(TypedDict):
    """State for concept extraction workflow."""
    # Input
    content_uuid: str
    content: Optional[Content]
    quotes: List[Quote]
    user_suggestions: Optional[str]  # Freeform text suggestions for the extraction process
    
    # Processing state
    phase: Literal["extraction", "human_review", "commit", "end"]
    iteration_count: int
    phase_1_iteration: int
    phase_2_iteration: int
    
    # Extraction results (using Annotated with operator.add for accumulation)
    candidate_concepts: Annotated[List[Dict], operator.add]
    duplicate_detections: Annotated[List[Dict], operator.add]
    novel_concepts: Annotated[List[Dict], operator.add]
    existing_concepts_with_quotes: Annotated[List[Dict], operator.add]
    relations: Annotated[List[Dict], operator.add]
    
    # Quality assessment
    quality_assessment: Optional[Dict]
    critique_log: Annotated[List[Dict], operator.add]
    
    # Human review
    human_feedback: Optional[str]
    human_approved: bool
    
    # Errors and warnings
    errors: Annotated[List[str], operator.add]
    warnings: Annotated[List[str], operator.add]


@dataclass
class InputState:
    """Input state for the graph."""
    content_uuid: str
    user_suggestions: Optional[str] = None  # Freeform text suggestions for the extraction process


# ============================================================================
# Pydantic Models for LLM Structured Output
# ============================================================================

class CandidateConcept(BaseModel):
    """A candidate concept extracted from quotes."""
    concept_id: str = Field(..., description="Temporary ID for tracking")
    title: str = Field(..., description="Título del concepto en español")
    concept: str = Field(..., description="Contenido del concepto")
    analysis: str = Field(..., description="Análisis personal")
    source_quote_ids: List[str] = Field(..., description="Quotes that formed this concept")
    rationale: str = Field(..., description="Why this concept was extracted")


class CandidateConceptsResponse(BaseModel):
    """Response from Call 1.1a: Extract candidate concepts."""
    candidate_concepts: List[CandidateConcept] = Field(..., description="List of candidate concepts")
    unattributed_quotes: List[str] = Field(default_factory=list, description="Quotes that don't form any concept")
    extraction_notes: str = Field(default="", description="Observations about the extraction process")


class DuplicateDetection(BaseModel):
    """Result of duplicate detection for a candidate concept."""
    candidate_concept_id: str = Field(..., description="ID of the candidate concept")
    is_duplicate: bool = Field(..., description="Is this a duplicate?")
    existing_concept_uuid: Optional[str] = Field(None, description="UUID of existing concept if duplicate")
    existing_concept_name: Optional[str] = Field(None, description="Name of existing concept if duplicate")
    confidence: float = Field(..., description="Confidence in duplicate detection (0.0-1.0)", ge=0.0, le=1.0)
    reasoning: str = Field(..., description="Explanation of why it's a duplicate or not")
    quote_ids_to_transfer: List[str] = Field(..., description="Quotes to attribute to existing concept")


class RelationQuery(BaseModel):
    """A search query for finding relation candidates."""
    query: str = Field(..., description="Search query text")


class ConceptRelationQueries(BaseModel):
    """Relation search queries for a concept."""
    concept_id: str = Field(..., description="ID of the concept")
    relation_queries: Dict[str, List[str]] = Field(..., description="Dict mapping relation types to query lists")


class RelationQueriesResponse(BaseModel):
    """Response from Call 1.1c: Generate relation search queries."""
    concept_queries: List[ConceptRelationQueries] = Field(..., description="Queries for each concept")


class ConceptRelation(BaseModel):
    """A relation between concepts."""
    target_concept_id: str = Field(..., description="Target concept ID (temp ID or UUID)")
    target_is_novel: bool = Field(..., description="Is target a novel concept?")
    relation_type: str = Field(..., description="Forward relation type")
    explanation: str = Field(..., description="Why this relation exists")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)


class ConceptRelationsResponse(BaseModel):
    """Response from Call 1.1e: Create relations for a concept."""
    target_concept_id: str = Field(..., description="ID of the concept for which relations are determined")
    relations: List[ConceptRelation] = Field(..., description="List of relations")
    relation_notes: str = Field(default="", description="Observations about relation creation")


class QualityIssue(BaseModel):
    """A quality issue identified in critique."""
    concept_id: Optional[str] = Field(None, description="ID of concept with issue (if applicable)")
    quote_id: Optional[str] = Field(None, description="ID of quote with issue (if applicable)")
    issue: str = Field(..., description="Description of the issue")
    severity: Literal["low", "medium", "high"] = Field(..., description="Severity of the issue")


class QualityCriterion(BaseModel):
    """Quality assessment for a single criterion."""
    passes: bool = Field(..., description="Does this criterion pass?")
    issues: List[QualityIssue] = Field(default_factory=list, description="List of issues")


class QualityAssessment(BaseModel):
    """Quality assessment from self-critique."""
    atomicity: QualityCriterion = Field(..., description="Atomicity assessment")
    distinctness: QualityCriterion = Field(..., description="Distinctness assessment")
    quote_coverage: QualityCriterion = Field(..., description="Quote coverage assessment")
    relation_accuracy: QualityCriterion = Field(..., description="Relation accuracy assessment")
    language: QualityCriterion = Field(..., description="Language assessment")
    edge_cases: QualityCriterion = Field(..., description="Edge cases assessment")


class SelfCritiqueResponse(BaseModel):
    """Response from Call 1.2: Self-critique."""
    quality_assessment: QualityAssessment = Field(..., description="Quality assessment")
    overall_passes: bool = Field(..., description="Does overall quality pass?")
    critique_summary: str = Field(..., description="Overall assessment and key issues")
    improvement_suggestions: List[str] = Field(..., description="Actionable improvement suggestions")


class RefinedExtraction(BaseModel):
    """Refined extraction from Call 1.3."""
    novel_concepts: List[Dict] = Field(..., description="Refined novel concepts")
    existing_concepts_with_quotes: List[Dict] = Field(..., description="Refined existing concepts with quotes")
    relations: List[Dict] = Field(..., description="Refined relations")


class RefinementResponse(BaseModel):
    """Response from Call 1.3: Refinement."""
    refined_extraction: RefinedExtraction = Field(..., description="Refined extraction")
    refinement_notes: str = Field(..., description="Summary of refinement process and changes")


class RevisedExtraction(BaseModel):
    """Revised extraction from Call 2.3."""
    novel_concepts: List[Dict] = Field(..., description="Revised novel concepts")
    existing_concepts_with_quotes: List[Dict] = Field(..., description="Revised existing concepts with quotes")
    relations: List[Dict] = Field(..., description="Revised relations")


class FeedbackIncorporationResponse(BaseModel):
    """Response from Call 2.3: Incorporate human feedback."""
    revised_extraction: RevisedExtraction = Field(..., description="Revised extraction")
    feedback_interpretation: str = Field(..., description="How the LLM interpreted the feedback")
    unresolved_feedback: str = Field(default="", description="Any feedback that couldn't be addressed")
    questions_for_human: str = Field(default="", description="Any clarifications needed")


# ============================================================================
# LLM Initialization
# ============================================================================

_llm_pro = None
_llm_flash = None
_embeddings = None


async def _get_llm_pro():
    """Get or initialize the Pro LLM for complicated calls."""
    global _llm_pro
    if _llm_pro is None:
        _llm_pro = init_chat_model(
            model="gemini-2.5-pro",
            model_provider="google-genai",
            temperature=0
        )
    return _llm_pro


async def _get_llm_flash():
    """Get or initialize the Flash LLM for simpler calls."""
    global _llm_flash
    if _llm_flash is None:
        _llm_flash = init_chat_model(
            model="gemini-2.5-flash",
            model_provider="google-genai",
            temperature=0
        )
    return _llm_flash


async def _get_embeddings():
    """Get or initialize embeddings."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
    return _embeddings


# ============================================================================
# Phase 1: LLM Self-Improvement Loop - Node Functions
# ============================================================================

async def check_content_processed(state: ConceptExtractionState) -> Dict[str, Any]:
    """Check if content is already processed and exit early if so."""
    content_uuid = state["content_uuid"]
    connection_manager = get_neo4j_connection_manager()
    
    try:
        async with connection_manager.session() as session:
            content = await find_content_by_uuid(session, content_uuid)
            if not content:
                return {
                    "errors": [f"Content not found: {content_uuid}"],
                    "phase": "end"
                }
            
            # Check if processed_date is set (check for the field in the content object)
            # Also check in the dict representation if it's a dict
            processed_date = None
            if hasattr(content, 'processed_date'):
                processed_date = getattr(content, 'processed_date', None)
            elif isinstance(content, dict):
                processed_date = content.get('processed_date')
            
            if processed_date is not None:
                return {
                    "warnings": [f"Content already processed on {processed_date}"],
                    "phase": "end"
                }
            
            return {"content": content}
    except Exception as e:
        return {
            "errors": [f"Error checking content: {str(e)}"],
            "phase": "end"
        }


async def load_content_quotes(state: ConceptExtractionState) -> Dict[str, Any]:
    """Load quotes for the content."""
    content = state.get("content")
    if not content:
        return {"quotes": [], "errors": ["No content loaded"], "phase": "end"}
    
    try:
        connection_manager = get_neo4j_connection_manager()
        async with connection_manager.session() as session:
            quotes = await find_quotes_by_content(session, content.uuid)
            
            if not quotes:
                return {
                    "quotes": [],
                    "warnings": ["No quotes found for content"],
                    "phase": "end"
                }
            
            return {
                "quotes": quotes,
                "phase": "extraction"
            }
    except Exception as e:
        return {
            "quotes": [],
            "errors": [f"Error loading quotes: {str(e)}"],
            "phase": "end"
        }


async def extract_candidate_concepts(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 1.1a: Extract candidate concepts with source quotes."""
    quotes = state.get("quotes", [])
    content = state.get("content")
    
    if not quotes:
        return {
            "candidate_concepts": [],
            "warnings": ["No quotes to process"]
        }
    
    llm = await _get_llm_pro()  # Complicated: requires understanding and synthesis
    llm_structured = llm.with_structured_output(CandidateConceptsResponse, method="json_schema")
    
    # Format quotes for prompt
    quotes_text = "\n\n".join([
        f"Quote {i+1} (ID: {q.uuid}):\n\"{q.text}\""
        for i, q in enumerate(quotes)
    ])
    
    content_info = f"Title: {content.title if content else 'Unknown'}\n"
    if content and hasattr(content, 'author') and content.author:
        content_info += f"Author: {content.author}\n"
    
    # Get user suggestions if provided
    user_suggestions = state.get("user_suggestions")
    suggestions_text = ""
    if user_suggestions:
        suggestions_text = f"\n\nUser Suggestions for Extraction:\n{user_suggestions}\n\nPlease consider these suggestions when extracting concepts."
    
    system_prompt = """You are a Zettelkasten expert extracting atomic concepts from quotes.

IMPORTANT: All outputs MUST be in Spanish.

An atomic concept (Zettel) should:
- Contain ONE clear, standalone idea
- Be understandable without the original context
- Be reusable and connectable to other ideas
- Include personal analysis and interpretation

Guidelines:
- Title: 3-8 words, captures the essence
- Concept: 2-4 sentences explaining the core idea
- Analysis: Your interpretation, significance, and connections to other ideas
- Each concept should be linked to the quotes that formed it

Extract all meaningful atomic concepts from the quotes provided."""
    
    user_prompt = f"""Content Information:
{content_info}
    
Quotes:
{quotes_text}{suggestions_text}

Extract all meaningful atomic concepts from these quotes. Link each concept to the quote IDs that formed it."""

    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        candidate_concepts_dicts = [c.model_dump() for c in response.candidate_concepts]
        
        return {
            "candidate_concepts": candidate_concepts_dicts,
            "warnings": response.unattributed_quotes if response.unattributed_quotes else []
        }
    except Exception as e:
        return {
            "errors": [f"Failed to extract candidate concepts: {str(e)}"],
            "candidate_concepts": []
        }


async def detect_duplicate_single(
    candidate_concept: Dict[str, Any],
    state: ConceptExtractionState
) -> Dict[str, Any]:
    """Call 1.1b: Detect duplicate for a single candidate concept (for parallel execution)."""
    llm = await _get_llm_pro()  # Complicated: requires semantic understanding
    llm_structured = llm.with_structured_output(DuplicateDetection, method="json_schema")
    embeddings = await _get_embeddings()
    
    # Generate embedding for candidate concept (use title + concept text)
    concept_text = f"{candidate_concept.get('title', '')} {candidate_concept.get('concept', '')}"
    concept_embedding = await embeddings.aembed_query(concept_text)
    
    # Search for similar concepts
    connection_manager = get_neo4j_connection_manager()
    async with connection_manager.session() as session:
        similar_concepts = await vector_search_concepts(
            session, concept_embedding, limit=50, threshold=0.7
        )
    
    if not similar_concepts:
        return {
            "duplicate_detections": [{
                "candidate_concept_id": candidate_concept.get("concept_id"),
                "is_duplicate": False,
                "confidence": 1.0,
                "reasoning": "No similar concepts found",
                "quote_ids_to_transfer": candidate_concept.get("source_quote_ids", [])
            }]
        }
    
    # Format similar concepts for LLM
    similar_concepts_text = "\n\n".join([
        f"Concept {i+1} (UUID: {c.uuid}):\nTitle: {c.title}\nSummary: {c.summary_short}"
        for i, c in enumerate(similar_concepts)
    ])
    
    system_prompt = """You are a Zettelkasten expert determining if a candidate concept is a duplicate of an existing concept.

A concept is a duplicate if it represents the SAME semantic idea as an existing concept, even if expressed differently.
A concept is NOT a duplicate if it represents a distinct idea, even if related.

Consider semantic equivalence, not just textual similarity."""
    
    user_prompt = f"""Candidate Concept:
Title: {candidate_concept.get('title')}
Concept: {candidate_concept.get('concept')}
Analysis: {candidate_concept.get('analysis', '')}

Similar Existing Concepts:
{similar_concepts_text}

Is the candidate concept a duplicate of any existing concept? If yes, which one?"""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        result = response.model_dump()
        result["candidate_concept_id"] = candidate_concept.get("concept_id")
        result["quote_ids_to_transfer"] = candidate_concept.get("source_quote_ids", [])
        
        return {"duplicate_detections": [result]}
    except Exception as e:
        return {
            "errors": [f"Failed to detect duplicate for {candidate_concept.get('concept_id')}: {str(e)}"],
            "duplicate_detections": [{
                "candidate_concept_id": candidate_concept.get("concept_id"),
                "is_duplicate": False,
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}",
                "quote_ids_to_transfer": candidate_concept.get("source_quote_ids", [])
            }]
        }


async def detect_duplicates_all(state: ConceptExtractionState) -> Dict[str, Any]:
    """Detect duplicates for all candidate concepts (sequential for now, can be parallelized)."""
    candidate_concepts = state.get("candidate_concepts", [])
    
    if not candidate_concepts:
        return {
            "novel_concepts": [],
            "existing_concepts_with_quotes": []
        }
    
    # Detect duplicates for each candidate (sequential for now)
    all_detections = []
    for candidate in candidate_concepts:
        result = await detect_duplicate_single(candidate, state)
        detections = result.get("duplicate_detections", [])
        all_detections.extend(detections)
    
    # Separate novel concepts from duplicates
    candidate_map = {c.get("concept_id"): c for c in candidate_concepts}
    novel_concepts = []
    existing_concepts_with_quotes = []
    
    for detection in all_detections:
        candidate_id = detection.get("candidate_concept_id")
        candidate = candidate_map.get(candidate_id)
        
        if not candidate:
            continue
        
        if detection.get("is_duplicate", False):
            # Add to existing concepts with quotes
            existing_concepts_with_quotes.append({
                "concept_uuid": detection.get("existing_concept_uuid"),
                "concept_name": detection.get("existing_concept_name"),
                "quote_ids": detection.get("quote_ids_to_transfer", [])
            })
        else:
            # Add to novel concepts
            novel_concepts.append(candidate)
    
    return {
        "novel_concepts": novel_concepts,
        "existing_concepts_with_quotes": existing_concepts_with_quotes,
        "duplicate_detections": all_detections
    }


async def generate_relation_queries(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 1.1c: Generate relation search queries for novel concepts."""
    novel_concepts = state.get("novel_concepts", [])
    
    if not novel_concepts:
        return {"relation_queries": []}
    
    llm = await _get_llm_flash()  # Simple: just generating search queries
    llm_structured = llm.with_structured_output(RelationQueriesResponse, method="json_schema")
    
    # Format novel concepts
    concepts_text = "\n\n".join([
        f"Concept {i+1} (ID: {c.get('concept_id')}):\nTitle: {c.get('title')}\nConcept: {c.get('concept')}"
        for i, c in enumerate(novel_concepts)
    ])
    
    relation_types_desc = """
- GENERALIZES: General concept that encompasses specific instances
- SPECIFIC_OF: Specific instance of a general concept
- PART_OF: Component that belongs to a larger system
- HAS_PART: System that contains components
- OPPOSES: Concepts in direct opposition
- SIMILAR_TO: Concepts that are related but distinct
- RELATES_TO: General relationship (catchall)
- SUPPORTS: Usually not used for concept-to-concept
- SUPPORTED_BY: Usually not used for concept-to-concept
"""
    
    system_prompt = """You are a Zettelkasten expert generating semantic search queries to find related concepts.

Generate 2 search queries per relation type for each concept. Queries should be in Spanish and designed to find concepts that might have the specified relation type."""
    
    user_prompt = f"""Novel Concepts:
{concepts_text}

Relation Types:
{relation_types_desc}

Generate 2 search queries per relation type for each novel concept. Focus on finding concepts that might relate to each novel concept."""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        return {"relation_queries": [q.model_dump() for q in response.concept_queries]}
    except Exception as e:
        return {
            "errors": [f"Failed to generate relation queries: {str(e)}"],
            "relation_queries": []
        }


async def search_relation_candidates(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 1.1d: Semantic search for relation candidates (vector search, not LLM)."""
    relation_queries = state.get("relation_queries", [])
    
    if not relation_queries:
        return {"relation_candidates": []}
    
    embeddings = await _get_embeddings()
    connection_manager = get_neo4j_connection_manager()
    
    all_candidates = {}  # UUID -> concept dict
    
    async with connection_manager.session() as session:
        for concept_queries in relation_queries:
            relation_queries_dict = concept_queries.get("relation_queries", {})
            for relation_type, queries in relation_queries_dict.items():
                for query_text in queries:
                    # Generate embedding for query
                    query_embedding = await embeddings.aembed_query(query_text)
                    
                    # Search for concepts
                    similar_concepts = await vector_search_concepts(
                        session, query_embedding, limit=10, threshold=0.7
                    )
                    
                    # Add to candidates pool
                    for concept in similar_concepts:
                        if concept.uuid not in all_candidates:
                            all_candidates[concept.uuid] = {
                                "concept_uuid": concept.uuid,
                                "title": concept.title,
                                "summary_short": concept.summary_short
                            }
    
    return {"relation_candidates": list(all_candidates.values())}


async def create_relations_all(state: ConceptExtractionState) -> Dict[str, Any]:
    """Create relations for all novel concepts (sequential for now, can be parallelized)."""
    novel_concepts = state.get("novel_concepts", [])
    relation_candidates = state.get("relation_candidates", [])
    
    if not novel_concepts:
        return {"relations": []}
    
    all_relations = []
    
    for novel_concept in novel_concepts:
        # Get other novel concepts (exclude current)
        other_novels = [c for c in novel_concepts if c.get("concept_id") != novel_concept.get("concept_id")]
        
        # Create relations for this concept
        result = await create_relations_single(
            novel_concept, other_novels, relation_candidates, state
        )
        relations = result.get("relations", [])
        all_relations.extend(relations)
    
    return {"relations": all_relations}


async def create_relations_single(
    novel_concept: Dict[str, Any],
    other_novel_concepts: List[Dict[str, Any]],
    relation_candidates: List[Dict[str, Any]],
    state: ConceptExtractionState
) -> Dict[str, Any]:
    """Call 1.1e: Create relations for a single novel concept (for parallel execution)."""
    llm = await _get_llm_pro()  # Complicated: requires understanding relationships
    llm_structured = llm.with_structured_output(ConceptRelationsResponse, method="json_schema")
    
    # Format other novel concepts
    other_novels_text = "\n\n".join([
        f"Novel Concept {i+1} (ID: {c.get('concept_id')}):\nTitle: {c.get('title')}\nConcept: {c.get('concept')}"
        for i, c in enumerate(other_novel_concepts)
    ]) if other_novel_concepts else "None"
    
    # Format relation candidates
    candidates_text = "\n\n".join([
        f"Candidate {i+1} (UUID: {c.get('concept_uuid')}):\nTitle: {c.get('title')}\nSummary: {c.get('summary_short')}"
        for i, c in enumerate(relation_candidates)
    ]) if relation_candidates else "None"
    
    relation_types_desc = """
- GENERALIZES: General concept that encompasses specific instances
- SPECIFIC_OF: Specific instance of a general concept
- PART_OF: Component that belongs to a larger system
- HAS_PART: System that contains components
- OPPOSES: Concepts in direct opposition
- SIMILAR_TO: Concepts that are related but distinct
- RELATES_TO: General relationship (catchall)
"""
    
    system_prompt = """You are a Zettelkasten expert determining relations between concepts.

Determine which relations should exist for the target concept, considering both other novel concepts and existing concept candidates."""
    
    user_prompt = f"""Target Novel Concept:
ID: {novel_concept.get('concept_id')}
Title: {novel_concept.get('title')}
Concept: {novel_concept.get('concept')}
Analysis: {novel_concept.get('analysis', '')}

Other Novel Concepts:
{other_novels_text}

Existing Concept Candidates:
{candidates_text}

Relation Types:
{relation_types_desc}

Determine which relations should exist for the target concept."""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        result = response.model_dump()
        result["target_concept_id"] = novel_concept.get("concept_id")
        
        return {"relations": [result]}
    except Exception as e:
                return {
            "errors": [f"Failed to create relations for {novel_concept.get('concept_id')}: {str(e)}"],
            "relations": []
        }


async def self_critique(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 1.2: Self-critique against quality checklist."""
    novel_concepts = state.get("novel_concepts", [])
    existing_concepts_with_quotes = state.get("existing_concepts_with_quotes", [])
    relations = state.get("relations", [])
    quotes = state.get("quotes", [])
    phase_1_iteration = state.get("phase_1_iteration", 0)
    
    llm = await _get_llm_pro()  # Complicated: requires deep analysis
    llm_structured = llm.with_structured_output(SelfCritiqueResponse, method="json_schema")
    
    # Format extraction results
    novel_concepts_text = "\n\n".join([
        f"Concept {i+1} (ID: {c.get('concept_id')}):\nTitle: {c.get('title')}\nConcept: {c.get('concept')}\nAnalysis: {c.get('analysis', '')}"
        for i, c in enumerate(novel_concepts)
    ]) if novel_concepts else "None"
    
    # Get user suggestions if provided
    user_suggestions = state.get("user_suggestions")
    suggestions_text = ""
    if user_suggestions:
        suggestions_text = f"\n\nUser Suggestions:\n{user_suggestions}\n\nConsider these suggestions when evaluating the extraction quality."
    
    system_prompt = """You are a Zettelkasten expert critiquing concept extraction quality.

Evaluate the extraction against these criteria:
1. Atomicity: Each concept contains ONE clear, standalone idea
2. Distinctness: New concepts are semantically distinct from existing concepts
3. Quote Coverage: All meaningful quotes are attributed to at least one concept
4. Relation Accuracy: Relations are semantically correct and meaningful
5. Language: All concepts are in Spanish
6. Edge Cases: Unattributed quotes, disconnected concepts are properly noted"""
    
    user_prompt = f"""Novel Concepts:
{novel_concepts_text}

Existing Concepts with Quotes:
{len(existing_concepts_with_quotes)} existing concepts have new quote attributions

Relations:
{len(relations)} relations created

Total Quotes: {len(quotes)}{suggestions_text}

Critique the extraction against the quality checklist."""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        critique_dict = response.model_dump()
        
        return {
            "quality_assessment": critique_dict,
            "critique_log": [critique_dict],
            "phase_1_iteration": phase_1_iteration + 1
        }
    except Exception as e:
        return {
            "errors": [f"Failed to perform self-critique: {str(e)}"],
            "quality_assessment": None,
            "phase_1_iteration": phase_1_iteration + 1
        }


async def refine_extraction(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 1.3: Refine extraction based on self-critique."""
    novel_concepts = state.get("novel_concepts", [])
    existing_concepts_with_quotes = state.get("existing_concepts_with_quotes", [])
    relations = state.get("relations", [])
    quality_assessment = state.get("quality_assessment")
    critique_log = state.get("critique_log", [])
    phase_1_iteration = state.get("phase_1_iteration", 0)
    
    if not quality_assessment:
        return {
            "phase_1_iteration": phase_1_iteration + 1
        }  # No refinement needed if no critique
    
    llm = await _get_llm_pro()  # Complicated: requires synthesis and improvement
    llm_structured = llm.with_structured_output(RefinementResponse, method="json_schema")
    
    # Get user suggestions if provided
    user_suggestions = state.get("user_suggestions")
    suggestions_text = ""
    if user_suggestions:
        suggestions_text = f"\n\nUser Suggestions:\n{user_suggestions}\n\nPlease incorporate these suggestions when refining the extraction."
    
    # Format current extraction
    extraction_text = f"""Current Novel Concepts: {len(novel_concepts)}
Current Relations: {len(relations)}
Current Existing Concepts with Quotes: {len(existing_concepts_with_quotes)}

Quality Assessment:
{quality_assessment.get('critique_summary', '') if isinstance(quality_assessment, dict) else str(quality_assessment)}"""
    
    system_prompt = """You are a Zettelkasten expert refining concept extraction based on critique.

Address all issues from the critique comprehensively. Update concepts, relations, and quote attributions as needed."""
    
    user_prompt = f"""Current Extraction:
{extraction_text}{suggestions_text}

Refine the extraction to address all issues from the critique."""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        refined = response.refined_extraction
        
        return {
            "novel_concepts": refined.novel_concepts,
            "existing_concepts_with_quotes": refined.existing_concepts_with_quotes,
            "relations": refined.relations,
            "phase_1_iteration": phase_1_iteration + 1
        }
    except Exception as e:
        return {
            "errors": [f"Failed to refine extraction: {str(e)}"],
            "phase_1_iteration": phase_1_iteration + 1
        }


# ============================================================================
# Phase 2: Human Review Loop - Node Functions
# ============================================================================

async def present_for_review(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 2.1: Present comprehensive report and interrupt for human review."""
    novel_concepts = state.get("novel_concepts", [])
    existing_concepts_with_quotes = state.get("existing_concepts_with_quotes", [])
    relations = state.get("relations", [])
    critique_log = state.get("critique_log", [])
    
    # Generate comprehensive report
    report = {
        "new_concepts": novel_concepts,
        "relations": relations,
        "existing_concepts_with_quotes": existing_concepts_with_quotes,
        "critique_log": critique_log
    }
    
    # Interrupt for human review
    interrupt({
        "action": "human_review",
        "report": report,
        "extraction_summary": f"{len(novel_concepts)} novel concepts, {len(relations)} relations"
    })
    
    return {}


async def incorporate_feedback(state: ConceptExtractionState) -> Dict[str, Any]:
    """Call 2.3: Incorporate human feedback."""
    human_feedback = state.get("human_feedback")
    novel_concepts = state.get("novel_concepts", [])
    existing_concepts_with_quotes = state.get("existing_concepts_with_quotes", [])
    relations = state.get("relations", [])
    phase_2_iteration = state.get("phase_2_iteration", 0)
    
    if not human_feedback:
        return {
            "phase_2_iteration": phase_2_iteration + 1
        }  # No feedback to incorporate
    
    llm = await _get_llm_pro()  # Complicated: requires understanding and applying feedback
    llm_structured = llm.with_structured_output(FeedbackIncorporationResponse, method="json_schema")
    
    extraction_text = f"""Novel Concepts: {len(novel_concepts)}
Relations: {len(relations)}
Existing Concepts with Quotes: {len(existing_concepts_with_quotes)}"""
    
    system_prompt = """You are a Zettelkasten expert incorporating human feedback into concept extraction.

Update the extraction based on human feedback. Human intent takes precedence over quality checklist."""
    
    user_prompt = f"""Current Extraction:
{extraction_text}

Human Feedback:
{human_feedback}

Incorporate the feedback into the extraction."""
    
    try:
        response = await llm_structured.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        revised = response.revised_extraction
        
        return {
            "novel_concepts": revised.novel_concepts,
            "existing_concepts_with_quotes": revised.existing_concepts_with_quotes,
            "relations": revised.relations,
            "phase_2_iteration": phase_2_iteration + 1
        }
    except Exception as e:
        return {
            "errors": [f"Failed to incorporate feedback: {str(e)}"],
            "phase_2_iteration": phase_2_iteration + 1
        }


# ============================================================================
# Phase 3: Commit to Database - Node Functions
# ============================================================================

async def create_concepts_db(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 3.1: Create Concept nodes in database."""
    novel_concepts = state.get("novel_concepts", [])
    content = state.get("content")
    
    if not novel_concepts:
        return {"created_concept_uuids": []}
    
    connection_manager = get_neo4j_connection_manager()
    created_uuids = []
    
    async with connection_manager.session() as session:
        for concept_dict in novel_concepts:
            # Create Concept object
            from minerva_models import EntityType, PartitionType
            
            concept = Concept(
                partition=PartitionType.DOMAIN,
                name=concept_dict.get("title", ""),
                title=concept_dict.get("title", ""),
                concept=concept_dict.get("concept", ""),
                analysis=concept_dict.get("analysis", ""),
                source=content.title if content else "",
                summary_short=concept_dict.get("title", "")[:100],  # Simplified
                summary=concept_dict.get("concept", "")[:500]  # Simplified
            )
            
            # Create in database
            concept_uuid = await create_concept(session, concept)
            created_uuids.append({
                "temp_id": concept_dict.get("concept_id"),
                "uuid": concept_uuid
            })
    
    return {"created_concept_uuids": created_uuids}


async def create_relations_db(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 3.2: Create bidirectional concept relations."""
    relations = state.get("relations", [])
    created_uuids = state.get("created_concept_uuids", [])
    
    # Create mapping from temp_id to UUID
    temp_to_uuid = {item["temp_id"]: item["uuid"] for item in created_uuids}
    
    connection_manager = get_neo4j_connection_manager()
    
    async with connection_manager.session() as session:
        for relation_dict in relations:
            target_concept_id = relation_dict.get("target_concept_id")
            target_relations = relation_dict.get("relations", [])
            
            # Get source UUID
            source_uuid = temp_to_uuid.get(target_concept_id)
            if not source_uuid:
                continue
            
            for rel in target_relations:
                target_id = rel.get("target_concept_id")
                relation_type = rel.get("relation_type")
                
                # Get target UUID
                if rel.get("target_is_novel", False):
                    target_uuid = temp_to_uuid.get(target_id)
                else:
                    target_uuid = target_id  # Already a UUID
                
                if not target_uuid:
                    continue
                
                # Create bidirectional relation
                try:
                    await create_concept_relation(session, source_uuid, target_uuid, relation_type)
                except Exception as e:
                    # Log error but continue
                    pass
    
    return {}


async def create_supports_relations(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 3.3: Create SUPPORTS relations from quotes to concepts."""
    novel_concepts = state.get("novel_concepts", [])
    existing_concepts_with_quotes = state.get("existing_concepts_with_quotes", [])
    created_uuids = state.get("created_concept_uuids", [])
    
    # Create mapping from temp_id to UUID
    temp_to_uuid = {item["temp_id"]: item["uuid"] for item in created_uuids}
    
    connection_manager = get_neo4j_connection_manager()
    
    async with connection_manager.session() as session:
        # Create SUPPORTS for novel concepts
        for concept_dict in novel_concepts:
            concept_uuid = temp_to_uuid.get(concept_dict.get("concept_id"))
            if not concept_uuid:
                continue
            
            quote_ids = concept_dict.get("source_quote_ids", [])
            for quote_id in quote_ids:
                try:
                    await create_supports_relation(session, quote_id, concept_uuid)
                except Exception as e:
                    pass
        
        # Create SUPPORTS for existing concepts
        for existing_dict in existing_concepts_with_quotes:
            concept_uuid = existing_dict.get("concept_uuid")
            quote_ids = existing_dict.get("quote_ids", [])
            
            for quote_id in quote_ids:
                try:
                    await create_supports_relation(session, quote_id, concept_uuid)
                except Exception as e:
                    pass
    
    return {}


async def create_obsidian_files(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 3.4: Create Obsidian zettel files."""
    novel_concepts = state.get("novel_concepts", [])
    relations = state.get("relations", [])
    created_uuids = state.get("created_concept_uuids", [])
    content = state.get("content")
    
    # Create mapping from temp_id to UUID
    temp_to_uuid = {item["temp_id"]: item["uuid"] for item in created_uuids}
    
    # Build relation map for each concept
    concept_relations_map = {}
    for relation_dict in relations:
        target_concept_id = relation_dict.get("target_concept_id")
        target_relations = relation_dict.get("relations", [])
        
        if target_concept_id not in concept_relations_map:
            concept_relations_map[target_concept_id] = {
                "GENERALIZES": [], "SPECIFIC_OF": [], "PART_OF": [], "HAS_PART": [],
                "SUPPORTS": [], "SUPPORTED_BY": [], "OPPOSES": [], "SIMILAR_TO": [], "RELATES_TO": []
            }
        
        for rel in target_relations:
            relation_type = rel.get("relation_type")
            target_id = rel.get("target_concept_id")
            
            if rel.get("target_is_novel", False):
                target_uuid = temp_to_uuid.get(target_id)
            else:
                target_uuid = target_id
            
            if target_uuid and relation_type in concept_relations_map[target_concept_id]:
                concept_relations_map[target_concept_id][relation_type].append(target_uuid)
    
    created_files = []
    
    for concept_dict in novel_concepts:
        concept_id = concept_dict.get("concept_id")
        concept_uuid = temp_to_uuid.get(concept_id)
        
        if not concept_uuid:
            continue
        
        concept_relations = concept_relations_map.get(concept_id, {
            "GENERALIZES": [], "SPECIFIC_OF": [], "PART_OF": [], "HAS_PART": [],
            "SUPPORTS": [], "SUPPORTED_BY": [], "OPPOSES": [], "SIMILAR_TO": [], "RELATES_TO": []
        })
        
        try:
            file_path = await create_zettel_file(
                concept_uuid=concept_uuid,
                title=concept_dict.get("title", ""),
                concept=concept_dict.get("concept", ""),
                analysis=concept_dict.get("analysis", ""),
                summary_short=concept_dict.get("title", "")[:100],
                summary=concept_dict.get("concept", "")[:500],
                concept_relations=concept_relations,
                source=content.title if content else None
            )
            created_files.append(file_path)
        except Exception as e:
            pass
    
    return {"created_files": created_files}


async def update_processed_date(state: ConceptExtractionState) -> Dict[str, Any]:
    """Step 3.5: Update Content processed_date."""
    content = state.get("content")
    if not content:
        return {}
    
    connection_manager = get_neo4j_connection_manager()
    async with connection_manager.session() as session:
        await update_content_processed_date(session, content.uuid)
    
    return {"phase": "end"}


# ============================================================================
# Conditional Routing Functions
# ============================================================================

def should_continue_phase1(state: ConceptExtractionState) -> Literal["refine", "human_review", "end"]:
    """Decide whether to continue Phase 1 loop or move to Phase 2."""
    phase_1_iteration = state.get("phase_1_iteration", 0)
    quality_assessment = state.get("quality_assessment")
    errors = state.get("errors", [])
    
    # Check for critical errors
    if errors:
        return "end"
    
    # Max 10 iterations
    if phase_1_iteration >= 10:
        return "human_review"
    
    # Check if quality passes
    if quality_assessment and isinstance(quality_assessment, dict):
        overall_passes = quality_assessment.get("overall_passes", False)
        if overall_passes:
            return "human_review"
    
    # Continue refinement
    return "refine"


def should_continue_phase2(state: ConceptExtractionState) -> Literal["incorporate", "commit", "end"]:
    """Decide whether to continue Phase 2 loop or move to Phase 3."""
    human_approved = state.get("human_approved", False)
    phase_2_iteration = state.get("phase_2_iteration", 0)
    errors = state.get("errors", [])
    
    # Check for critical errors
    if errors:
        return "end"
    
    # Max 20 iterations
    if phase_2_iteration >= 20:
        return "end"
    
    # If approved, commit
    if human_approved:
        return "commit"
    
    # Continue incorporating feedback
    return "incorporate"


# ============================================================================
# Graph Assembly
# ============================================================================

# Build graph
# Note: Checkpointer is handled automatically by LangGraph API
# For local development, you can add: checkpointer = MemorySaver()
builder = StateGraph(ConceptExtractionState)

# Phase 1 nodes
builder.add_node("check_content_processed", check_content_processed)
builder.add_node("load_content_quotes", load_content_quotes)
builder.add_node("extract_candidate_concepts", extract_candidate_concepts)
builder.add_node("detect_duplicates_all", detect_duplicates_all)
builder.add_node("generate_relation_queries", generate_relation_queries)
builder.add_node("search_relation_candidates", search_relation_candidates)
builder.add_node("create_relations_all", create_relations_all)
builder.add_node("self_critique", self_critique)
builder.add_node("refine_extraction", refine_extraction)

# Phase 2 nodes
builder.add_node("present_for_review", present_for_review)
builder.add_node("incorporate_feedback", incorporate_feedback)

# Phase 3 nodes
builder.add_node("create_concepts_db", create_concepts_db)
builder.add_node("create_relations_db", create_relations_db)
builder.add_node("create_supports_relations", create_supports_relations)
builder.add_node("create_obsidian_files", create_obsidian_files)
builder.add_node("update_processed_date", update_processed_date)

# Edges
builder.set_entry_point("check_content_processed")
builder.add_edge("check_content_processed", "load_content_quotes")
builder.add_edge("load_content_quotes", "extract_candidate_concepts")

# After extract_candidate_concepts, detect duplicates (sequential for now, can be parallelized)
builder.add_edge("extract_candidate_concepts", "detect_duplicates_all")
builder.add_edge("detect_duplicates_all", "generate_relation_queries")
builder.add_edge("generate_relation_queries", "search_relation_candidates")
# After search_relation_candidates, create relations (sequential for now, can be parallelized)
builder.add_edge("search_relation_candidates", "create_relations_all")
builder.add_edge("create_relations_all", "self_critique")
builder.add_conditional_edges(
    "self_critique",
    should_continue_phase1,
    {
        "refine": "refine_extraction",
        "human_review": "present_for_review",
            "end": "__end__"
        }
    )
builder.add_edge("refine_extraction", "self_critique")  # Loop back

# Phase 2
builder.add_conditional_edges(
    "present_for_review",
    should_continue_phase2,
    {
        "incorporate": "incorporate_feedback",
        "commit": "create_concepts_db",
            "end": "__end__"
        }
    )
builder.add_edge("incorporate_feedback", "present_for_review")  # Loop back

# Phase 3
builder.add_edge("create_concepts_db", "create_relations_db")
builder.add_edge("create_relations_db", "create_supports_relations")
builder.add_edge("create_supports_relations", "create_obsidian_files")
builder.add_edge("create_obsidian_files", "update_processed_date")
builder.add_edge("update_processed_date", "__end__")

# Compile graph
# LangGraph API handles checkpointing automatically, so we don't pass a checkpointer here
graph = builder.compile(name="Concept Extraction")

