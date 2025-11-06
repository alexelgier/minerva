"""LangGraph pipeline for parsing book quotes from markdown files and storing them in Neo4j."""

from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Dict, List
from datetime import datetime

from langgraph.graph import StateGraph
import aiofiles
import re
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_neo4j import Neo4jVector
from langchain_core.documents import Document

from minerva_models import Content, Person, ResourceType, ResourceStatus, Quote
from langchain_ollama import OllamaEmbeddings

from zettel_agent.db import (
    get_neo4j_connection_manager,
    search_person_by_name,
    create_person,
    create_content,
    create_authored_by_relationship,
)

# Lazy initialization to avoid blocking on module import
_llm = None
_quote_vector = None

async def _get_llm():
    """Get or initialize the LLM using LangChain's standard chat model initialization."""
    global _llm
    if _llm is None:
        # Use init_chat_model with Google GenAI provider (keeps Gemini model)
        _llm = init_chat_model(
            model="gemini-2.5-flash-lite",
            model_provider="google-genai",
            temperature=0
        )
    return _llm

async def _get_quote_vector():
    """Get or initialize the Neo4jVector for Quote storage."""
    global _quote_vector
    if _quote_vector is None:
        connection_manager = get_neo4j_connection_manager()
        _quote_vector = Neo4jVector.from_existing_index(
            embedding=OllamaEmbeddings(model="mxbai-embed-large:latest"),
            node_label="Quote",
            index_name="quote_embeddings_index",
            url=connection_manager.uri,
            username=connection_manager.auth[0],
            password=connection_manager.auth[1],
            database="neo4j",
        )
    return _quote_vector

@dataclass
class InputState:
    file_path: str
    author: str
    title: str

@dataclass
class State:
    file_path: str
    author: str
    title: str
    file_content: str = None
    book: Content = None
    parsed_author: Person = None
    quotes: List[Quote] = None
    sections: List[str] = None
    summary: str = None
    summary_short: str = None

class SummaryResponse(BaseModel):
    summary: str = Field(..., description="Summary of the book. Max 100 words.")
    summary_short: str = Field(..., description="Short summary of the book. Max 30 words.")

