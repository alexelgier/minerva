# Decision Trees for Common Tasks

## 🚀 Quick Decision Trees

### "How do I add a new entity type?"

```
Is it a domain entity?
├── Yes
│   ├── Does it need special processing?
│   │   ├── Yes → Create processor in processing/extraction/processors/
│   │   └── No → Use base entity processor
│   ├── Does it need relationships?
│   │   ├── Yes → Add to relationship extraction
│   │   └── No → Skip relationship processing
│   ├── Does it need vector search?
│   │   ├── Yes → Add to vector indexes
│   │   └── No → Skip vector search setup
│   └── Documentation → Update database-schema.md and processing-pipeline.md
└── No → Use existing generic entity types
```

**Files to modify**:
- `src/minerva_backend/graph/models/entities.py` - Add entity model
- `src/minerva_backend/graph/repositories/` - Add repository
- `src/minerva_backend/processing/extraction/processors/` - Add processor (if needed)
- `backend/docs/architecture/database-schema.md` - Update schema docs

### "How do I debug a processing issue?"

```
Check logs first
├── Found error in logs?
│   ├── Yes → Check error type
│   │   ├── Service unavailable → Check service status
│   │   ├── Processing error → Check LLM service
│   │   ├── Database error → Check Neo4j connection
│   │   └── Validation error → Check input data
│   └── No → Check system health
│       ├── All services running? → Check configuration
│       └── Some services down? → Restart services
└── No errors in logs?
    ├── Check API health endpoints
    ├── Check service connectivity
    └── Check resource usage (CPU, memory)
```

**Quick checks**:
- `curl http://localhost:8000/api/health`
- `curl http://localhost:7474` (Neo4j)
- `curl http://localhost:11434` (Ollama)
- `temporal workflow list` (Temporal)

### "How do I understand the system architecture?"

```
Start with high-level overview
├── Read architecture/overview.md
├── Understand data flow
│   ├── Read processing-pipeline.md
│   ├── Check database-schema.md
│   └── Review dependency-injection.md
├── Explore specific components
│   ├── API layer → api/endpoints.md
│   ├── Processing → features/concept-extraction.md
│   └── Database → architecture/database-schema.md
└── Check implementation details
    ├── Source code structure
    ├── Configuration files
    └── Test files
```

### "How do I set up the development environment?"

```
Choose your OS
├── Windows
│   ├── Install Python 3.13+
│   ├── Install Poetry
│   ├── Install Neo4j Desktop
│   ├── Install Temporal CLI
│   └── Install Ollama
├── macOS
│   ├── Install Python 3.13+ (brew install python@3.13)
│   ├── Install Poetry (curl -sSL https://install.python-poetry.org | python3 -)
│   ├── Install Neo4j Desktop
│   ├── Install Temporal CLI
│   └── Install Ollama (brew install ollama)
└── Linux
    ├── Install Python 3.13+ (sudo apt install python3.13)
    ├── Install Poetry (curl -sSL https://install.python-poetry.org | python3 -)
    ├── Install Neo4j (Docker or manual)
    ├── Install Temporal CLI
    └── Install Ollama (curl -fsSL https://ollama.ai/install.sh | sh)

Then:
├── Clone repository
├── Install dependencies (poetry install)
├── Configure environment (.env file)
├── Start services (Neo4j, Temporal, Ollama)
├── Initialize database
└── Start application
```

### "How do I test my changes?"

```
What type of change?
├── New feature
│   ├── Write unit tests
│   ├── Write integration tests
│   ├── Update existing tests
│   └── Run full test suite
├── Bug fix
│   ├── Write test for bug
│   ├── Fix the bug
│   ├── Verify test passes
│   └── Run regression tests
├── Refactoring
│   ├── Run existing tests
│   ├── Ensure no behavior change
│   └── Update tests if needed
└── Documentation
    ├── Verify examples work
    ├── Check links and references
    └── Test code snippets
```

**Test commands**:
- `poetry run pytest` - Run all tests
- `poetry run pytest tests/unit/` - Unit tests only
- `poetry run pytest tests/integration/` - Integration tests only
- `poetry run pytest --cov=minerva_backend --cov-report=html` - With coverage

### "How do I handle API errors?"

```
Check error response
├── success: false?
│   ├── Yes → Check error.code
│   │   ├── VALIDATION_ERROR → Check input data
│   │   ├── RESOURCE_NOT_FOUND → Check resource exists
│   │   ├── SERVICE_UNAVAILABLE → Check service status
│   │   ├── PROCESSING_ERROR → Check processing logs
│   │   └── INTERNAL_ERROR → Check application logs
│   └── No → Check HTTP status code
│       ├── 200-299 → Success (check response data)
│       ├── 400-499 → Client error (check request)
│       └── 500-599 → Server error (check logs)
└── No → Check network connectivity
```

