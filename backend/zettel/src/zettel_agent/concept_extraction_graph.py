"""
Concept Analysis Graph - Extracts atomic Concepts (Zettels) from quotes.

This module implements a concept analysis system that:
1. Loads existing Concepts from Neo4j
2. Analyzes each quote to see if it fits existing Concepts
3. Clusters unattributed quotes
4. Proposes new atomic Concepts

Follows LangGraph 1.0 patterns for state management and node functions.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import math
import os
from typing import List, Dict, Optional, Any, Literal, Set
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings
from langchain_neo4j import Neo4jVector
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from minerva_models import Quote, Content

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict

from zettel_agent.db import (
    get_neo4j_connection_manager,
    find_content_by_uuid,
    find_concept_by_uuid,
    find_quote_by_uuid,
    get_unprocessed_quotes,
    vector_search_concepts,
)


# ============================================================================
# Constants
# ============================================================================

SIMILARITY_THRESHOLD = 0.7
MAX_QUOTE_GROUP_SIZE = 10
BATCH_SIZE = 50  # Process quotes in batches

# ============================================================================
# Data Models
# ============================================================================

class QuoteAttribution(BaseModel):
    """A quote attributed to an existing Concept."""
    quote_uuid: str = Field(description="UUID of the quote")
    concept_uuid: str = Field(description="UUID of the target Concept")
    reasoning: str = Field(description="Why this quote supports this Concept")
    confidence: float = Field(
        description="Confidence score 0.0-1.0",
        ge=0.0,
        le=1.0
    )


class ConceptProposal(BaseModel):
    """A proposed new Concept to be created."""
    # Align with existing Concept model fields
    name: str = Field(description="Concept name")
    title: str = Field(description="Concise title for the atomic concept")
    concept: str = Field(description="The atomic idea itself")
    analysis: str = Field(description="Personal analysis and interpretation")
    source: str = Field(description="Book title being processed")
    summary_short: str = Field(description="Summary of the concept, max 30 words")
    summary: str = Field(description="Detailed summary of the concept, max 100 words")
    source_quote_uuids: List[str] = Field(description="UUIDs of supporting quotes")
    reasoning: str = Field(description="Why these quotes form a coherent concept")


class QuoteAnalysisResult(BaseModel):
    """Result of analyzing a quote against existing Concepts."""
    should_attribute: bool = Field(description="Should quote be attributed to existing Concept?")
    concept_uuid: Optional[str] = Field(default=None, description="Target Concept UUID if attributing")
    reasoning: str = Field(description="Reasoning for the decision")
    confidence: float = Field(description="Confidence in decision", ge=0.0, le=1.0)


# ============================================================================
# LangGraph State Definition
# ============================================================================

@dataclass
class InputState:
    content_uuid: str

class Context(TypedDict):
    pass

class State(TypedDict):
    content_uuid: str
    content: Content | None
    processed_quote_uuids: Set[str]  # Track processed quotes by UUID
    quote_attributions: List[QuoteAttribution]
    concept_proposals: List[ConceptProposal]
    analysis_complete: bool
    iteration_count: int  # Add counter to prevent infinite loops


# ============================================================================
# Utility Functions
# ============================================================================

# Lazy initialization for vector stores
_quote_vector = None
_concept_vector = None


async def _get_quote_vector():
    """Get or initialize Neo4jVector for Quote search."""
    global _quote_vector
    print(f"[GET_QUOTE_VECTOR] Entry - _quote_vector is None: {_quote_vector is None}")
    if _quote_vector is None:
        print(f"[GET_QUOTE_VECTOR] Initializing quote vector store...")
        connection_manager = get_neo4j_connection_manager()
        print(f"[GET_QUOTE_VECTOR] Creating Neo4jVector for Quote with index: quote_embeddings_index")
        _quote_vector = Neo4jVector.from_existing_index(
            embedding=OllamaEmbeddings(model="mxbai-embed-large:latest"),
            node_label="Quote",
            index_name="quote_embeddings_index",
            url=connection_manager.uri,
            username=connection_manager.auth[0],
            password=connection_manager.auth[1],
            database="neo4j",
        )
        print(f"[GET_QUOTE_VECTOR] Quote vector store initialized successfully")
    else:
        print(f"[GET_QUOTE_VECTOR] Using existing quote vector store")
    print(f"[GET_QUOTE_VECTOR] Exit - returning quote vector")
    return _quote_vector


async def _get_concept_vector():
    """Get or initialize Neo4jVector for Concept search."""
    global _concept_vector
    print(f"[GET_CONCEPT_VECTOR] Entry - _concept_vector is None: {_concept_vector is None}")
    if _concept_vector is None:
        print(f"[GET_CONCEPT_VECTOR] Initializing concept vector store...")
        connection_manager = get_neo4j_connection_manager()
        print(f"[GET_CONCEPT_VECTOR] Creating Neo4jVector for Concept with index: concept_embeddings_index")
        _concept_vector = Neo4jVector.from_existing_index(
            embedding=OllamaEmbeddings(model="mxbai-embed-large:latest"),
            node_label="Concept",
            index_name="concept_embeddings_index",
            url=connection_manager.uri,
            username=connection_manager.auth[0],
            password=connection_manager.auth[1],
            database="neo4j",
        )
        print(f"[GET_CONCEPT_VECTOR] Concept vector store initialized successfully")
    else:
        print(f"[GET_CONCEPT_VECTOR] Using existing concept vector store")
    print(f"[GET_CONCEPT_VECTOR] Exit - returning concept vector")
    return _concept_vector


async def get_quote_embedding(quote_uuid: str) -> List[float] | None:
    """Get the embedding for a quote from Neo4j by UUID."""
    print(f"[GET_QUOTE_EMBEDDING] Entry - quote_uuid: {quote_uuid}")
    connection_manager = get_neo4j_connection_manager()
    async with connection_manager.session() as session:
        query = "MATCH (q:Quote {uuid: $uuid}) RETURN q.embedding as embedding"
        print(f"[GET_QUOTE_EMBEDDING] Executing query for quote: {quote_uuid}")
        result = await session.run(query, uuid=quote_uuid)
        record = await result.single()
        if record:
            embedding = record.get("embedding")
            embedding_len = len(embedding) if embedding else 0
            print(f"[GET_QUOTE_EMBEDDING] Found embedding with {embedding_len} dimensions")
            return embedding
        else:
            print(f"[GET_QUOTE_EMBEDDING] No embedding found for quote: {quote_uuid}")
    print(f"[GET_QUOTE_EMBEDDING] Exit - returning None")
    return None


async def get_similar_quotes_for_seed(
    seed_text: str,
    content_uuid: str,
    processed_uuids: Set[str],
    limit: int = MAX_QUOTE_GROUP_SIZE,
    threshold: float = SIMILARITY_THRESHOLD
) -> List[Quote]:
    """Get quotes similar to seed text using vector search, excluding processed ones."""
    print(f"[GET_SIMILAR_QUOTES] Entry - seed_text preview: {seed_text[:50]}..., content_uuid: {content_uuid}, processed_count: {len(processed_uuids)}, limit: {limit}, threshold: {threshold}")
    quote_vector = await _get_quote_vector()
    connection_manager = get_neo4j_connection_manager()
    
    # Use similarity search - get more results than needed for filtering
    print(f"[GET_SIMILAR_QUOTES] Performing vector similarity search with k={limit * 3}")
    results = await quote_vector.asimilarity_search_with_relevance_scores(
        seed_text,
        k=limit * 3  # Get more, then filter
    )
    print(f"[GET_SIMILAR_QUOTES] Vector search returned {len(results)} results")
    
    # Filter by content_uuid, exclude processed, and apply threshold
    similar_quotes = []
    filtered_out_by_score = 0
    filtered_out_by_processed = 0
    filtered_out_by_content = 0
    async with connection_manager.session() as session:
        for idx, (doc, score) in enumerate(results):
            print(f"[GET_SIMILAR_QUOTES] Processing result {idx+1}/{len(results)} - score: {score:.4f}")
            
            if score < threshold:
                filtered_out_by_score += 1
                print(f"[GET_SIMILAR_QUOTES]  -> Filtered out: score {score:.4f} < threshold {threshold}")
                continue
            
            quote_uuid = doc.metadata.get('uuid')
            if not quote_uuid or quote_uuid in processed_uuids:
                filtered_out_by_processed += 1
                print(f"[GET_SIMILAR_QUOTES]  -> Filtered out: already processed or no UUID (uuid: {quote_uuid})")
                continue
            
            # Verify it's for this content
            doc_content_uuid = doc.metadata.get('content_uuid')
            if doc_content_uuid != content_uuid:
                filtered_out_by_content += 1
                print(f"[GET_SIMILAR_QUOTES]  -> Filtered out: content mismatch (doc: {doc_content_uuid} != expected: {content_uuid})")
                continue
            
            # Get full quote object
            print(f"[GET_SIMILAR_QUOTES]  -> Fetching quote object for UUID: {quote_uuid}")
            quote = await find_quote_by_uuid(session, quote_uuid)
            if quote:
                similar_quotes.append(quote)
                print(f"[GET_SIMILAR_QUOTES]  -> Added quote: {quote.text[:50]}... (similarity: {score:.4f})")
            else:
                print(f"[GET_SIMILAR_QUOTES]  -> Warning: Quote not found in DB for UUID: {quote_uuid}")
            
            if len(similar_quotes) >= limit:
                print(f"[GET_SIMILAR_QUOTES] Reached limit of {limit} quotes, stopping")
                break
    
    print(f"[GET_SIMILAR_QUOTES] Exit - Found {len(similar_quotes)} similar quotes (filtered: {filtered_out_by_score} by score, {filtered_out_by_processed} by processed, {filtered_out_by_content} by content)")
    return similar_quotes


# ============================================================================
# LLM and Analysis Functions
# ============================================================================

# Lazy initialization for LLM
_llm = None

async def _get_llm():
    """Get or initialize LLM for concept analysis."""
    global _llm
    print(f"[GET_LLM] Entry - _llm is None: {_llm is None}")
    if _llm is None:
        print(f"[GET_LLM] Initializing LLM with model: gemini-2.5-flash-lite, temperature: 0.3")
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0.3  # Some creativity for analysis
        )
        print(f"[GET_LLM] LLM initialized successfully")
    else:
        print(f"[GET_LLM] Using existing LLM instance")
    print(f"[GET_LLM] Exit - returning LLM")
    return _llm


def _format_concepts_for_prompt(concepts: List) -> str:
    """Format Concepts for LLM prompt."""
    lines = []
    for i, concept in enumerate(concepts, 1):
        lines.append(f"{i}. UUID: {concept.uuid}")
        lines.append(f"   Title: {concept.title}")
        lines.append(f"   Concept: {concept.concept}")
        lines.append("")
    return "\n".join(lines)


async def analyze_quote_against_concepts(
    quote: Quote,
    threshold: float = 0.7
) -> Optional[QuoteAnalysisResult]:
    """
    Analyze if a quote fits any existing Concept using vector search.
    
    Uses Neo4jVector to search for similar Concepts using the quote's existing
    embedding from Neo4j, avoiding wasteful re-embedding.
    """
    print(f"[ANALYZE_QUOTE] Entry - quote_uuid: {quote.uuid}, quote preview: {quote.text[:50]}..., threshold: {threshold}")
    
    # Get quote embedding from Neo4j (already stored, don't regenerate)
    print(f"[ANALYZE_QUOTE] Fetching quote embedding from Neo4j...")
    quote_embedding = await get_quote_embedding(quote.uuid)
    
    # Use direct Cypher vector search for Concepts (most efficient)
    # This leverages existing embeddings without re-embedding
    connection_manager = get_neo4j_connection_manager()
    
    if not quote_embedding:
        # Edge case: no embedding found, fall back to text-based search
        print(f"[ANALYZE_QUOTE] Warning: No embedding found for quote {quote.uuid}, falling back to text search")
        concept_vector = await _get_concept_vector()
        print(f"[ANALYZE_QUOTE] Performing text-based similarity search for concepts...")
        concept_docs = await concept_vector.asimilarity_search_with_relevance_scores(
            quote.text,
            k=5
        )
        print(f"[ANALYZE_QUOTE] Text search returned {len(concept_docs)} concept candidates")
        # Convert to Concept objects
        similar_concepts = []
        async with connection_manager.session() as session:
            for doc_idx, (doc, score) in enumerate(concept_docs):
                print(f"[ANALYZE_QUOTE] Processing concept doc {doc_idx+1} - score: {score:.4f}")
                if score < threshold:
                    print(f"[ANALYZE_QUOTE]  -> Filtered out: score {score:.4f} < threshold {threshold}")
                    continue
                concept_uuid = doc.metadata.get('uuid')
                print(f"[ANALYZE_QUOTE]  -> Fetching concept with UUID: {concept_uuid}")
                if concept_uuid:
                    concept = await find_concept_by_uuid(session, concept_uuid)
                    if concept:
                        similar_concepts.append(concept)
                        print(f"[ANALYZE_QUOTE]  -> Added concept: {concept.title} (similarity: {score:.4f})")
                    else:
                        print(f"[ANALYZE_QUOTE]  -> Warning: Concept not found for UUID: {concept_uuid}")
    else:
        # Use existing embedding with direct Cypher query (most efficient)
        print(f"[ANALYZE_QUOTE] Using existing embedding for vector search (embedding dim: {len(quote_embedding)})")
        async with connection_manager.session() as session:
            similar_concepts = await vector_search_concepts(
                session=session,
                query_embedding=quote_embedding,
                limit=5,
                threshold=threshold
            )
            print(f"[ANALYZE_QUOTE] Vector search returned {len(similar_concepts)} concepts above threshold")
    
    if not similar_concepts:
        print(f"[ANALYZE_QUOTE] No similar concepts found - returning should_attribute=False")
        return QuoteAnalysisResult(
            should_attribute=False,
            reasoning="No existing Concepts found",
            confidence=1.0
        )
    
    # Ask LLM if quote fits any of these Concepts using structured output
    print(f"[ANALYZE_QUOTE] Found {len(similar_concepts)} similar concepts, invoking LLM...")
    print(f"[ANALYZE_QUOTE] Similar concepts: {[c.title for c in similar_concepts]}")
    llm = await _get_llm()
    llm_with_output = llm.with_structured_output(QuoteAnalysisResult, method="json_schema")
    
    system_prompt = """You are a Zettelkasten expert analyzing whether a quote supports an existing atomic concept.

