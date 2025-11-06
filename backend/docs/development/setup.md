# Development Setup Guide

## 🏗️ Complete Development Environment Setup

This guide provides detailed instructions for setting up a complete Minerva Backend development environment from scratch.

## 📋 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS 10.15+, or Ubuntu 18.04+
- **RAM**: 8GB (16GB recommended)
- **Storage**: 10GB free space
- **CPU**: 4 cores (8 cores recommended)

### Required Software Versions
- **Python**: 3.13 or higher
- **Poetry**: 1.4.0 or higher
- **Git**: 2.30 or higher
- **Neo4j**: 5.0 or higher
- **Temporal**: 1.17 or higher

## 🚀 Step-by-Step Setup

### Step 1: Install Python and Poetry

#### Windows
```powershell
# Install Python from Microsoft Store or python.org
# Verify installation
python --version

# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Add Poetry to PATH
$env:PATH += ";$env:APPDATA\Python\Scripts"
```

#### macOS
```bash
# Install Python (if not already installed)
brew install python@3.13

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

#### Ubuntu/Debian
```bash
# Install Python
sudo apt update
sudo apt install python3.13 python3.13-venv python3-pip

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 2: Install Neo4j

#### Option A: Neo4j Desktop (Recommended)
1. Download from [neo4j.com/download](https://neo4j.com/download/)
2. Install and launch Neo4j Desktop
3. Create a new project
4. Create a new database:
   - **Name**: `minerva-dev`
   - **Password**: `Alxe342!`
   - **Version**: 5.0 or higher
5. Start the database

#### Option B: Docker
```bash
# Pull Neo4j image
docker pull neo4j:5.0

# Run Neo4j container
docker run \
  --name neo4j-minerva \
  -p 7474:7474 -p 7687:7687 \
  -d \
  -v $HOME/neo4j/data:/data \
  -v $HOME/neo4j/logs:/logs \
  -v $HOME/neo4j/import:/var/lib/neo4j/import \
  -v $HOME/neo4j/plugins:/plugins \
  --env NEO4J_AUTH=neo4j/Alxe342! \
  neo4j:5.0
```

#### Option C: Manual Installation
1. Download Neo4j from [neo4j.com/download](https://neo4j.com/download/)
2. Extract to desired location
3. Configure `conf/neo4j.conf`:
   ```properties
   dbms.default_database=minerva
   dbms.security.auth_enabled=true
   dbms.default_listen_address=0.0.0.0
   ```
4. Start Neo4j: `./bin/neo4j start`

### Step 3: Install Temporal

#### Option A: Temporal CLI (Recommended)
```bash
# Install Temporal CLI
curl -sSf https://temporal.download/cli.sh | sh

# Start Temporal server
temporal server start-dev
```

#### Option B: Docker Compose
```yaml
# docker-compose.temporal.yml
version: '3.8'
services:
  temporal:
    image: temporalio/auto-setup:1.17.0
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
      - DYNAMIC_CONFIG_FILE_PATH=config/dynamicconfig/development-sql.yaml
    depends_on:
      - postgresql
  postgresql:
    image: postgres:13
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=temporal
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal
```

```bash
# Start Temporal with Docker
docker-compose -f docker-compose.temporal.yml up -d
```

### Step 4: Install Ollama (LLM Service)

#### Windows
```powershell
# Download from https://ollama.ai/download
# Or use winget
winget install Ollama.Ollama
```

#### macOS
```bash
# Install with Homebrew
brew install ollama

# Or download from https://ollama.ai/download
```

#### Ubuntu/Debian
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh
```

#### Start Ollama Service
```bash
# Start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
```

### Step 5: Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd Minerva/backend

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Verify installation
python -c "import minerva_backend; print('Installation successful!')"
```

### Step 6: Configure Environment

Create `.env` file in the backend directory:

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
MINERVA_HOST=0.0.0.0
MINERVA_PORT=8000

# CORS Configuration
MINERVA_CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
MINERVA_CORS_ALLOW_CREDENTIALS=true
MINERVA_CORS_ALLOW_METHODS=["*"]
MINERVA_CORS_ALLOW_HEADERS=["*"]

# Processing Configuration
MINERVA_DEFAULT_PROCESSING_START=06:00
MINERVA_DEFAULT_PROCESSING_END=12:00
MINERVA_MAX_STATUS_POLL_ATTEMPTS=10
MINERVA_STATUS_POLL_INTERVAL=0.2

# Logging Configuration
MINERVA_LOG_LEVEL=INFO
MINERVA_LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Step 7: Initialize Database

```bash
# Initialize emotion types
python -c "
from minerva_backend.containers import Container
container = Container()
container.db_connection().init_emotion_types()
print('Database initialized successfully!')
"
```

### Step 8: Start the Application

```bash
# Start FastAPI server
python -m minerva_backend.api.main

# Or use uvicorn directly
uvicorn minerva_backend.api.main:backend_app --reload --host 0.0.0.0 --port 8000
```

## 🧪 Verify Installation

### 1. Check Health Endpoint
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "0.1.0",
  "services": {
    "database": "healthy",
    "temporal": "healthy",
    "llm": "healthy"
  }
}
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

### 4. Run Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=minerva_backend --cov-report=html
```

## 🔧 Development Tools Setup

### VS Code Extensions
Install these recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml",
    "ms-vscode.vscode-markdown",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode"
  ]
}
```

### Git Hooks
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

### Code Quality Tools
```bash
# Install additional tools
poetry add --group dev black isort flake8 mypy pytest-cov pre-commit

# Configure tools
poetry run black --config pyproject.toml src/
poetry run isort --config pyproject.toml src/
poetry run flake8 src/
poetry run mypy src/
```

## 🐳 Docker Development Environment

### Option 1: Full Docker Setup
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  neo4j:
    image: neo4j:5.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/Alxe342!
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs

  temporal:
    image: temporalio/auto-setup:1.17.0
    ports:
      - "7233:7233"
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=temporal
      - POSTGRES_PWD=temporal
      - POSTGRES_SEEDS=postgresql
    depends_on:
      - postgresql

  postgresql:
    image: postgres:13
    environment:
      - POSTGRES_DB=temporal
      - POSTGRES_USER=temporal
      - POSTGRES_PASSWORD=temporal

  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

  minerva-backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=Alxe342!
      - TEMPORAL_URI=temporal:7233
    depends_on:
      - neo4j
      - temporal
      - ollama
    volumes:
      - .:/app
    command: uvicorn minerva_backend.api.main:backend_app --host 0.0.0.0 --port 8000 --reload

volumes:
  neo4j_data:
  neo4j_logs:
  ollama_data:
```

### Option 2: Hybrid Setup
```bash
# Start only infrastructure services
docker-compose -f docker-compose.dev.yml up neo4j temporal postgresql ollama -d

# Run application locally
poetry shell
python -m minerva_backend.api.main
```

## 🔍 Troubleshooting

### Common Issues

#### Issue: Poetry Installation Failed
**Error**: `Poetry installation failed`

**Solutions**:
1. Check Python version: `python --version`
2. Reinstall Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
3. Add to PATH: `export PATH="$HOME/.local/bin:$PATH"`

#### Issue: Neo4j Connection Failed
**Error**: `ServiceUnavailableError: Neo4j Database service is currently unavailable`

**Solutions**:
1. Check Neo4j status: `curl http://localhost:7474`
2. Verify credentials in `.env`
3. Check firewall settings
4. Restart Neo4j service

#### Issue: Temporal Connection Failed
**Error**: `ConnectionError: Failed to connect to Temporal`

**Solutions**:
1. Check Temporal status: `temporal workflow list`
2. Verify TEMPORAL_URI in `.env`
3. Restart Temporal: `temporal server start-dev`

#### Issue: Ollama Model Not Found
**Error**: `Model not found`

**Solutions**:
1. Check Ollama status: `curl http://localhost:11434`
2. Pull model: `ollama pull llama2`
3. List models: `ollama list`

#### Issue: Import Errors
**Error**: `ModuleNotFoundError: No module named 'minerva_backend'`

**Solutions**:
1. Activate virtual environment: `poetry shell`
2. Reinstall dependencies: `poetry install`
3. Check Python path: `which python`

### Performance Optimization

#### Memory Usage
```bash
# Monitor memory usage
htop
# Or on Windows
tasklist /fi "imagename eq python.exe"
```

#### Database Performance
```cypher
// Check Neo4j performance
CALL db.stats.retrieve('GRAPH COUNTS');
CALL db.stats.retrieve('QUERIES');
```

#### Log Analysis
```bash
# Monitor logs
tail -f logs/minerva.log
tail -f logs/minerva_errors.log
tail -f logs/minerva_performance.log
```

## 📚 Additional Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [Temporal Python SDK](https://docs.temporal.io/application-development/foundations/install-temporal)
- [Poetry Documentation](https://python-poetry.org/docs/)

### Community
- [FastAPI Discord](https://discord.gg/9Z9BqmpH6A)
- [Neo4j Community](https://community.neo4j.com/)
- [Temporal Slack](https://temporal.io/slack)

### Learning
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [Neo4j Graph Academy](https://graphacademy.neo4j.com/)
- [Temporal Learn](https://learn.temporal.io/)

## 🎯 Next Steps

1. **Complete Setup**: Follow all steps above
2. **Run Tests**: Ensure all tests pass
3. **Explore Codebase**: Start with `src/minerva_backend/api/main.py`
4. **Make Changes**: Try adding a new endpoint
5. **Join Development**: Participate in team discussions

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**: Review error logs in `logs/` directory
2. **Verify Services**: Ensure all services are running
3. **Check Configuration**: Verify `.env` file settings
4. **Search Issues**: Look for similar problems in the repository
5. **Ask for Help**: Contact the development team

Welcome to Minerva Backend development! 🚀