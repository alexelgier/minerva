"""
Application Configuration
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings, loaded from environment variables."""
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "Alxe342!"
    CURATION_DB_PATH: str = "curation.db"
    TEMPORAL_URI: str = "localhost:7233"


# Singleton instance of settings
settings = Settings()