An atomic concept (Zettel) should contain ONE clear idea. A quote supports a concept if it:
- Provides evidence for the concept
- Clarifies or elaborates the concept
- Offers a complementary perspective
- Contains an example of the concept

A quote does NOT support a concept if it:
- Introduces a completely different idea
- Contradicts the concept
- Is only tangentially related"""

    user_prompt = f"""Quote to analyze:
"{quote.text}"
Section: {quote.section or 'N/A'}

Existing Concepts (sorted by similarity):
{_format_concepts_for_prompt(similar_concepts)}

Does this quote support any of these existing Concepts?"""

    try:
        print(f"[ANALYZE_QUOTE] Invoking LLM with structured output...")
        print(f"[ANALYZE_QUOTE] Quote text length: {len(quote.text)} chars, concepts count: {len(similar_concepts)}")
        result = await llm_with_output.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        print(f"[ANALYZE_QUOTE] LLM returned - should_attribute: {result.should_attribute}, confidence: {result.confidence:.4f}")
        if result.should_attribute:
            print(f"[ANALYZE_QUOTE]  -> Concept UUID: {result.concept_uuid}")
            print(f"[ANALYZE_QUOTE]  -> Reasoning: {result.reasoning[:100]}...")
        print(f"[ANALYZE_QUOTE] Exit - returning result")
        return result
    except Exception as e:
        print(f"[ANALYZE_QUOTE] [ERROR] Failed to get structured output: {e}")
        print(f"[ANALYZE_QUOTE] [ERROR] Exception type: {type(e).__name__}")
        import traceback
        print(f"[ANALYZE_QUOTE] [ERROR] Traceback: {traceback.format_exc()}")
        return QuoteAnalysisResult(
            should_attribute=False,
            reasoning=f"LLM error: {e}",
            confidence=0.0
        )


async def propose_concept_from_quotes(
    quotes: List[Quote],
    book_title: str
) -> Optional[ConceptProposal]:
    """Generate a Concept proposal from a cluster of quotes."""
    print(f"[PROPOSAL] Entry - quotes count: {len(quotes)}, book_title: {book_title}")
    print(f"[PROPOSAL] Quote UUIDs: {[q.uuid for q in quotes]}")
    
    # Use structured output for better reliability
    llm = await _get_llm()
    llm_with_output = llm.with_structured_output(ConceptProposal, method="json_schema")
    
    system_prompt = """You are a Zettelkasten expert extracting atomic concepts from quotes.

