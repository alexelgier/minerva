# Error Codes Documentation

## 🚨 Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status_code": 400,
    "context": {
      "field": "additional context information"
    }
  }
}
```

## 📋 Error Code Categories

### 4xx Client Errors

#### VALIDATION_ERROR (400)
**Description**: Request validation failed due to invalid input data.

**Common Causes**:
- Missing required fields
- Invalid data types
- Data format violations
- Constraint violations

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid date format. Expected YYYY-MM-DD",
    "status_code": 400,
    "context": {
      "field": "entry_date",
      "provided_value": "15-01-2024"
    }
  }
}
```

#### RESOURCE_NOT_FOUND (404)
**Description**: The requested resource was not found.

**Common Causes**:
- Invalid workflow ID
- Non-existent journal entry
- Missing entity or relationship
- Invalid endpoint path

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Workflow with identifier 'invalid-uuid' not found",
    "status_code": 404,
    "context": {
      "resource": "Workflow",
      "identifier": "invalid-uuid"
    }
  }
}
```

### 5xx Server Errors

#### SERVICE_UNAVAILABLE (503)
**Description**: An external service is currently unavailable.

**Common Causes**:
- Neo4j database connection failed
- Temporal service unavailable
- Ollama LLM service down
- Network connectivity issues

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Neo4j Database service is currently unavailable",
    "status_code": 503,
    "context": {
      "service": "Neo4j Database",
      "retry_after": "30 seconds"
    }
  }
}
```

#### PROCESSING_ERROR (422)
**Description**: Processing operation failed due to business logic issues.

**Common Causes**:
- LLM processing timeout
- Entity extraction failed
- Relationship extraction failed
- Knowledge graph write failed
- Curation validation failed

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "PROCESSING_ERROR",
    "message": "Failed to extract entities from journal entry",
    "status_code": 422,
    "context": {
      "journal_id": "journal-uuid-123",
      "stage": "ENTITY_PROCESSING",
      "retry_count": 3
    }
  }
}
```

#### INTERNAL_ERROR (500)
**Description**: Unexpected internal server error.

**Common Causes**:
- Unhandled exceptions
- System resource exhaustion
- Configuration errors
- Unexpected system state

**Example**:
```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred",
    "status_code": 500,
    "context": {
      "function": "extract_entities",
      "timestamp": "2024-01-15T10:00:00Z"
    }
  }
}
```

## 🔍 Error Context Fields

### Common Context Fields

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | The field that caused the validation error |
| `provided_value` | any | The value that was provided |
| `expected_format` | string | The expected format or type |
| `resource` | string | The type of resource that was not found |
| `identifier` | string | The identifier that was not found |
| `service` | string | The service that is unavailable |
| `retry_after` | string | Suggested retry time |
| `journal_id` | string | Journal entry identifier |
| `workflow_id` | string | Workflow identifier |
| `stage` | string | Processing stage where error occurred |
| `retry_count` | integer | Number of retry attempts |
| `function` | string | Function where error occurred |
| `timestamp` | string | When the error occurred |

### Pipeline-Specific Context

| Field | Type | Description |
|-------|------|-------------|
| `pipeline_stage` | string | Current pipeline stage |
| `entity_count` | integer | Number of entities processed |
| `relationship_count` | integer | Number of relationships processed |
| `error_count` | integer | Total error count |
| `processing_time` | string | Time spent processing |

### Database-Specific Context

| Field | Type | Description |
|-------|------|-------------|
| `database` | string | Database name (neo4j, curation) |
| `operation` | string | Database operation (read, write, delete) |
| `constraint` | string | Constraint that was violated |
| `query` | string | Database query that failed |

## 🛠️ Error Handling Best Practices

### Client-Side Handling

1. **Check Error Code**: Always check the `error.code` field first
2. **Display User-Friendly Messages**: Use the `error.message` for user display
3. **Log Context**: Log the full error context for debugging
4. **Implement Retry Logic**: For `SERVICE_UNAVAILABLE` errors
5. **Handle Validation Errors**: Show field-specific validation messages

### Example Client Error Handling

```javascript
async function submitJournal(entryData) {
  try {
    const response = await fetch('/api/journal/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entryData)
    });
    
    const result = await response.json();
    
    if (!result.success) {
      switch (result.error.code) {
        case 'VALIDATION_ERROR':
          showValidationError(result.error.message, result.error.context.field);
          break;
        case 'SERVICE_UNAVAILABLE':
          showRetryMessage(result.error.context.retry_after);
          break;
        case 'PROCESSING_ERROR':
          showProcessingError(result.error.message);
          break;
        default:
          showGenericError(result.error.message);
      }
      return;
    }
    
    // Handle success
    showSuccess(result.message);
    
  } catch (error) {
    showGenericError('Network error occurred');
  }
}
```

## 📊 Error Monitoring

### Logging
- All errors are logged with full context
- Error codes are tracked for monitoring
- Performance metrics include error rates

### Metrics to Track
- Error rate by endpoint
- Error rate by error code
- Error rate by processing stage
- Average error resolution time
- Service availability metrics

### Alerting
- High error rates (>5% for any endpoint)
- Service unavailability
- Processing pipeline failures
- Database connection issues

## 🔧 Debugging

### Development Mode
In development mode, error responses include additional debugging information:

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An internal error occurred",
    "status_code": 500,
    "context": {
      "function": "extract_entities",
      "timestamp": "2024-01-15T10:00:00Z"
    },
    "request": {
      "method": "POST",
      "url": "http://localhost:8000/api/journal/submit",
      "path": "/api/journal/submit"
    }
  }
}
```

### Production Mode
In production mode, sensitive information is filtered out:
- Database connection strings
- Internal file paths
- Stack traces
- Personal information

## 🚀 Error Recovery

### Automatic Recovery
- **Retry Logic**: Built into Temporal workflows
- **Circuit Breakers**: Prevent cascading failures
- **Graceful Degradation**: Continue processing when possible

### Manual Recovery
- **Admin Interface**: Manual intervention tools
- **Error Dashboard**: Monitor and resolve errors
- **Data Repair**: Tools to fix corrupted data

## 📝 Error Code Reference

| Code | Status | Description | Retryable |
|------|--------|-------------|-----------|
| `VALIDATION_ERROR` | 400 | Request validation failed | No |
| `RESOURCE_NOT_FOUND` | 404 | Resource not found | No |
| `SERVICE_UNAVAILABLE` | 503 | External service unavailable | Yes |
| `PROCESSING_ERROR` | 422 | Processing operation failed | Yes |
| `INTERNAL_ERROR` | 500 | Unexpected internal error | Yes |
