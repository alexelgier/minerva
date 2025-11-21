"""Web search utilities for enriching Author and Content nodes with web information.

This module provides functions to search the web for author and book information
using Google's native Google Search tool (grounding) via Gemini API, and then use LLM 
to extract and synthesize relevant information.

See: https://ai.google.dev/gemini-api/docs/google-search
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI


class AuthorEnrichmentResponse(BaseModel):
    """Structured response for author enrichment."""
    summary: str = Field(..., description="Comprehensive summary of the author's life, work, and significance. Max 300 words.")
    summary_short: str = Field(..., description="Short summary of the author. Max 50 words.")
    occupation: str = Field(..., description="Primary occupation or profession of the author.")


class BookEnrichmentResponse(BaseModel):
    """Structured response for book enrichment."""
    summary: str = Field(..., description="Enhanced summary of the book incorporating web information. Max 300 words.")
    summary_short: str = Field(..., description="Short enhanced summary. Max 50 words.")


# Lazy initialization
_llm_with_search = None
_llm_structured = None


def _get_llm_with_search():
    """Get or initialize the LLM with Google Search tool bound."""
    global _llm_with_search
    if _llm_with_search is None:
        # Use ChatGoogleGenerativeAI directly to bind the google_search tool
        # The google_search tool is built into Gemini API and doesn't require CSE ID
        _llm_with_search = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0
        ).bind_tools([{"google_search": {}}])
    return _llm_with_search


def _get_llm_structured():
    """Get or initialize the LLM for structured output (without search)."""
    global _llm_structured
    if _llm_structured is None:
        _llm_structured = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            temperature=0
        )
    return _llm_structured


async def enrich_author_with_web_search(
    author_name: str,
    existing_summary: Optional[str] = None,
    existing_occupation: Optional[str] = None
) -> Optional[AuthorEnrichmentResponse]:
    """
    Enrich author information using Google's native search tool (grounding).
    
    Uses Gemini's built-in Google Search tool to search the web for information about 
    the author and then uses LLM to synthesize a comprehensive summary, short summary, 
    and occupation.
    
    Args:
        author_name: Name of the author to search for
        existing_summary: Existing summary to enhance (optional)
        existing_occupation: Existing occupation to enhance (optional)
        
    Returns:
        AuthorEnrichmentResponse with enriched information, or None if search fails
        
    Example:
        ```python
        response = await enrich_author_with_web_search("Vladimir Lenin")
        if response:
            print(response.summary)
            print(response.occupation)
        ```
    """
    try:
        # Use LLM with Google Search tool bound - it will automatically search if needed
        llm_with_search = _get_llm_with_search()
        
        existing_info = ""
        if existing_summary:
            existing_info += f"\nExisting summary: {existing_summary}\n"
        if existing_occupation:
            existing_info += f"Existing occupation: {existing_occupation}\n"
        
        # Create prompt that will trigger web search
        prompt = f"""Search the web for information about the author {author_name} and create a comprehensive summary.

Author name: {author_name}
{existing_info}

Based on web search results, create a comprehensive summary of the author's life, work, and significance. 
If existing information is provided, enhance and expand upon it with the web search information.
Focus on:
- Their background and biography
- Their major works and contributions
- Their significance in their field
- Their occupation/profession

Provide a comprehensive summary (max 300 words), a short summary (max 50 words), and their primary occupation.
Format your response as JSON with fields: summary, summary_short, and occupation."""
        
        # Invoke with search tool - model will automatically search if needed
        response = await llm_with_search.ainvoke(prompt)
        
        # Extract text from response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse the structured response using a separate LLM call for structured output
        llm_structured = _get_llm_structured()
        llm_structured_output = llm_structured.with_structured_output(
            AuthorEnrichmentResponse, 
            method="json_schema"
        )
        
        # Ask the structured LLM to extract the information from the search-enhanced response
        extraction_prompt = f"""Extract the author information from the following text and format it as structured data:

{response_text}

Extract:
- summary: Comprehensive summary (max 300 words)
- summary_short: Short summary (max 50 words)  
- occupation: Primary occupation or profession"""
        
        structured_response = await llm_structured_output.ainvoke(extraction_prompt)
        return structured_response
        
    except Exception as e:
        # Log error but don't fail the workflow
        print(f"Error enriching author {author_name} with web search: {e}")
        return None


async def enrich_summary_with_web_search(
    book_title: str,
    author_name: str,
    existing_summary: Optional[str] = None,
    existing_summary_short: Optional[str] = None
) -> Optional[BookEnrichmentResponse]:
    """
    Enrich book summary using Google's native search tool (grounding).
    
    Uses Gemini's built-in Google Search tool to search the web for information about 
    the book and then uses LLM to enhance the existing summary with additional context.
    
    Args:
        book_title: Title of the book
        author_name: Name of the author
        existing_summary: Existing summary to enhance (optional)
        existing_summary_short: Existing short summary to enhance (optional)
        
    Returns:
        BookEnrichmentResponse with enriched summaries, or None if search fails
        
    Example:
        ```python
        response = await enrich_summary_with_web_search(
            "Obras Completas Tomo IV",
            "Vladimir Lenin",
            existing_summary="..."
        )
        if response:
            print(response.summary)
        ```
    """
    try:
        # Use LLM with Google Search tool bound - it will automatically search if needed
        llm_with_search = _get_llm_with_search()
        
        existing_info = ""
        if existing_summary:
            existing_info += f"\nExisting summary: {existing_summary}\n"
        if existing_summary_short:
            existing_info += f"Existing short summary: {existing_summary_short}\n"
        
        # Create prompt that will trigger web search
        prompt = f"""Search the web for information about the book "{book_title}" by {author_name} and enhance the summary.

Book title: {book_title}
Author: {author_name}
{existing_info}

Based on web search results, enhance the book summary with additional context and information.
If existing summaries are provided, expand and enrich them with relevant information from the web search.
Focus on:
- The book's main themes and topics
- Its historical or cultural significance
- Key concepts or ideas covered
- Its reception or importance

Provide an enhanced comprehensive summary (max 300 words) and a short summary (max 50 words).
Format your response as JSON with fields: summary and summary_short."""
        
        # Invoke with search tool - model will automatically search if needed
        response = await llm_with_search.ainvoke(prompt)
        
        # Extract text from response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse the structured response using a separate LLM call for structured output
        llm_structured = _get_llm_structured()
        llm_structured_output = llm_structured.with_structured_output(
            BookEnrichmentResponse, 
            method="json_schema"
        )
        
        # Ask the structured LLM to extract the information from the search-enhanced response
        extraction_prompt = f"""Extract the book summary information from the following text and format it as structured data:

{response_text}

Extract:
- summary: Enhanced comprehensive summary (max 300 words)
- summary_short: Enhanced short summary (max 50 words)"""
        
        structured_response = await llm_structured_output.ainvoke(extraction_prompt)
        return structured_response
        
    except Exception as e:
        # Log error but don't fail the workflow
        print(f"Error enriching book {book_title} with web search: {e}")
        return None

