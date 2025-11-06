# Developer Onboarding Guide

## 🚀 Welcome to Minerva Backend Development

This guide will help you get up and running with the Minerva Backend development environment quickly and efficiently.

## 📋 Prerequisites

### Required Software
- **Python 3.13+** - [Download](https://www.python.org/downloads/)
- **Poetry** - [Installation Guide](https://python-poetry.org/docs/#installation)
- **Git** - [Download](https://git-scm.com/downloads)
- **Neo4j Desktop** - [Download](https://neo4j.com/download/)

### Recommended Software
- **VS Code** - [Download](https://code.visualstudio.com/)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Postman** - [Download](https://www.postman.com/downloads/)

## 🛠️ Quick Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Minerva/backend
```

### 2. Install Dependencies
```bash
# Install Python dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 3. Set Up Neo4j Database
1. Download and install Neo4j Desktop
2. Create a new database
3. Set password to `Alxe342!` (or update config)
4. Start the database

### 4. Set Up Temporal (Optional for Development)
```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Start Temporal server
temporal server start-dev
```

### 5. Configure Environment
Create a `.env` file in the backend directory:
```env
# Database Configuration
MINERVA_NEO4J_URI=bolt://localhost:7687
MINERVA_NEO4J_USER=neo4j
MINERVA_NEO4J_PASSWORD=Alxe342!
MINERVA_CURATION_DB_PATH=curation.db

# Temporal Configuration
MINERVA_TEMPORAL_URI=localhost:7233

# API Configuration
MINERVA_DEBUG=true
MINERVA_LOG_LEVEL=DEBUG
```

### 6. Initialize Database
```bash
# Run database initialization
python -c "from minerva_backend.containers import Container; container = Container(); container.db_connection().init_emotion_types()"
```

### 7. Start the Application
```bash
# Start the FastAPI server
python -m minerva_backend.api.main

# Or use uvicorn directly
uvicorn minerva_backend.api.main:backend_app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Testing Your Setup

### 1. Health Check
```bash
curl http://localhost:8000/api/health
```

### 2. Test Journal Submission
```bash
curl -X POST http://localhost:8000/api/journal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Today I went to the park with John. It was a beautiful day and I felt happy.",
    "date": "2024-01-15"
  }'
```

### 3. Check API Documentation
Visit: http://localhost:8000/docs

## 📁 Project Structure

```
backend/
├── src/
│   └── minerva_backend/
│       ├── api/                 # FastAPI application
│       │   ├── routers/        # API route handlers
│       │   ├── models.py        # Pydantic models
│       │   ├── exceptions.py    # Custom exceptions
│       └── main.py             # FastAPI app initialization
│       ├── graph/              # Knowledge graph (Neo4j)
│       │   ├── models/         # Graph data models
│       │   ├── repositories/   # Data access layer
│       │   └── services/       # Business logic
│       ├── processing/         # Processing pipeline
│       │   ├── extraction/     # Entity extraction
│       │   ├── llm_service.py  # LLM integration
│       │   └── temporal_orchestrator.py  # Workflow orchestration
│       ├── obsidian/           # Obsidian integration
│       ├── prompt/             # LLM prompts
│       ├── utils/              # Utilities
│       ├── config.py           # Configuration
│       └── containers.py       # Dependency injection
├── tests/                      # Test files
├── docs/                       # Documentation
├── pyproject.toml             # Dependencies
└── .env                        # Environment variables
```

## 🔧 Development Workflow

### 1. Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `poetry run pytest`
4. Format code: `poetry run black src/ && poetry run isort src/`
5. Commit changes: `git commit -m "Add your feature"`

### 2. Testing Changes
1. Start the application
2. Test via API endpoints
3. Check logs for errors
4. Verify database changes

### 3. Debugging
1. Enable debug mode in `.env`
2. Check logs in `logs/` directory
3. Use Neo4j Browser for database inspection
4. Use Temporal Web UI for workflow monitoring

## 🧪 Running Tests

### Run All Tests
```bash
poetry run pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
poetry run pytest tests/unit/

# Integration tests only
poetry run pytest tests/integration/

# API tests only
poetry run pytest -m api

# With coverage
poetry run pytest --cov=minerva_backend --cov-report=html
```

### Test Configuration
- Tests use mocked dependencies by default
- Integration tests require running services
- Use `--slow` marker for long-running tests

## 📊 Monitoring and Logging

### Log Files
- **Application logs**: `logs/minerva.log`
- **Error logs**: `logs/minerva_errors.log`
- **Performance logs**: `logs/minerva_performance.log`

### Log Levels
- **DEBUG**: Detailed information for debugging
- **INFO**: General information about system operation
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failed operations
- **CRITICAL**: Critical errors that may cause system failure

### Performance Monitoring
- Processing time for entity extraction
- LLM request duration
- Database operation timing
- Memory usage tracking

## 🐛 Common Issues and Solutions

### Issue: Neo4j Connection Failed
**Error**: `ServiceUnavailableError: Neo4j Database service is currently unavailable`

**Solutions**:
1. Check if Neo4j is running: `curl http://localhost:7474`
2. Verify credentials in `.env` file
3. Check firewall settings
4. Ensure Neo4j is listening on port 7687

### Issue: Temporal Connection Failed
**Error**: `ConnectionError: Failed to connect to Temporal`

**Solutions**:
1. Check if Temporal is running: `temporal workflow list`
2. Verify TEMPORAL_URI in `.env` file
3. Ensure Temporal is listening on port 7233

### Issue: LLM Service Unavailable
**Error**: `ServiceUnavailableError: LLM service is currently unavailable`

**Solutions**:
1. Install Ollama: https://ollama.ai/
2. Start Ollama service: `ollama serve`
3. Pull a model: `ollama pull llama2`

### Issue: Import Errors
**Error**: `ModuleNotFoundError: No module named 'minerva_backend'`

**Solutions**:
1. Ensure you're in the virtual environment: `poetry shell`
2. Reinstall dependencies: `poetry install`
3. Check Python path: `which python`

### Issue: Database Initialization Failed
**Error**: `DatabaseError: Failed to initialize emotion types`

**Solutions**:
1. Check Neo4j connection
2. Verify database permissions
3. Run initialization manually:
   ```python
   from minerva_backend.containers import Container
   container = Container()
   container.db_connection().init_emotion_types()
   ```

## 🔄 Code Quality

### Formatting
```bash
# Format code with black
poetry run black src/

# Sort imports with isort
poetry run isort src/

# Check formatting
poetry run black --check src/
poetry run isort --check-only src/
```

### Linting
```bash
# Run linting
poetry run flake8 src/

# Run type checking
poetry run mypy src/
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=minerva_backend --cov-report=html

# Run specific tests
poetry run pytest tests/unit/api/test_journal.py
```

## 📚 Learning Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Neo4j
- [Neo4j Documentation](https://neo4j.com/docs/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)

### Temporal
- [Temporal Documentation](https://docs.temporal.io/)
- [Temporal Python SDK](https://docs.temporal.io/application-development/foundations/install-temporal)

### Poetry
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Poetry Tutorial](https://python-poetry.org/docs/basic-usage/)

## 🤝 Contributing

### 1. Code Style
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings
- Add tests for new features

### 2. Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commit format
- Reference issues when applicable

### 3. Pull Requests
- Create feature branches from `main`
- Include tests for new functionality
- Update documentation as needed
- Request review from team members

## 📞 Getting Help

### Documentation
- Check this onboarding guide
- Review API documentation at `/docs`
- Read architecture documentation in `docs/architecture/`

### Support
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

### Community
- Join the development team chat
- Attend team meetings
- Participate in code reviews

## 🎯 Next Steps

1. **Explore the Codebase**: Start with `src/minerva_backend/api/main.py`
2. **Run Tests**: Ensure all tests pass
3. **Make a Small Change**: Try adding a new endpoint
4. **Read Documentation**: Review architecture and API docs
5. **Join the Team**: Participate in discussions and reviews

Welcome to the Minerva Backend development team! 🚀
