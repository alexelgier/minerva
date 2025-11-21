# Zettel Agent Documentation

Comprehensive documentation for the zettel_agent module.

## Documentation Index

### [API Reference](API.md)

Complete API reference for all public functions, classes, and modules.

**Contents:**
- Database module (`db.py`) - All query functions and connection management
- Concept Extraction Graph - All node functions and state schemas
- Quote Parse Graph - All node functions and state schemas
- Obsidian Utilities - File generation functions
- Pydantic models and data structures

**Use this when:**
- You need to understand a specific function's parameters and return values
- You're integrating the module into another system
- You're looking for code examples

### [Architecture Documentation](ARCHITECTURE.md)

Deep technical architecture documentation covering system design and implementation details.

**Contents:**
- System architecture overview
- State management patterns
- Graph structure and node relationships
- Vector search implementation
- LLM integration patterns
- Database schema
- Error handling strategies
- Performance considerations

**Use this when:**
- You want to understand how the system works internally
- You're debugging complex issues
- You're planning modifications or extensions
- You need to understand performance characteristics

### [Developer Guide](DEVELOPER.md)

Guide for extending and modifying the module.

**Contents:**
- Code organization and structure
- Adding new graph nodes
- Modifying state schemas
- Adding database queries
- Customizing LLM prompts
- Testing strategies
- Debugging techniques
- Common patterns and best practices

**Use this when:**
- You're adding new features
- You're modifying existing functionality
- You need to understand code patterns
- You're writing tests

### [Workflows Documentation](WORKFLOWS.md)

Detailed workflow documentation for both graphs.

**Contents:**
- Quote Parse Graph - Step-by-step execution flow
- Concept Extraction Graph - All three phases in detail
- State transitions and routing logic
- Error recovery flows

**Use this when:**
- You want to understand the complete workflow
- You're debugging workflow issues
- You need to understand state transitions
- You're troubleshooting errors

## Quick Links

### Getting Started
- [Main README](../README.md) - Overview and quick start guide
- [Setup Guide](../../../docs/setup/zettel-setup.md) - Detailed setup instructions

### Project-Level Documentation
- [Architecture](../../../docs/architecture/zettel.md) - Project-level architecture
- [Usage Guide](../../../docs/usage/zettel.md) - Usage examples and patterns

### Design Documents
- [Concept Extraction Design](../src/zettel_agent/CONCEPT_EXTRACTION_DESIGN.md) - Detailed design document

## Documentation Structure

```
zettel/
├── README.md                    # Main module README
├── docs/
│   ├── README.md               # This file (documentation index)
│   ├── API.md                  # API reference
│   ├── ARCHITECTURE.md         # Architecture documentation
│   ├── DEVELOPER.md            # Developer guide
│   └── WORKFLOWS.md            # Workflow documentation
└── src/
    └── zettel_agent/
        └── CONCEPT_EXTRACTION_DESIGN.md  # Design document
```

## Contributing to Documentation

When updating documentation:

1. **API Reference:** Update when adding/modifying functions
2. **Architecture:** Update when changing system design
3. **Developer Guide:** Update when adding new patterns or guidelines
4. **Workflows:** Update when modifying workflow logic

## Documentation Standards

- Use clear, concise language
- Include code examples
- Cross-reference related sections
- Keep documentation up-to-date with code
- Use consistent formatting

