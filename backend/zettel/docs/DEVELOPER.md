# Developer Guide

Guide for extending and modifying the zettel_agent module.

## Table of Contents

- [Code Organization](#code-organization)
- [Adding New Graph Nodes](#adding-new-graph-nodes)
- [Modifying State Schemas](#modifying-state-schemas)
- [Adding Database Queries](#adding-database-queries)
- [Customizing LLM Prompts](#customizing-llm-prompts)
- [Testing Strategies](#testing-strategies)
- [Debugging Techniques](#debugging-techniques)
- [Common Patterns](#common-patterns)

---

## Code Organization

### Project Structure

```
zettel/
├── src/
│   └── zettel_agent/
│       ├── __init__.py              # Module exports
│       ├── quote_parse_graph.py     # Quote parsing workflow
│       ├── concept_extraction_graph.py # Concept extraction workflow
│       ├── db.py                    # Neo4j operations
│       ├── obsidian_utils.py        # Obsidian file generation
│       └── CONCEPT_EXTRACTION_DESIGN.md # Design document
├── docs/                            # Documentation
├── langgraph.json                   # LangGraph configuration
└── pyproject.toml                   # Poetry dependencies
```

### Module Responsibilities

**`db.py`:**
- Neo4j connection management
- Database query functions
- Serialization/deserialization utilities

**`quote_parse_graph.py`:**
- Quote parsing workflow
- Markdown parsing logic
- Book summary generation

**`concept_extraction_graph.py`:**
- Concept extraction workflow
- LLM integration
- Quality validation
- Human-in-the-loop support

**`obsidian_utils.py`:**
- Obsidian file generation
- Frontmatter formatting
- Content formatting

---

## Adding New Graph Nodes

### Step-by-Step Guide

**1. Define Node Function:**

```python
async def my_new_node(state: ConceptExtractionState) -> Dict[str, Any]:
    """
    Description of what this node does.
    
    Args:
        state: Current workflow state
        
    Returns:
        Dict with state updates
    """
    # Access state
    quotes = state.get("quotes", [])
    
    # Perform operation
    result = await some_operation(quotes)
    
    # Return state update
    return {
        "new_field": result,
        "phase": "next_phase"
    }
```

**2. Add Node to Graph:**

```python
builder.add_node("my_new_node", my_new_node)
```

**3. Add Edges:**

```python
# Add edge from previous node
builder.add_edge("previous_node", "my_new_node")

# Add edge to next node
builder.add_edge("my_new_node", "next_node")

# Or use conditional edge
builder.add_conditional_edges(
    "my_new_node",
    routing_function,
    {
        "option1": "node1",
        "option2": "node2"
    }
)
```

**4. Update State Schema (if needed):**

```python
class ConceptExtractionState(TypedDict):
    # ... existing fields ...
    new_field: Optional[NewType]  # Add new field
```

### Best Practices

- **Single Responsibility:** Each node should do one thing
- **Error Handling:** Always handle errors and update state
- **State Updates:** Return only changed fields
- **Documentation:** Add comprehensive docstrings

---

## Modifying State Schemas

### Adding New Fields

**1. Update TypedDict:**

```python
class ConceptExtractionState(TypedDict):
    # ... existing fields ...
    new_field: Optional[NewType]
```

**2. Update Initial State:**

Ensure new fields are initialized when creating initial state.

**3. Update Nodes:**

Update nodes that need to read/write the new field.

### Using Reducers

**For Accumulating Lists:**

```python
from typing_extensions import Annotated
import operator

class ConceptExtractionState(TypedDict):
    # Use Annotated with operator.add for accumulation
    my_list: Annotated[List[Dict], operator.add]
```

**Benefits:**
- Prevents overwriting previous values
- Allows parallel nodes to contribute
- Automatic accumulation

**Example:**
```python
# Node 1
return {"my_list": [item1, item2]}

# Node 2 (parallel)
return {"my_list": [item3, item4]}

# Result: my_list = [item1, item2, item3, item4]
```

---

## Adding Database Queries

### Step-by-Step Guide

**1. Define Query Function:**

```python
async def my_new_query(
    session: AsyncSession,
    param1: str,
    param2: int
) -> List[MyModel]:
    """
    Description of query.
    
    Args:
        session: Neo4j session
        param1: Description
        param2: Description
        
    Returns:
        List of model objects
    """
    query = """
    MATCH (n:NodeType {field: $param1})
    WHERE n.other_field > $param2
    RETURN n
    ORDER BY n.field ASC
    """
    
    result = await session.run(query, param1=param1, param2=param2)
    items = []
    async for record in result:
        properties = dict(record["n"])
        items.append(deserialize_to_model(properties, MyModel))
    return items
```

**2. Follow Patterns:**

- Use parameterized queries (prevent injection)
- Deserialize results to Pydantic models
- Handle None/empty results
- Include error handling

**3. Export Function:**

Add to `__init__.py` if needed for external use.

### Common Patterns

**Finding by UUID:**
```python
query = "MATCH (n:NodeType {uuid: $uuid}) RETURN n"
```

**Creating Nodes:**
```python
query = "CREATE (n:NodeType $properties) RETURN n.uuid as uuid"
properties = serialize_model(model)
```

**Creating Relationships:**
```python
query = """
MATCH (a:NodeA {uuid: $uuid_a})
MATCH (b:NodeB {uuid: $uuid_b})
CREATE (a)-[:RELATIONSHIP]->(b)
"""
```

---

## Customizing LLM Prompts

### System Prompts

**Location:** In node functions

**Pattern:**
```python
system_prompt = """You are a Zettelkasten expert.

Guidelines:
- Rule 1
- Rule 2
- Rule 3

Output requirements:
- Requirement 1
- Requirement 2
"""
```

**Best Practices:**
- Be specific about role
- Include all guidelines
- Specify output format
- Provide examples if helpful

### User Prompts

**Pattern:**
```python
user_prompt = f"""Context Information:
{context}

Data:
{data}

Task:
{task_description}
"""
```

**Best Practices:**
- Include all relevant context
- Format data clearly
- Be explicit about task
- Use structured format

### Structured Outputs

**Define Pydantic Model:**
```python
class MyResponse(BaseModel):
    field1: str = Field(..., description="Description")
    field2: List[str] = Field(..., description="Description")
```

**Use with LLM:**
```python
llm_structured = llm.with_structured_output(
    MyResponse,
    method="json_schema"
)
response = await llm_structured.ainvoke([...])
```

---

## Testing Strategies

### Unit Testing

**Test Individual Functions:**
```python
import pytest
from zettel_agent.db import serialize_model

def test_serialize_model():
    from minerva_models import Content
    from datetime import datetime
    
    content = Content(
        title="Test",
        created_at=datetime.now()
    )
    result = serialize_model(content)
    assert isinstance(result["created_at"], str)
```

### Integration Testing

**Test Graph Workflows:**
```python
async def test_quote_parse_graph():
    from zettel_agent.quote_parse_graph import graph
    
    result = await graph.ainvoke({
        "file_path": "test.md",
        "author": "Test Author",
        "title": "Test Title"
    })
    
    assert "content_uuid" in result
```

### Mocking

**Mock External Services:**
```python
from unittest.mock import AsyncMock, patch

@patch('zettel_agent.db.get_neo4j_connection_manager')
async def test_with_mock(mock_manager):
    mock_session = AsyncMock()
    mock_manager.return_value.session.return_value.__aenter__.return_value = mock_session
    
    # Test with mocked database
```

---

## Debugging Techniques

### State Inspection

**Print State:**
```python
async def my_node(state: ConceptExtractionState) -> Dict[str, Any]:
    print(f"Current state: {state}")
    # ... rest of function
```

**Log State Updates:**
```python
import logging

logger = logging.getLogger(__name__)

async def my_node(state: ConceptExtractionState) -> Dict[str, Any]:
    logger.debug(f"State before: {state}")
    result = await operation()
    logger.debug(f"State update: {result}")
    return result
```

### LangGraph Studio

**Visual Debugging:**
1. Start LangGraph dev server
2. Open LangGraph Studio
3. Connect to server
4. Run workflow
5. Inspect state at each node

### Error Tracing

**Check Error Accumulation:**
```python
errors = state.get("errors", [])
if errors:
    print(f"Errors: {errors}")
```

**Check Warnings:**
```python
warnings = state.get("warnings", [])
if warnings:
    print(f"Warnings: {warnings}")
```

### Database Inspection

**Query Neo4j:**
```cypher
// Check nodes
MATCH (n) RETURN n LIMIT 10

// Check relationships
MATCH (a)-[r]->(b) RETURN a, r, b LIMIT 10

// Check vector indexes
SHOW INDEXES
```

---

## Common Patterns

### Lazy Initialization

**Pattern:**
```python
_llm = None

async def _get_llm():
    global _llm
    if _llm is None:
        _llm = init_chat_model(...)
    return _llm
```

**Benefits:**
- Reduces startup time
- Saves resources
- Initializes on first use

### Error Handling in Nodes

**Pattern:**
```python
async def my_node(state: ConceptExtractionState) -> Dict[str, Any]:
    try:
        result = await operation()
        return {"result": result}
    except Exception as e:
        return {
            "errors": [f"Operation failed: {str(e)}"],
            "phase": "end"
        }
```

### Conditional Routing

**Pattern:**
```python
def should_continue(state: ConceptExtractionState) -> Literal["option1", "option2", "end"]:
    if state.get("errors"):
        return "end"
    if condition:
        return "option1"
    return "option2"
```

### State Updates

**Pattern:**
```python
# Return only changed fields
return {
    "field1": new_value,
    "field2": updated_value
}

# Use reducers for lists
return {
    "my_list": [new_item]  # Will be added to existing list
}
```

### Database Session Management

**Pattern:**
```python
connection_manager = get_neo4j_connection_manager()
async with connection_manager.session() as session:
    result = await query_function(session, ...)
```

### LLM Structured Output

**Pattern:**
```python
llm = await _get_llm()
llm_structured = llm.with_structured_output(
    ResponseModel,
    method="json_schema"
)
response = await llm_structured.ainvoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_prompt)
])
```

---

## Code Style Guidelines

### Type Hints

**Always use type hints:**
```python
async def my_function(
    param1: str,
    param2: int
) -> Dict[str, Any]:
    ...
```

### Docstrings

**Use Google-style docstrings:**
```python
def my_function(param1: str, param2: int) -> Dict[str, Any]:
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
```

### Naming Conventions

- **Functions:** `snake_case`
- **Classes:** `PascalCase`
- **Constants:** `UPPER_SNAKE_CASE`
- **Private functions:** `_leading_underscore`

### Import Organization

```python
# Standard library
from typing import Dict, List

# Third-party
from langchain import ...
from neo4j import ...

# Local
from zettel_agent.db import ...
```

---

## See Also

- [API Reference](API.md) - Complete API documentation
- [Architecture Documentation](ARCHITECTURE.md) - Technical architecture
- [Workflows Documentation](WORKFLOWS.md) - Workflow details