**Error handling**:
- Check [Error Codes](api/error-codes.md) for details
- Use error.context for additional information
- Implement retry logic for SERVICE_UNAVAILABLE errors

### "How do I optimize performance?"

```
Identify bottleneck
├── Slow API responses?
│   ├── Check database queries
│   ├── Check service health
│   ├── Check network latency
│   └── Check resource usage
├── Slow processing?
│   ├── Check LLM service performance
│   ├── Check database performance
│   ├── Check memory usage
│   └── Check processing logs
├── High memory usage?
│   ├── Check for memory leaks
│   ├── Restart services
│   ├── Check batch sizes
│   └── Monitor resource usage
└── Database slow?
    ├── Check indexes
    ├── Check query performance
    ├── Check connection pool
    └── Check database size
```

**Performance tools**:
- `htop` - Monitor system resources
- Neo4j Browser - Check query performance
- `tail -f logs/minerva_performance.log` - Check performance logs

### "How do I deploy to production?"

```
Prepare for production
├── Update configuration
│   ├── Set production environment variables
│   ├── Configure proper logging
│   ├── Set up monitoring
│   └── Configure security settings
├── Database setup
│   ├── Set up production Neo4j
│   ├── Configure backups
│   ├── Set up monitoring
│   └── Test connectivity
├── Service setup
│   ├── Set up production Temporal
│   ├── Set up production LLM service
│   ├── Configure load balancing
│   └── Set up health checks
└── Application deployment
    ├── Build application
    ├── Deploy to production server
    ├── Run database migrations
    └── Start services
```

### "How do I add a new API endpoint?"

```
Plan the endpoint
├── What does it do?
├── What data does it need?
├── What does it return?
└── What errors can occur?

Implement the endpoint
├── Add to appropriate router
├── Define request/response models
├── Implement business logic
├── Add error handling
└── Add documentation

Test the endpoint
├── Write unit tests
├── Write integration tests
├── Test error cases
└── Update API documentation
```

**Files to modify**:
- `src/minerva_backend/api/routers/` - Add endpoint
- `src/minerva_backend/api/models.py` - Add models
- `tests/unit/api/` - Add tests
- `docs/api/endpoints.md` - Update documentation

### "How do I add a new feature?"

```
Plan the feature
├── What problem does it solve?
├── How does it fit into existing architecture?
├── What components need to be modified?
└── What are the dependencies?

Implement the feature
├── Create/update models
├── Implement business logic
├── Add API endpoints (if needed)
├── Add processing logic (if needed)
├── Update database schema (if needed)
└── Add configuration (if needed)

Test the feature
├── Write unit tests
├── Write integration tests
├── Test error cases
├── Test performance
└── Update documentation
```

### "How do I troubleshoot a specific error?"

```
Get error details
├── Check error message
├── Check error code
├── Check error context
└── Check logs

Identify the cause
├── Service unavailable?
│   ├── Check service status
│   ├── Check connectivity
│   └── Restart service
├── Configuration error?
│   ├── Check environment variables
│   ├── Check configuration files
│   └── Validate settings
├── Data error?
│   ├── Check input data
│   ├── Check database state
│   └── Validate data format
└── Code error?
    ├── Check code logic
    ├── Check dependencies
    └── Review recent changes
```

## 🎯 Quick Reference Commands

### Service Management
```bash
# Check service status
curl http://localhost:8000/api/health
curl http://localhost:7474
curl http://localhost:11434
temporal workflow list

# Start services
temporal server start-dev
ollama serve
# Neo4j: Use Neo4j Desktop or Docker

# Stop services
pkill -f "temporal"
pkill -f "ollama serve"
```

### Development
```bash
# Run tests
poetry run pytest
poetry run pytest tests/unit/
poetry run pytest --cov=minerva_backend --cov-report=html

# Start application
poetry shell
python -m minerva_backend.api.main

# Check logs
tail -f logs/minerva.log
tail -f logs/minerva_errors.log
```

### Database
```bash
# Initialize database
python -c "from minerva_backend.containers import Container; container = Container(); container.db_connection().init_emotion_types()"

# Check database
# In Neo4j Browser: http://localhost:7474
MATCH (n) RETURN count(n) as total_nodes
```

---

*These decision trees provide step-by-step guidance for common tasks. Use them as a starting point and refer to detailed documentation for specific implementation details.*
