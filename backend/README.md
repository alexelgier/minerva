# Minerva Backend

A personal knowledge management system that processes journal entries to extract entities and relationships, building a comprehensive knowledge graph.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Poetry
- Neo4j Desktop
- Ollama (for LLM processing)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd Minerva/backend

# Install dependencies
poetry install

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start Neo4j and Ollama
# Then run the application
poetry run python -m minerva_backend.api.main
```

## 🏗️ Architecture

Minerva Backend is built with a clean, modular architecture using dependency injection:

- **FastAPI** - Web framework with automatic API documentation
- **Neo4j** - Graph database for knowledge storage
- **Temporal** - Workflow orchestration for long-running processes
- **Ollama** - Local LLM for entity extraction
- **Dependency Injector** - Inversion of control container

### Key Components

- **API Layer** - RESTful endpoints with dependency injection
- **Processing Pipeline** - Entity extraction and relationship discovery
- **Knowledge Graph** - Neo4j-based graph storage
- **Temporal Workflows** - Asynchronous processing orchestration
- **Obsidian Integration** - Sync with Obsidian vaults

## 📚 Documentation

- [Architecture Overview](docs/architecture/overview.md)
- [Dependency Injection](docs/architecture/dependency-injection.md)
- [API Endpoints](docs/api/endpoints.md)
- [Development Setup](docs/development/onboarding.md)
- [Testing Guide](docs/development/testing.md)

## 🧪 Testing

**Complete Test Isolation**: All 238 unit tests run with complete isolation - no real database connections, LLM calls, or file I/O.

```bash
# Run all tests (238 tests, ~10 seconds)
poetry run pytest

# Run with coverage
poetry run pytest --cov=minerva_backend --cov-report=html

# Run specific test categories
poetry run pytest tests/unit/        # Unit tests (isolated)
poetry run pytest tests/integration/ # Integration tests (real dependencies)

# Run specific test files
poetry run pytest tests/unit/api/test_journal.py -v
```

### Test Features
- ✅ **Complete Isolation**: All external dependencies mocked
- ✅ **No Real I/O**: No database, file, or network calls
- ✅ **Fast Execution**: 238 tests in ~10 seconds
- ✅ **Comprehensive Coverage**: All services and repositories tested

## 🔧 Development

### Code Quality
```bash
# Format code
poetry run black src/
poetry run isort src/

# Lint code
poetry run flake8 src/
poetry run mypy src/
```

### Database Setup
```bash
# Initialize Neo4j with emotion types
poetry run python -c "from minerva_backend.containers import Container; container = Container(); container.db_connection().init_emotion_types()"
```

## 📊 Entity Types

The system extracts and manages these entity types:

- **Person** - People mentioned in journal entries
- **Feeling** - Emotional states and experiences
- **Emotion** - Specific emotions with intensity levels
- **Event** - Activities and occurrences
- **Project** - Ongoing initiatives and goals
- **Content** - Books, articles, videos, etc.
- **Consumable** - Resources being consumed
- **Place** - Locations and places
- **Concept** - Abstract ideas and concepts

## 🔄 Processing Workflow

1. **Journal Entry** - User submits journal entry via API
2. **Entity Extraction** - LLM extracts entities from text
3. **Human Curation** - User reviews and validates entities
4. **Relationship Extraction** - LLM finds relationships between entities
5. **Knowledge Graph Update** - Validated data stored in Neo4j

## 🛡️ Security

- **Local Processing** - LLM runs locally, no external API calls
- **Input Validation** - Pydantic models validate all inputs
- **CORS Configuration** - Restricted to known origins
- **Error Sanitization** - Sensitive data filtered from responses

## 📈 Scalability

- **Temporal Workflows** - Handle long-running processes asynchronously
- **Repository Pattern** - Easy to swap data storage backends
- **Dependency Injection** - Loose coupling enables testing and modification
- **Modular Design** - Components can be scaled independently

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [Contributing Guide](docs/development/onboarding.md) for detailed instructions.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Check the [documentation](docs/)
- Create an [issue](https://github.com/your-repo/issues)
- Contact the development team

## 🎯 Roadmap

- [ ] Enhanced entity extraction algorithms
- [ ] Real-time collaboration features
- [ ] Advanced graph analytics
- [ ] Mobile application support
- [ ] Plugin system for custom extractors

---

Built with ❤️ by the Minerva team