async def read_file(state: State) -> Dict[str, Any]:
    """Read the file content into state."""
    async with aiofiles.open(state.file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    return {"file_content": content}

def _parse_quotes_from_content(content: str) -> List[Quote]:
    """Parse quotes from markdown content."""
    quotes = []
    
    # Find the "# Citas" section
    citas_match = re.search(r'# Citas\n\n(.*)', content, re.DOTALL)
    if not citas_match:
        return quotes
    
    citas_content = citas_match.group(1)
    
    # Split by sections (## headers)
    section_pattern = r'##\s+(.+?)\n(.*?)(?=##\s+|\Z)'
    sections = re.findall(section_pattern, citas_content, re.DOTALL)
    
    for section_title, section_content in sections:
        section_title = section_title.strip()
        
        # Split section content into individual quotes
        # Quotes are separated by blank lines and may end with page numbers
        quote_blocks = re.split(r'\n\n+', section_content.strip())
        
        for block in quote_blocks:
            block = block.strip()
            if not block:
                continue
            
            # Extract page reference (number at the end)
            page_match = re.search(r'\n(\d+(?:-\d+)?)\s*$', block)
            page_reference = page_match.group(1) if page_match else None
            
            # Remove page reference from quote text
            if page_reference:
                quote_text = block[:page_match.start()].strip()
            else:
                quote_text = block
            
            # Skip if quote is too short (likely parsing error)
            if len(quote_text) < 20:
                continue
            
            quotes.append(Quote(
                text=quote_text,
                section=section_title,
                page_reference=page_reference
            ))
    
    return quotes

async def make_summary(state: State) -> Dict[str, Any]:
    """Generate summary and short summary for the book."""
    llm = await _get_llm()
    llm_structured = llm.with_structured_output(SummaryResponse, method="json_schema")
    
    prompt = f"""You are a helpful assistant that generates summaries for a book from the notes the user has taken about the book.
Book title: {state.title}
Book author: {state.author}
Here are the notes the user has taken about the book:
{state.file_content}
---
Generate a summary and a short summary of the book."""
    
    response = await llm_structured.ainvoke(prompt)
    
    return {
        "summary": response.summary,
        "summary_short": response.summary_short
    }


async def parse_quotes(state: State) -> Dict[str, Any]:
    """Parse quotes from the file and create book entity."""
    book = Content(
        name=f"{state.author} - {state.title}",
        author=state.author,
        title=state.title,
        summary=state.summary,
        summary_short=state.summary_short,
        category=ResourceType.BOOK,
        status=ResourceStatus.COMPLETED,
    )
    
    quotes = _parse_quotes_from_content(state.file_content)
    sections = list(set(q.section for q in quotes))
    
    return {
        "book": book,
        "quotes": quotes,
        "sections": sections
    }

async def ensure_author_exists(state: State) -> Dict[str, Any]:
    """Ensure the author exists as a Person entity, creating if necessary."""
    connection_manager = get_neo4j_connection_manager()
    
    async with connection_manager.session() as session:
        existing_persons = await search_person_by_name(session, state.author)
        
        # Find exact name match
        author_person = next(
            (p for p in existing_persons if p.name.lower() == state.author.lower()), 
            None
        )
        
        # Create if not found
        if author_person is None:
            author_person = Person(
                name=state.author,
                summary=f"Author of {state.title}",
                summary_short=f"Author of {state.title}",
                occupation="Author"
            )
            author_person.uuid = await create_person(session, author_person)
    
    return {"parsed_author": author_person}
    
async def write_to_db(state: State) -> Dict[str, Any]:
    """Write book, author relationship, and quotes to database."""
    connection_manager = get_neo4j_connection_manager()
    
    async with connection_manager.session() as session:
        content_uuid = await create_content(session, state.book)
        
        # Create author relationship
        if state.parsed_author:
            await create_authored_by_relationship(
                session, state.parsed_author.uuid, content_uuid
            )
        
        # Create quotes using langchain-neo4j if they exist
        if state.quotes:
            quote_vector = await _get_quote_vector()
            
            # Convert Quote objects to langchain Document objects
            documents = []
            for quote in state.quotes:
                doc = Document(
                    page_content=quote.text,
                    metadata={
                        'partition': 'LEXICAL',
                        'created_at': quote.created_at if hasattr(quote, 'created_at') else datetime.now(),
                        'page_reference': quote.page_reference,
                        'uuid': quote.uuid,
                        'type': 'Quote',
                        'section': quote.section,
                        'content_uuid': content_uuid,
                    }
                )
                documents.append(doc)
            
            # Add documents to Neo4jVector (automatically handles embeddings)
            quote_vector.add_documents(documents)
            
            # Create QUOTED_IN relationships
            quote_uuids = [doc.metadata['uuid'] for doc in documents]
            relationship_query = """
            MATCH (c:Content {uuid: $content_uuid})
            UNWIND $quote_uuids AS quote_uuid
            MATCH (q:Quote {uuid: quote_uuid})
            MERGE (q)-[:QUOTED_IN]->(c)
            """
            await session.run(relationship_query, content_uuid=content_uuid, quote_uuids=quote_uuids)
    
    return {"book": state.book, "content_uuid": content_uuid}

graph = (
    StateGraph(State, input_schema=InputState)
    .add_node("read_file", read_file)
    .add_node("make_summary", make_summary)
    .add_node("parse_quotes", parse_quotes)
    .add_node("ensure_author_exists", ensure_author_exists)
    .add_node("write_to_db", write_to_db)
    .add_edge("__start__", "read_file")
    .add_edge("read_file", "make_summary")
    .add_edge("make_summary", "parse_quotes")
    .add_edge("parse_quotes", "ensure_author_exists")
    .add_edge("ensure_author_exists", "write_to_db")
    .add_edge("write_to_db", "__end__")
    .compile(name="Quote Parser")
)

if __name__ == "__main__":
    import asyncio
    
    async def main():
        if "GOOGLE_API_KEY" not in os.environ:
            os.environ["GOOGLE_API_KEY"] = "AIzaSyCw3FzCBecZscg1bh5auhEtkMWLzg3wDTs"
        
        result = await graph.ainvoke({
            "file_path": r"D:\yo\04 - Culture\Libros\Lenin\Tomo IV.md",
            "author": "Vladimir Lenin",
            "title": "Obras Completas Tomo IV",
        })
        
        return result
    
    asyncio.run(main())