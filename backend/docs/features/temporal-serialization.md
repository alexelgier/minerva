# Temporal Serialization System

## Overview

The Minerva backend uses a custom Temporal data converter to ensure proper serialization and deserialization of complex objects (`EntityMapping` and `RelationSpanContextMapping`) across Temporal workflow boundaries. This system prevents type loss and ensures that domain entities maintain their proper structure throughout the processing pipeline.

## Problem Solved

### Original Issue
- **Error**: `'dict' object has no attribute 'uuid'` in Temporal workflows
- **Root Cause**: Temporal's default serialization converted `EntityMapping` objects to plain dictionaries
- **Impact**: Curation pipeline failed when trying to access `entity.uuid` on deserialized objects

### Solution
- **Custom Data Converter**: Implemented specialized payload converters for complex objects
- **Type Preservation**: Ensures domain entities maintain their proper types through serialization
- **Fail-Fast Design**: Raises clear errors instead of silent failures

## Architecture

### Custom Payload Converters

#### EntityMappingPayloadConverter
Handles serialization/deserialization of `EntityMapping` objects:

```python
class EntityMappingPayloadConverter(EncodingPayloadConverter):
    def to_payload(self, value: Any) -> Optional[Payload]:
        # Serializes EntityMapping with type information preserved
    
    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        # Deserializes using ENTITY_TYPE_MAP and entity.type field
```

#### RelationSpanContextMappingPayloadConverter
Handles serialization/deserialization of `RelationSpanContextMapping` objects:

```python
class RelationSpanContextMappingPayloadConverter(EncodingPayloadConverter):
    def to_payload(self, value: Any) -> Optional[Payload]:
        # Serializes RelationSpanContextMapping with type information preserved
    
    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        # Deserializes using relation.type field for proper type reconstruction
```

#### ListEntityMappingPayloadConverter
Handles serialization/deserialization of `List[EntityMapping]` objects:

```python
class ListEntityMappingPayloadConverter(EncodingPayloadConverter):
    def to_payload(self, value: Any) -> Optional[Payload]:
        # Serializes list of EntityMapping objects using individual converter logic
    
    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        # Deserializes list using EntityMappingPayloadConverter for each item
```

#### ListRelationSpanContextMappingPayloadConverter
Handles serialization/deserialization of `List[RelationSpanContextMapping]` objects:

```python
class ListRelationSpanContextMappingPayloadConverter(EncodingPayloadConverter):
    def to_payload(self, value: Any) -> Optional[Payload]:
        # Serializes list of RelationSpanContextMapping objects using individual converter logic
    
    def from_payload(self, payload: Payload, type_hint: Optional[Type] = None) -> Any:
        # Deserializes list using RelationSpanContextMappingPayloadConverter for each item
```

### Type Reconstruction Strategy

#### Entity Types
- **Uses Existing Infrastructure**: Leverages `ENTITY_TYPE_MAP` from `curation_manager.py`
- **Type Field**: Uses `entity.type` field to determine correct domain entity class
- **Supported Types**: Person, Concept, Feeling, Event, Project, Content, Consumable, Place

#### Relation Types
- **Type Field**: Uses `relation.type` field to determine correct relation class
- **Supported Types**: `Relation` and `ConceptRelation` based on type value
- **Context Handling**: Properly deserializes `RelationshipContext` objects

#### Span Types
- **Type Correction**: Ensures `Span` objects have correct `LexicalType.SPAN` value
- **Field Validation**: Validates all required span fields during deserialization

## Implementation Details

### Serialization Process
1. **Object Detection**: Identifies `EntityMapping` or `RelationSpanContextMapping` objects
2. **Type Preservation**: Extracts type information from existing fields
3. **JSON Conversion**: Converts to JSON with custom `DateTimeEncoder` for datetime handling
4. **Payload Creation**: Creates Temporal `Payload` with custom encoding metadata

### Deserialization Process
1. **Encoding Check**: Verifies custom encoding in payload metadata
2. **JSON Parsing**: Converts binary payload back to JSON
3. **Type Lookup**: Uses type fields to determine correct class from type maps
4. **Object Reconstruction**: Creates proper domain objects with all fields

### Error Handling
- **Missing Type Fields**: Raises `RuntimeError` with clear error message
- **Unknown Types**: Raises `RuntimeError` for unsupported entity/relation types
- **Validation Errors**: Pydantic validation errors are propagated with context
- **Serialization Errors**: JSON encoding errors are caught and re-raised with context

## Usage