IMPORTANT: All outputs MUST be in Spanish.

An atomic concept (Zettel) should:
- Contain ONE clear, standalone idea
- Be understandable without the original context
- Be reusable and connectable to other ideas
- Include personal analysis and interpretation

Guidelines:
- Name: 3-8 words, captures the essence
- Title: 3-8 words, captures the essence
- Concept: 2-4 sentences explaining the core idea
- Analysis: Your interpretation, significance, and connections to other ideas
- Summary: Generated from concept + quotes context
- Summary_short: Generated from concept + quotes context"""

    quotes_text = "\n\n".join([
        f"Quote {i+1} (uuid: {q.uuid}) (from {q.section or 'unknown section'}):\n\"{q.text}\""
        for i, q in enumerate(quotes)
    ])
    
    total_text_length = sum(len(q.text) for q in quotes)
    print(f"[PROPOSAL] Total quotes text length: {total_text_length} chars")
    
    user_prompt = f"""Extract an atomic concept from these related quotes:

{quotes_text}

Create a Concept that synthesizes the core idea across these quotes.
Source should be: {book_title}"""

    try:
        print(f"[PROPOSAL] Invoking LLM with structured output...")
        print(f"[PROPOSAL] User prompt length: {len(user_prompt)} chars")
        proposal = await llm_with_output.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        print(f"[PROPOSAL] LLM returned proposal successfully")
        print(f"[PROPOSAL] Proposal name: {proposal.name}")
        print(f"[PROPOSAL] Proposal title: {proposal.title}")
        print(f"[PROPOSAL] Concept length: {len(proposal.concept)} chars")
        print(f"[PROPOSAL] Analysis length: {len(proposal.analysis)} chars")
        
        # Add source UUIDs
        proposal.source_quote_uuids = [q.uuid for q in quotes]
        print(f"[PROPOSAL] Added {len(proposal.source_quote_uuids)} source quote UUIDs")
        print(f"[PROPOSAL] Exit - returning proposal")
        return proposal
    except Exception as e:
        print(f"[PROPOSAL] [ERROR] Failed to create proposal: {e}")
        print(f"[PROPOSAL] [ERROR] Exception type: {type(e).__name__}")
        import traceback
        print(f"[PROPOSAL] [ERROR] Traceback: {traceback.format_exc()}")
        return None


async def find_best_proposal_match(
    quote: Quote, 
    concept_proposals: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Find the best matching concept proposal for a quote using vector search first."""
    print(f"[PROPOSAL_MATCH] Entry - quote_uuid: {quote.uuid}, proposals count: {len(concept_proposals)}")
    
    if not concept_proposals:
        print(f"[PROPOSAL_MATCH] No proposals provided - returning None")
        return None
    
    # Convert dict proposals to ConceptProposal objects for easier handling
    proposal_objects = []
    print(f"[PROPOSAL_MATCH] Converting {len(concept_proposals)} proposal dicts to objects...")
    for prop_idx, prop_dict in enumerate(concept_proposals):
        try:
            proposal_objects.append(ConceptProposal(**prop_dict))
            print(f"[PROPOSAL_MATCH]  -> Converted proposal {prop_idx+1}: {prop_dict.get('name', 'unknown')}")
        except Exception as e:
            print(f"[PROPOSAL_MATCH] Error converting proposal dict {prop_idx} to object: {e}")
            continue
    
    if not proposal_objects:
        print(f"[PROPOSAL_MATCH] No valid proposal objects after conversion - returning None")
        return None
    
    print(f"[PROPOSAL_MATCH] Successfully converted {len(proposal_objects)} proposals")
    
    # Use vector similarity to find similar proposals first
    # Get quote embedding from Neo4j (don't regenerate)
    print(f"[PROPOSAL_MATCH] Fetching quote embedding...")
    quote_embedding = await get_quote_embedding(quote.uuid)
    if quote_embedding is None:
        # Fallback: generate embedding if not found (edge case)
        print(f"[PROPOSAL_MATCH] No quote embedding found, generating new embedding...")
        embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
        quote_embedding = await embeddings.aembed_query(quote.text)
        print(f"[PROPOSAL_MATCH] Generated embedding with {len(quote_embedding)} dimensions")
    else:
        print(f"[PROPOSAL_MATCH] Using existing embedding with {len(quote_embedding)} dimensions")
        
    similar_proposals = []
    embeddings = OllamaEmbeddings(model="mxbai-embed-large:latest")
    print(f"[PROPOSAL_MATCH] Computing similarity between quote and {len(proposal_objects)} proposals...")
    for i, proposal in enumerate(proposal_objects):
        print(f"[PROPOSAL_MATCH] Processing proposal {i+1}/{len(proposal_objects)}: {proposal.name}")
        # Create embedding for proposal concept text
        print(f"[PROPOSAL_MATCH]  -> Generating embedding for proposal concept (length: {len(proposal.concept)} chars)")
        proposal_embedding = await embeddings.aembed_query(proposal.concept)
            
        # Calculate cosine similarity (pure Python)
        dot_product = sum(x * y for x, y in zip(quote_embedding, proposal_embedding))
        norm_quote = math.sqrt(sum(x * x for x in quote_embedding))
        norm_proposal = math.sqrt(sum(x * x for x in proposal_embedding))
        similarity = dot_product / (norm_quote * norm_proposal) if (norm_quote * norm_proposal) > 0 else 0.0
        
        print(f"[PROPOSAL_MATCH]  -> Similarity: {similarity:.4f} (threshold: 0.7)")
        if similarity >= 0.7:  # Same threshold as existing concepts
            similar_proposals.append((proposal, similarity, i))
            print(f"[PROPOSAL_MATCH]  -> Added to similar proposals list")
        else:
            print(f"[PROPOSAL_MATCH]  -> Below threshold, skipping")
    
    # Sort by similarity
    similar_proposals.sort(key=lambda x: x[1], reverse=True)
    print(f"[PROPOSAL_MATCH] Found {len(similar_proposals)} proposals above similarity threshold")
    
    if not similar_proposals:
        print(f"[PROPOSAL_MATCH] No similar proposals found - returning None")
        return None
    
    # Only call LLM if we found similar proposals above threshold
    print(f"[PROPOSAL_MATCH] Invoking LLM to validate best match...")
    llm = await _get_llm()
    llm_with_output = llm.with_structured_output(QuoteAnalysisResult, method="json_schema")
    
    system_prompt = """You are a Zettelkasten expert analyzing whether a quote supports a proposed atomic concept.

A quote supports a proposed concept if it:
- Provides evidence for the concept
- Clarifies or elaborates the concept  
- Offers a complementary perspective
- Contains an example of the concept

A quote does NOT support a proposed concept if it:
- Introduces a completely different idea
- Contradicts the concept
- Is only tangentially related"""

    proposals_text = "\n\n".join([
        f"Proposal {i+1}: {proposal.name}\nConcept: {proposal.concept}\nQuotes: {len(proposal.source_quote_uuids)} quotes\nSimilarity: {similarity:.3f}"
        for proposal, similarity, i in similar_proposals
    ])

    user_prompt = f"""Quote to analyze:
"{quote.text}"
Section: {quote.section or 'N/A'}

Proposed Concepts (sorted by similarity):
{proposals_text}

Does this quote support any of these proposed Concepts? If yes, which one is the best match?"""

    try:
        print(f"[PROPOSAL_MATCH] Calling LLM with {len(similar_proposals)} proposals...")
        result = await llm_with_output.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        print(f"[PROPOSAL_MATCH] LLM returned - should_attribute: {result.should_attribute}, confidence: {result.confidence:.4f}")
        
        if result.should_attribute and result.confidence > 0.7:
            # Return the best matching proposal (highest similarity)
            best_proposal, best_similarity, best_idx = similar_proposals[0]
            match_result = {
                "proposal_idx": best_idx,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "similarity": best_similarity
            }
            print(f"[PROPOSAL_MATCH] Match found! Proposal idx: {best_idx}, name: {best_proposal.name}, similarity: {best_similarity:.4f}")
            print(f"[PROPOSAL_MATCH] Exit - returning match result")
            return match_result
        else:
            print(f"[PROPOSAL_MATCH] LLM rejected match (should_attribute: {result.should_attribute}, confidence: {result.confidence:.4f} <= 0.7)")
        
        print(f"[PROPOSAL_MATCH] Exit - returning None")
        return None
    except Exception as e:
        print(f"[PROPOSAL_MATCH] [ERROR] Error finding proposal match: {e}")
        print(f"[PROPOSAL_MATCH] [ERROR] Exception type: {type(e).__name__}")
        import traceback
        print(f"[PROPOSAL_MATCH] [ERROR] Traceback: {traceback.format_exc()}")
        return None


