# Documentation Index

## 🚀 Quick Start
- **New to Minerva?** → [README](README.md) → [Architecture Overview](architecture/overview.md) → [Development Setup](development/setup.md)
- **Need to understand the system?** → [Architecture Overview](architecture/overview.md) → [Processing Pipeline](architecture/processing-pipeline.md) → [Database Schema](architecture/database-schema.md)
- **Ready to develop?** → [Developer Onboarding](development/onboarding.md) → [Testing Guide](development/testing.md) → [API Endpoints](api/endpoints.md)

## 📋 By Task

### Development Tasks
- **Set up development environment** → [Development Setup](development/setup.md)
- **Understand the architecture** → [Architecture Overview](architecture/overview.md)
- **Add new features** → [Developer Onboarding](development/onboarding.md) → [Feature Development Guide](development/feature-development.md)
- **Debug issues** → [Troubleshooting Guide](troubleshooting/index.md)
- **Run tests** → [Testing Guide](development/testing.md)
- **Deploy to production** → [Production Deployment](deployment/production-deployment.md)

### API Tasks
- **Integrate with API** → [API Endpoints](api/endpoints.md)
- **Handle errors** → [Error Codes](api/error-codes.md)
- **Test API endpoints** → [API Testing](development/testing.md#api-testing)

### Database Tasks
- **Understand data model** → [Database Schema](architecture/database-schema.md)
- **Query data** → [Database Schema](architecture/database-schema.md#common-queries)
- **Modify schema** → [Database Schema](architecture/database-schema.md#maintenance)

### Processing Tasks
- **Understand processing flow** → [Processing Pipeline](architecture/processing-pipeline.md)
- **Add new entity types** → [Processing Pipeline](architecture/processing-pipeline.md#adding-new-entity-types)
- **Debug processing issues** → [Troubleshooting Guide](troubleshooting/index.md)

## 🏗️ By Component

### Core Architecture
- **System Overview** → [Architecture Overview](architecture/overview.md)
- **Processing Pipeline** → [Processing Pipeline](architecture/processing-pipeline.md)
- **Database Design** → [Database Schema](architecture/database-schema.md)
- **Dependency Injection** → [Dependency Injection](architecture/dependency-injection.md)

### API Layer
- **REST Endpoints** → [API Endpoints](api/endpoints.md)
- **Error Handling** → [Error Codes](api/error-codes.md)
- **Request/Response Models** → [API Endpoints](api/endpoints.md#detailed-endpoint-documentation)

### Processing Layer
- **Entity Extraction** → [Concept Extraction](features/concept-extraction.md)
- **Relationship Extraction** → [Concept Relations](features/concept-relations.md)
- **Temporal Workflows** → [Temporal Serialization](features/temporal-serialization.md)
- **Field Comparison** → [Field Comparison](features/field-comparison.md)

### Development Tools
- **Setup & Configuration** → [Development Setup](development/setup.md)
- **Testing Framework** → [Testing Guide](development/testing.md)
- **Code Coverage** → [Coverage Reporting](development/coverage-reporting.md)
- **Onboarding** → [Developer Onboarding](development/onboarding.md)

## 🔧 By Problem Type

### Setup Issues
- **Can't connect to Neo4j** → [Troubleshooting Guide](troubleshooting/index.md#neo4j-connection-issues)
- **Poetry installation failed** → [Development Setup](development/setup.md#step-1-install-python-and-poetry)
- **Temporal connection failed** → [Troubleshooting Guide](troubleshooting/index.md#temporal-connection-issues)

### Development Issues
- **Tests failing** → [Testing Guide](development/testing.md#troubleshooting)
- **Import errors** → [Troubleshooting Guide](troubleshooting/index.md#import-errors)
- **Database initialization failed** → [Troubleshooting Guide](troubleshooting/index.md#database-issues)

### Processing Issues
- **Entity extraction failing** → [Troubleshooting Guide](troubleshooting/index.md#processing-issues)
- **LLM service unavailable** → [Troubleshooting Guide](troubleshooting/index.md#llm-service-issues)
- **Temporal serialization errors** → [Temporal Serialization](features/temporal-serialization.md#troubleshooting)

### API Issues
- **Validation errors** → [Error Codes](api/error-codes.md#validation_error-400)
- **Service unavailable** → [Error Codes](api/error-codes.md#service_unavailable-503)
- **Processing errors** → [Error Codes](api/error-codes.md#processing_error-422)

## 🎯 Common Decision Trees

### "How do I add a new entity type?"
1. **Is it a domain entity?** → Yes → Go to step 2
   - No → Use existing generic entity types
2. **Does it need special processing?** → Yes → Create processor
   - No → Use base entity processor
3. **Does it need relationships?** → Yes → Add to relationship extraction
   - No → Skip relationship processing
4. **Does it need vector search?** → Yes → Add to vector indexes
   - No → Skip vector search setup
5. **Documentation** → Update [Database Schema](architecture/database-schema.md) and [Processing Pipeline](architecture/processing-pipeline.md)

### "How do I debug a processing issue?"
1. **Check logs** → [Troubleshooting Guide](troubleshooting/index.md#checking-logs)
2. **Verify services** → [Troubleshooting Guide](troubleshooting/index.md#verifying-services)
3. **Check configuration** → [Development Setup](development/setup.md#step-6-configure-environment)
4. **Run tests** → [Testing Guide](development/testing.md#running-tests)

### "How do I understand the system architecture?"
1. **Start with overview** → [Architecture Overview](architecture/overview.md)
2. **Understand data flow** → [Processing Pipeline](architecture/processing-pipeline.md)
3. **Explore database** → [Database Schema](architecture/database-schema.md)
4. **See dependencies** → [Dependency Injection](architecture/dependency-injection.md)

## 📚 Feature-Specific Guides

### Concept Extraction
- **Overview** → [Concept Extraction](features/concept-extraction.md)
- **Relations** → [Concept Relations](features/concept-relations.md)
- **Field Comparison** → [Field Comparison](features/field-comparison.md)
- **Frontmatter Constants** → [Frontmatter Constants](features/frontmatter-constants.md)

### Temporal Workflows
- **Serialization** → [Temporal Serialization](features/temporal-serialization.md)
- **Entity UUID Handling** → [Entity UUID Handling](features/entity-uuid-handling.md)
- **Processing Pipeline** → [Processing Pipeline](architecture/processing-pipeline.md#temporal-workflow)

### Database Operations
- **Schema** → [Database Schema](architecture/database-schema.md)
- **Queries** → [Database Schema](architecture/database-schema.md#common-queries)
- **Indexes** → [Database Schema](architecture/database-schema.md#indexes)
- **Constraints** → [Database Schema](architecture/database-schema.md#constraints)

## 🔍 Quick Reference

### Key Files
- **Main API** → `src/minerva_backend/api/main.py`
- **Processing Pipeline** → `src/minerva_backend/processing/extraction_service.py`
- **Database Connection** → `src/minerva_backend/graph/db.py`
- **Configuration** → `src/minerva_backend/config.py`
- **Dependency Injection** → `src/minerva_backend/containers.py`

### Key Commands
- **Run tests** → `poetry run pytest`
- **Start server** → `python -m minerva_backend.api.main`
- **Check health** → `curl http://localhost:8000/api/health`
- **Run coverage** → `poetry run pytest --cov=minerva_backend --cov-report=html`

### Key URLs
- **API Documentation** → http://localhost:8000/docs
- **Health Check** → http://localhost:8000/api/health
- **Neo4j Browser** → http://localhost:7474
- **Temporal Web UI** → http://localhost:8080

## 📞 Getting Help

1. **Check this index** for relevant documentation
2. **Use decision trees** for step-by-step guidance
3. **Check troubleshooting guide** for common issues
4. **Review error codes** for API-specific problems
5. **Contact development team** if issues persist

---

*This index is designed to help both developers and AI assistants quickly find the right documentation for any task or problem.*
