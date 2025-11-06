# Troubleshooting Guide

## 🚨 Quick Problem Solver

### "My system won't start"
1. **Check services** → [Service Issues](#service-issues)
2. **Check configuration** → [Configuration Issues](#configuration-issues)
3. **Check logs** → [Log Analysis](#log-analysis)

### "I'm getting errors"
1. **API errors** → [API Error Codes](api/error-codes.md)
2. **Processing errors** → [Processing Issues](#processing-issues)
3. **Database errors** → [Database Issues](#database-issues)

### "Something is slow"
1. **Check performance** → [Performance Issues](#performance-issues)
2. **Check resources** → [Resource Issues](#resource-issues)
3. **Check configuration** → [Configuration Issues](#configuration-issues)

## 🔧 Service Issues

### Neo4j Connection Issues

**Error**: `ServiceUnavailableError: Neo4j Database service is currently unavailable`

**Quick Fix**:
```bash
# Check if Neo4j is running
curl http://localhost:7474

# If not running, start Neo4j
# Option 1: Neo4j Desktop
# - Open Neo4j Desktop
# - Start your database

# Option 2: Docker
docker run --name neo4j-minerva -p 7474:7474 -p 7687:7687 -d -v $HOME/neo4j/data:/data -v $HOME/neo4j/logs:/logs -v $HOME/neo4j/import:/var/lib/neo4j/import -v $HOME/neo4j/plugins:/plugins --env NEO4J_AUTH=neo4j/Alxe342! neo4j:5.0
```

**Verify Connection**:
```bash
# Test connection
curl -u neo4j:Alxe342! http://localhost:7474/db/data/
```

**Common Causes**:
- Neo4j not started
- Wrong credentials in `.env`
- Firewall blocking port 7687
- Neo4j running on different port

### Temporal Connection Issues

**Error**: `ConnectionError: Failed to connect to Temporal`

**Quick Fix**:
```bash
# Check if Temporal is running
temporal workflow list

# If not running, start Temporal
# Option 1: Temporal CLI
temporal server start-dev

# Option 2: Docker
docker run -p 7233:7233 temporalio/auto-setup:1.17.0
```

**Verify Connection**:
```bash
# Test connection
temporal workflow list
```

**Common Causes**:
- Temporal not started
- Wrong URI in `.env`
- Firewall blocking port 7233
- Temporal running on different port

### LLM Service Issues

**Error**: `ServiceUnavailableError: LLM service is currently unavailable`

**Quick Fix**:
```bash
# Check if Ollama is running
curl http://localhost:11434

# If not running, start Ollama
ollama serve

# Pull a model (in another terminal)
ollama pull llama2
```

**Verify Connection**:
```bash
# Test connection
curl http://localhost:11434/api/tags
```

**Common Causes**:
- Ollama not started
- No models downloaded
- Wrong URL in configuration
- Firewall blocking port 11434

## 🗄️ Database Issues

### Database Initialization Failed

**Error**: `DatabaseError: Failed to initialize emotion types`

**Quick Fix**:
```bash
# Check Neo4j connection first
curl -u neo4j:Alxe342! http://localhost:7474/db/data/

# Run initialization manually
python -c "
from minerva_backend.containers import Container
container = Container()
container.db_connection().init_emotion_types()
print('Database initialized successfully!')
"
```

**Common Causes**:
- Neo4j not running
- Wrong credentials
- Database permissions
- Network connectivity

### Database Query Issues

**Error**: `Neo4jError: Database query failed`

**Debug Steps**:
1. **Check query syntax** in Neo4j Browser (http://localhost:7474)
2. **Verify data exists** with simple queries
3. **Check indexes** are created
4. **Review logs** for specific error details

**Common Queries for Debugging**:
```cypher
// Check if data exists
MATCH (n) RETURN count(n) as total_nodes

// Check specific entity type
MATCH (n:Person) RETURN count(n) as person_count

// Check relationships
MATCH ()-[r]->() RETURN count(r) as total_relationships
```

## ⚙️ Processing Issues

### Entity Extraction Failing

**Error**: `ProcessingError: Failed to extract entities from journal entry`

**Debug Steps**:
1. **Check LLM service** is running
2. **Verify journal text** is not empty
3. **Check processing logs** for specific errors
4. **Test with simple text** first

**Quick Test**:
```bash
# Test with simple journal entry
curl -X POST http://localhost:8000/api/journal/submit \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Today I went to the park with John.",
    "date": "2024-01-15"
  }'
```

**Common Causes**:
- LLM service unavailable
- Empty or invalid journal text
- Processing timeout
- Memory issues

### Relationship Extraction Failing

**Error**: `ProcessingError: Failed to extract relationships`

**Debug Steps**:
1. **Check if entities exist** first
2. **Verify entity types** are correct
3. **Check relationship processor** configuration
4. **Review processing logs**

**Common Causes**:
- No entities to relate
- Invalid entity types
- LLM service issues
- Processing timeout

### Temporal Serialization Issues

**Error**: `'dict' object has no attribute 'uuid'`

**Quick Fix**:
This is usually resolved by the custom Temporal data converter. Check:
1. **Custom data converter** is properly configured
2. **Entity types** are properly mapped
3. **Temporal client** is using the custom converter

**Verify Fix**:
```python
# Check if custom data converter is being used
from minerva_backend.processing.temporal_converter import create_custom_data_converter
converter = create_custom_data_converter()
```

## 🔧 Configuration Issues

### Environment Variables

**Error**: `ConfigurationError: Missing required environment variable`

**Quick Fix**:
1. **Check `.env` file** exists in backend directory
2. **Verify all required variables** are set
3. **Check variable names** match exactly
4. **Restart application** after changes

**Required Variables**:
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
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'minerva_backend'`

**Quick Fix**:
```bash
# Activate virtual environment
poetry shell

# Reinstall dependencies
poetry install

# Check Python path
which python
```

**Common Causes**:
- Virtual environment not activated
- Dependencies not installed
- Wrong Python version
- Path issues

## 📊 Performance Issues

### Slow Processing

**Symptoms**: Entity extraction takes > 5 minutes

**Debug Steps**:
1. **Check LLM service** performance
2. **Monitor memory usage**
3. **Check database performance**
4. **Review processing logs**

**Quick Fixes**:
```bash
# Check memory usage
htop

# Check database performance
# In Neo4j Browser
CALL db.stats.retrieve('GRAPH COUNTS');
CALL db.stats.retrieve('QUERIES');

# Check processing logs
tail -f logs/minerva_performance.log
```

### High Memory Usage

**Symptoms**: System running out of memory

**Quick Fixes**:
1. **Restart services** (Neo4j, Temporal, Ollama)
2. **Check for memory leaks** in logs
3. **Reduce batch sizes** in processing
4. **Increase system memory** if possible

### Slow API Responses

**Symptoms**: API calls taking > 10 seconds

**Debug Steps**:
1. **Check service health** endpoints
2. **Monitor database queries**
3. **Check network connectivity**
4. **Review API logs**

## 📝 Log Analysis

### Checking Logs

**Log Locations**:
- **Application logs**: `logs/minerva.log`
- **Error logs**: `logs/minerva_errors.log`
- **Performance logs**: `logs/minerva_performance.log`
- **LLM logs**: `logs/minerva_llm.log`

**Common Commands**:
```bash
# View recent errors
tail -f logs/minerva_errors.log

# Search for specific errors
grep "ERROR" logs/minerva.log

# Check performance
tail -f logs/minerva_performance.log

# Monitor all logs
tail -f logs/*.log
```

### Common Log Patterns

**Neo4j Connection Issues**:
```
ERROR: ServiceUnavailableError: Neo4j Database service is currently unavailable
```

**LLM Service Issues**:
```
ERROR: ServiceUnavailableError: LLM service is currently unavailable
```

**Processing Issues**:
```
ERROR: ProcessingError: Failed to extract entities from journal entry
```

**Temporal Issues**:
```
ERROR: ConnectionError: Failed to connect to Temporal
```

## 🔍 Debugging Tools

### Health Check Endpoints

```bash
# System health
curl http://localhost:8000/api/health

# Database health
curl http://localhost:8000/api/health/database

# Processing status
curl http://localhost:8000/api/processing/status
```

### Database Browser

- **Neo4j Browser**: http://localhost:7474
- **Username**: neo4j
- **Password**: Alxe342!

### Temporal Web UI

- **Temporal Web UI**: http://localhost:8080
- **View workflows**: http://localhost:8080/namespaces/default/workflows

### API Documentation

- **Interactive API**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## 🚀 Quick Recovery

### Complete System Reset

```bash
# Stop all services
docker stop $(docker ps -q) 2>/dev/null || true
pkill -f "ollama serve" 2>/dev/null || true
pkill -f "temporal" 2>/dev/null || true

# Clean up
docker system prune -f

# Restart services
# 1. Start Neo4j
docker run --name neo4j-minerva -p 7474:7474 -p 7687:7687 -d -v $HOME/neo4j/data:/data --env NEO4J_AUTH=neo4j/Alxe342! neo4j:5.0

# 2. Start Temporal
temporal server start-dev

# 3. Start Ollama
ollama serve

# 4. Start Minerva
cd backend
poetry shell
python -m minerva_backend.api.main
```

### Database Reset

```bash
# Clear Neo4j database
# In Neo4j Browser (http://localhost:7474)
MATCH (n) DETACH DELETE n;

# Reinitialize
python -c "
from minerva_backend.containers import Container
container = Container()
container.db_connection().init_emotion_types()
print('Database reset and initialized!')
"
```

## 📞 Getting More Help

1. **Check this guide** for your specific issue
2. **Review error codes** in [API Error Codes](api/error-codes.md)
3. **Check logs** for detailed error information
4. **Search issues** in the repository
5. **Contact development team** with:
   - Error message
   - Log excerpts
   - Steps to reproduce
   - System configuration

---

*This troubleshooting guide covers the most common issues. For specific problems not covered here, check the detailed documentation in each component's section.*