### Integration with Temporal
The custom data converter is automatically used by the Temporal orchestrator:

```python
# temporal_orchestrator.py
from minerva_backend.processing.temporal_converter import create_custom_data_converter

# Client initialization
client = await Client.connect(
    temporal_uri, 
    data_converter=create_custom_data_converter()
)

# Worker initialization
client = await Client.connect(
    settings.TEMPORAL_URI, 
    data_converter=create_custom_data_converter()
)
```

### Converter Ordering
The custom data converter uses a specific order to ensure proper type matching:

```python
payload_converter = CompositePayloadConverter(
    ListEntityMappingPayloadConverter(),           # List converters first
    ListRelationSpanContextMappingPayloadConverter(),
    EntityMappingPayloadConverter(),               # Individual converters second
    RelationSpanContextMappingPayloadConverter(),
    *pydantic_data_converter.payload_converter.converters.values(),  # Pydantic third
    *DefaultPayloadConverter.default_encoding_payload_converters,    # Defaults last
)
```

**Why This Order Matters:**
- **List Converters First**: Ensures `List[EntityMapping]` matches before individual `EntityMapping`
- **Individual Converters Second**: Handles single objects after lists are ruled out
- **Pydantic Third**: Handles other Pydantic models
- **Defaults Last**: Fallback for basic types

### Data Flow
```
EntityMapping/RelationSpanContextMapping (or List[...])
    ↓ (Custom Payload Converter - List or Individual)
JSON with Type Information
    ↓ (Temporal Serialization)
Binary Payload
    ↓ (Temporal Deserialization)
JSON with Type Information
    ↓ (Custom Payload Converter - List or Individual)
Proper Domain Objects (or List[...])
```

## Testing

### Unit Tests
Comprehensive test coverage in `test_temporal_converter.py`:

- **Serialization Tests**: Verify objects are properly converted to JSON
- **Deserialization Tests**: Verify objects are properly reconstructed
- **Type Safety Tests**: Verify correct domain entity types are created
- **Error Handling Tests**: Verify proper error messages for invalid data
- **Edge Case Tests**: Verify handling of missing fields and unknown types

### Test Coverage
- **EntityMapping**: Person, Concept, and other entity types
- **RelationSpanContextMapping**: Relation and ConceptRelation types
- **List Serialization**: `List[EntityMapping]` and `List[RelationSpanContextMapping]` round-trips
- **Empty Lists**: Proper handling of empty list serialization
- **Mixed Lists**: Fallback behavior for non-homogeneous lists
- **Error Scenarios**: Missing type fields, unknown types, validation errors
- **Integration**: Custom data converter creation and usage

## Benefits

### Type Safety
- **Guaranteed Types**: All objects maintain their expected types throughout the pipeline
- **No Runtime Errors**: Eliminates `AttributeError` when accessing object properties
- **IDE Support**: Full autocomplete and type checking support

### Reliability
- **Fail-Fast Design**: Configuration errors are caught immediately
- **Clear Error Messages**: Detailed error messages for debugging
- **No Silent Failures**: All errors are properly propagated

### Maintainability
- **Existing Infrastructure**: Uses existing type maps and type fields
- **Minimal Changes**: Only requires updating Temporal client/worker configuration
- **Backward Compatible**: Works with existing Pydantic data converter for other types

## Configuration

### Required Changes
1. **Import Update**: Replace `pydantic_data_converter` import with `create_custom_data_converter`
2. **Client Configuration**: Use custom data converter in client initialization
3. **Worker Configuration**: Use custom data converter in worker initialization

### No Breaking Changes
- **Existing Code**: All existing functionality continues to work
- **Test Suite**: All 359 tests continue to pass
- **API Compatibility**: No changes to public APIs

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `temporal_converter.py` is properly imported
2. **Type Errors**: Verify `ENTITY_TYPE_MAP` includes all required entity types
3. **Serialization Errors**: Check that all datetime objects are properly handled

### Debugging
- **Enable Logging**: Add logging to payload converters for debugging
- **Test Serialization**: Use unit tests to verify serialization/deserialization
- **Check Types**: Verify that deserialized objects have correct types

## Future Enhancements

### Potential Improvements
1. **Performance**: Optimize serialization for large objects
2. **Caching**: Add caching for frequently serialized objects
3. **Compression**: Add compression for large payloads
4. **Versioning**: Add version support for schema changes

### Monitoring
1. **Metrics**: Track serialization/deserialization performance
2. **Errors**: Monitor error rates and types
3. **Types**: Track which entity/relation types are most common