# ============================================================================
# LangGraph Node Functions
# ============================================================================

async def ensure_indices(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Ensure indices are created for the concept analysis graph."""
    print(f"[ENSURE_INDICES] Entry - node function called")
    print(f"[ENSURE_INDICES] State keys: {list(state.keys())}")
    print(f"[ENSURE_INDICES] content_uuid: {state.get('content_uuid')}")
    
    connection_manager = get_neo4j_connection_manager()
    print(f"[ENSURE_INDICES] Got connection manager")
    
    # Create vector indexes for Concept and Quote nodes
    indexes_to_create = [
        ("Concept", "concept_embeddings_index"),
        ("Quote", "quote_embeddings_index"),
    ]
    
    print(f"[ENSURE_INDICES] Creating {len(indexes_to_create)} vector indexes...")
    
    async with connection_manager.session() as session:
        for idx, (label, index_name) in enumerate(indexes_to_create):
            print(f"[ENSURE_INDICES] Processing index {idx+1}/{len(indexes_to_create)}: {index_name} for label {label}")
            try:
                # Create vector index with 1024 dimensions and cosine similarity
                query = f"""
                CREATE VECTOR INDEX {index_name} IF NOT EXISTS
                FOR (n:{label}) ON (n.embedding)
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: 1024,
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """
                print(f"[ENSURE_INDICES] Executing CREATE INDEX query for {index_name}...")
                result = await session.run(query)
                await result.consume()  # Ensure query completes
                print(f"[ENSURE_INDICES] Created/verified index: {index_name} for label: {label}")
            except Exception as e:
                print(f"[ENSURE_INDICES] Warning: Failed to create index {index_name}: {e}")
                print(f"[ENSURE_INDICES] Exception type: {type(e).__name__}")
                import traceback
                print(f"[ENSURE_INDICES] Traceback: {traceback.format_exc()}")
    
    print(f"[ENSURE_INDICES] Index creation complete")
    print(f"[ENSURE_INDICES] Exit - returning empty dict")
    return {}


async def load_content_and_quotes(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Load content and initialize quote tracking."""
    print(f"[LOAD_DATA] Entry - node function called")
    print(f"[LOAD_DATA] State keys: {list(state.keys())}")
    print(f"[LOAD_DATA] Starting to load content")
    content_uuid = state["content_uuid"]
    print(f"[LOAD_DATA] Content UUID: {content_uuid}")
    
    connection_manager = get_neo4j_connection_manager()
    print(f"[LOAD_DATA] Got connection manager")
    
    try:
        async with connection_manager.session() as session:
            # Fetch content
            print(f"[LOAD_DATA] Opening database session...")
            print(f"[LOAD_DATA] Fetching content from database...")
            content = await find_content_by_uuid(session, content_uuid)
            if not content:
                print(f"[LOAD_DATA] Content not found for UUID: {content_uuid}")
                print(f"[LOAD_DATA] Exit - returning with analysis_complete=True")
                return {
                    "content": None,
                    "analysis_complete": True
                }
            
            print(f"[LOAD_DATA] Found content: {content.title}")
            print(f"[LOAD_DATA] Content UUID: {content.uuid}")
            print(f"[LOAD_DATA] Content type: {type(content).__name__}")
            print(f"[LOAD_DATA] Initializing processed_quote_uuids as empty set")
            
            result = {
                "content": content,
                "processed_quote_uuids": set()  # Start with empty set
            }
            print(f"[LOAD_DATA] Exit - returning result with content and empty processed set")
            return result
        
    except Exception as e:
        print(f"[LOAD_DATA] [ERROR] Error fetching data from database: {e}")
        print(f"[LOAD_DATA] [ERROR] Exception type: {type(e).__name__}")
        import traceback
        print(f"[LOAD_DATA] [ERROR] Traceback: {traceback.format_exc()}")
        print(f"[LOAD_DATA] Exit - returning error result")
        return {
            "content": None,
            "analysis_complete": True
        }

async def attribute_quotes_to_existing_concepts(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Attribute unprocessed quotes to existing concepts and proposed concepts."""
    print(f"[ATTRIBUTE] Entry - node function called")
    print(f"[ATTRIBUTE] State keys: {list(state.keys())}")
    
    content = state.get("content")
    existing_attributions = state.get("quote_attributions", [])
    concept_proposals = state.get("concept_proposals", [])
    processed_uuids = state.get("processed_quote_uuids", set())
    iteration_count = state.get("iteration_count", 0)
    
    print(f"[ATTRIBUTE] Current state:")
    print(f"[ATTRIBUTE]  - content: {content.title if content else None}")
    print(f"[ATTRIBUTE]  - existing_attributions count: {len(existing_attributions)}")
    print(f"[ATTRIBUTE]  - concept_proposals count: {len(concept_proposals)}")
    print(f"[ATTRIBUTE]  - processed_uuids count: {len(processed_uuids)}")
    print(f"[ATTRIBUTE]  - iteration_count: {iteration_count}")
    
    if not content:
        print(f"[ATTRIBUTE] No content found - marking analysis as complete")
        return {
            "quote_attributions": existing_attributions,
            "analysis_complete": True
        }
    
    # Get batch of unprocessed quotes
    print(f"[ATTRIBUTE] Fetching unprocessed quotes (batch size: {BATCH_SIZE}, excluding {len(processed_uuids)} processed)")
    connection_manager = get_neo4j_connection_manager()
    async with connection_manager.session() as session:
        unprocessed_quotes = await get_unprocessed_quotes(
            session,
            content.uuid,
            list(processed_uuids),
            limit=BATCH_SIZE
        )
    
    print(f"[ATTRIBUTE] Retrieved {len(unprocessed_quotes)} unprocessed quotes")
    
    if not unprocessed_quotes:
        print(f"[ATTRIBUTE] No unprocessed quotes remaining - marking analysis as complete")
        return {
            "quote_attributions": existing_attributions,
            "analysis_complete": True
        }
    
    print(f"[ATTRIBUTE] Processing {len(unprocessed_quotes)} quotes...")
    print(f"[ATTRIBUTE] Quote UUIDs to process: {[q.uuid for q in unprocessed_quotes]}")
    
    # Analyze each quote
    new_attributions = []
    newly_processed_uuids = set()
    matched_existing = 0
    matched_proposal = 0
    unmatched = 0
    
    for quote_idx, quote in enumerate(unprocessed_quotes):
        print(f"[ATTRIBUTE] Processing quote {quote_idx+1}/{len(unprocessed_quotes)}: {quote.uuid}")
        print(f"[ATTRIBUTE]  -> Quote preview: {quote.text[:80]}...")
        
        # First try existing concepts
        print(f"[ATTRIBUTE]  -> Step 1: Checking against existing concepts...")
        attribution = await analyze_quote_against_concepts(quote)
        
        if attribution and attribution.should_attribute:
            # Found match with existing concept
            print(f"[ATTRIBUTE]  -> ✓ Matched existing concept: {attribution.concept_uuid}")
            print(f"[ATTRIBUTE]  ->   Confidence: {attribution.confidence:.4f}")
            print(f"[ATTRIBUTE]  ->   Reasoning: {attribution.reasoning[:80]}...")
            new_attributions.append(QuoteAttribution(
                quote_uuid=quote.uuid,
                concept_uuid=attribution.concept_uuid,
                reasoning=attribution.reasoning,
                confidence=attribution.confidence
            ))
            newly_processed_uuids.add(quote.uuid)
            matched_existing += 1
        else:
            # Try proposed concepts
            print(f"[ATTRIBUTE]  -> Step 2: Checking against {len(concept_proposals)} proposed concepts...")
            best_proposal_match = await find_best_proposal_match(quote, concept_proposals)
            
            if best_proposal_match:
                # Add quote to existing proposal
                proposal_idx = best_proposal_match["proposal_idx"]
                proposal_name = concept_proposals[proposal_idx].get("name", "unknown")
                print(f"[ATTRIBUTE]  -> ✓ Matched proposal {proposal_idx}: {proposal_name}")
                print(f"[ATTRIBUTE]  ->   Confidence: {best_proposal_match['confidence']:.4f}")
                print(f"[ATTRIBUTE]  ->   Similarity: {best_proposal_match['similarity']:.4f}")
                concept_proposals[proposal_idx]["source_quote_uuids"].append(quote.uuid)
                newly_processed_uuids.add(quote.uuid)
                matched_proposal += 1
            else:
                print(f"[ATTRIBUTE]  -> ✗ No match found - quote remains unprocessed")
                unmatched += 1
            # If no match, quote remains unprocessed (not added to processed_uuids)
    
    print(f"[ATTRIBUTE] Processing summary:")
    print(f"[ATTRIBUTE]  - Matched existing concepts: {matched_existing}")
    print(f"[ATTRIBUTE]  - Matched proposals: {matched_proposal}")
    print(f"[ATTRIBUTE]  - Unmatched: {unmatched}")
    
    # Combine existing and new attributions
    all_attributions = existing_attributions + [attr.model_dump() for attr in new_attributions]
    print(f"[ATTRIBUTE] Total attributions: {len(all_attributions)} (was {len(existing_attributions)}, added {len(new_attributions)})")
    
    # Update processed UUIDs
    updated_processed = processed_uuids | newly_processed_uuids
    print(f"[ATTRIBUTE] Updated processed UUIDs: {len(updated_processed)} (was {len(processed_uuids)}, added {len(newly_processed_uuids)})")
    
    # Also add quotes that are in proposals to processed set
    proposal_uuids = {uuid for prop in concept_proposals for uuid in prop.get("source_quote_uuids", [])}
    print(f"[ATTRIBUTE] Proposal quote UUIDs: {len(proposal_uuids)}")
    updated_processed = updated_processed | proposal_uuids
    print(f"[ATTRIBUTE] Final processed UUIDs count: {len(updated_processed)}")
    
    new_iteration_count = iteration_count + 1
    print(f"[ATTRIBUTE] Incrementing iteration count: {iteration_count} -> {new_iteration_count}")
    
    print(f"[ATTRIBUTE] Complete: {len(new_attributions)} attributed, {len(updated_processed) - len(processed_uuids)} processed total")
    print(f"[ATTRIBUTE] Exit - returning updated state")
    
    return {
        "quote_attributions": all_attributions,
        "concept_proposals": concept_proposals,
        "processed_quote_uuids": updated_processed,
        "iteration_count": new_iteration_count
    }

async def form_concept_from_seed(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Pick seed quote, find similar quotes using vector search, form concept."""
    print(f"[SEED_CONCEPT] Entry - node function called")
    print(f"[SEED_CONCEPT] State keys: {list(state.keys())}")
    
    content = state.get("content")
    existing_proposals = state.get("concept_proposals", [])
    processed_uuids = state.get("processed_quote_uuids", set())
    iteration_count = state.get("iteration_count", 0)
    
    print(f"[SEED_CONCEPT] Current state:")
    print(f"[SEED_CONCEPT]  - content: {content.title if content else None}")
    print(f"[SEED_CONCEPT]  - existing_proposals count: {len(existing_proposals)}")
    print(f"[SEED_CONCEPT]  - processed_uuids count: {len(processed_uuids)}")
    print(f"[SEED_CONCEPT]  - iteration_count: {iteration_count}")
    
    if not content:
        print(f"[SEED_CONCEPT] No content found - marking analysis as complete")
        return {
            "concept_proposals": existing_proposals,
            "analysis_complete": True
        }
    
    # Get one unprocessed quote as seed
    print(f"[SEED_CONCEPT] Fetching seed quote candidate (excluding {len(processed_uuids)} processed)...")
    connection_manager = get_neo4j_connection_manager()
    async with connection_manager.session() as session:
        seed_candidates = await get_unprocessed_quotes(
            session,
            content.uuid,
            list(processed_uuids),
            limit=1
        )
    
    print(f"[SEED_CONCEPT] Retrieved {len(seed_candidates)} seed candidate(s)")
    
    if not seed_candidates:
        print(f"[SEED_CONCEPT] No unprocessed quotes remaining - marking analysis as complete")
        return {
            "concept_proposals": existing_proposals,
            "analysis_complete": True
        }
    
    seed_quote = seed_candidates[0]
    print(f"[SEED_CONCEPT] Using seed quote: {seed_quote.uuid}")
    print(f"[SEED_CONCEPT] Seed quote preview: {seed_quote.text[:80]}...")
    print(f"[SEED_CONCEPT] Seed quote section: {seed_quote.section or 'N/A'}")
    
    # Find similar quotes using vector search
    print(f"[SEED_CONCEPT] Searching for similar quotes (limit: {MAX_QUOTE_GROUP_SIZE})...")
    similar_quotes = await get_similar_quotes_for_seed(
        seed_quote.text,
        content.uuid,
        processed_uuids,
        limit=MAX_QUOTE_GROUP_SIZE
    )
    
    print(f"[SEED_CONCEPT] Vector search returned {len(similar_quotes)} similar quotes")
    
    # If no similar quotes found, just use seed
    if not similar_quotes:
        print(f"[SEED_CONCEPT] No similar quotes found - using seed quote only")
        similar_quotes = [seed_quote]
    else:
        # Ensure seed is included
        seed_in_list = seed_quote.uuid in {q.uuid for q in similar_quotes}
        print(f"[SEED_CONCEPT] Seed quote in similar list: {seed_in_list}")
        if not seed_in_list:
            print(f"[SEED_CONCEPT] Adding seed quote to front of similar quotes list")
            similar_quotes.insert(0, seed_quote)
        else:
            print(f"[SEED_CONCEPT] Seed quote already in similar quotes list")
    
    print(f"[SEED_CONCEPT] Final quote group size: {len(similar_quotes)}")
    print(f"[SEED_CONCEPT] Quote UUIDs in group: {[q.uuid for q in similar_quotes]}")
    
    # Form concept proposal
    print(f"[SEED_CONCEPT] Generating concept proposal from {len(similar_quotes)} quotes...")
    proposal = await propose_concept_from_quotes(similar_quotes, content.title)
    
    if proposal:
        # Add to existing proposals
        new_proposals = existing_proposals + [proposal.model_dump()]
        print(f"[SEED_CONCEPT] ✓ Created concept: '{proposal.name}' from {len(similar_quotes)} quotes")
        print(f"[SEED_CONCEPT] Proposal details:")
        print(f"[SEED_CONCEPT]  - Title: {proposal.title}")
        print(f"[SEED_CONCEPT]  - Concept length: {len(proposal.concept)} chars")
        print(f"[SEED_CONCEPT]  - Source quote UUIDs: {len(proposal.source_quote_uuids)}")
    else:
        new_proposals = existing_proposals
        print(f"[SEED_CONCEPT] ✗ Failed to create concept from {len(similar_quotes)} quotes")
    
    # Update processed UUIDs
    processed_quote_uuids = {q.uuid for q in similar_quotes}
    print(f"[SEED_CONCEPT] Marking {len(processed_quote_uuids)} quotes as processed")
    updated_processed = processed_uuids | processed_quote_uuids
    print(f"[SEED_CONCEPT] Updated processed UUIDs: {len(updated_processed)} (was {len(processed_uuids)}, added {len(processed_quote_uuids)})")
    
    # Count remaining unprocessed quotes
    print(f"[SEED_CONCEPT] Checking remaining unprocessed quotes...")
    async with connection_manager.session() as session:
        remaining = await get_unprocessed_quotes(
            session,
            content.uuid,
            list(updated_processed),
            limit=1
        )
        remaining_count = len(remaining)
    
    print(f"[SEED_CONCEPT] Remaining unprocessed quotes: {remaining_count}")
    
    new_iteration_count = iteration_count + 1
    print(f"[SEED_CONCEPT] Incrementing iteration count: {iteration_count} -> {new_iteration_count}")
    print(f"[SEED_CONCEPT] Exit - returning updated state")
    
    return {
        "concept_proposals": new_proposals,
        "processed_quote_uuids": updated_processed,
        "iteration_count": new_iteration_count
    }


# ============================================================================
# Conditional Edge Functions
# ============================================================================

def should_continue(state: State) -> Literal["attribute", "end"]:
    """Decide whether to continue with attribution or end."""
    print(f"[CONDITIONAL] Entry - evaluating whether to continue")
    print(f"[CONDITIONAL] State keys: {list(state.keys())}")
    
    content = state.get("content")
    processed_uuids = state.get("processed_quote_uuids", set())
    iteration_count = state.get("iteration_count", 0)
    analysis_complete = state.get("analysis_complete", False)
    
    print(f"[CONDITIONAL] Current values:")
    print(f"[CONDITIONAL]  - content: {content.title if content else None}")
    print(f"[CONDITIONAL]  - processed_uuids count: {len(processed_uuids)}")
    print(f"[CONDITIONAL]  - iteration_count: {iteration_count}")
    print(f"[CONDITIONAL]  - analysis_complete: {analysis_complete}")
    
    # Prevent infinite loops - max 100 iterations
    if iteration_count >= 100:
        print(f"[CONDITIONAL] Max iterations reached ({iteration_count}) - ending analysis")
        print(f"[CONDITIONAL] Exit - returning 'end'")
        return "end"
    
    if analysis_complete:
        print(f"[CONDITIONAL] Analysis marked as complete - ending")
        print(f"[CONDITIONAL] Exit - returning 'end'")
        return "end"
    
    if not content:
        print(f"[CONDITIONAL] No content - ending")
        print(f"[CONDITIONAL] Exit - returning 'end'")
        return "end"
    
    # Check if there are unprocessed quotes by attempting a quick query
    # (We'll use a simpler check - if we have quotes, assume there might be more)
    print(f"[CONDITIONAL] Conditions passed - continuing")
    print(f"[CONDITIONAL] {len(processed_uuids)} quotes processed - continuing (iteration {iteration_count + 1})")
    print(f"[CONDITIONAL] Exit - returning 'attribute'")
    return "attribute"


# ============================================================================
# Graph Definition
# ============================================================================

# Define the graph
graph = (
    StateGraph(State, input_schema=InputState, context_schema=Context)
    .add_node("ensure_indices", ensure_indices)
    .add_node("load_content_and_quotes", load_content_and_quotes)
    .add_node("attribute_quotes_to_existing_concepts", attribute_quotes_to_existing_concepts)
    .add_node("form_concept_from_seed", form_concept_from_seed)
    
    # Sequential edges
    .add_edge("__start__", "ensure_indices")
    .add_edge("ensure_indices", "load_content_and_quotes")
    .add_edge("load_content_and_quotes", "attribute_quotes_to_existing_concepts")
    
    # Conditional edge after attribution
    .add_conditional_edges(
        "attribute_quotes_to_existing_concepts",
        should_continue,
        {
            "attribute": "form_concept_from_seed",
            "end": "__end__"
        }
    )
    
    # Conditional edge after concept formation
    .add_conditional_edges(
        "form_concept_from_seed", 
        should_continue,
        {
            "attribute": "attribute_quotes_to_existing_concepts",
            "end": "__end__"
        }
    )
    
    .compile(name="Concept Analysis")
)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        print("[main] Starting Concept Analysis Graph execution")
        
        # Example usage - replace with actual content UUID
        result = await graph.ainvoke({
            "content_uuid": "43ecf73b-01c6-426d-978a-1b73e041370c"
        }, {"recursion_limit": 100})
        
        print("[main] Graph execution completed")
        print(f"[main] Final result: {result}")
        return result
        
    if "GOOGLE_API_KEY" not in os.environ:
        print("[main] Setting GOOGLE_API_KEY environment variable")
        os.environ["GOOGLE_API_KEY"] = "AIzaSyCw3FzCBecZscg1bh5auhEtkMWLzg3wDTs"
    
    print("[main] Starting asyncio execution")
    result = asyncio.run(main())
