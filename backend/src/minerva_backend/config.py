"""
Application Configuration
Loads settings from environment variables.
"""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings, loaded from environment variables."""
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "Alxe342!"
    CURATION_DB_PATH: str = "curation.db"
    TEMPORAL_URI: str = "localhost:7233"

    # API Configuration
    api_title: str = "Minerva Backend"
    api_version: str = "0.1.0"
    api_description: str = "Personal Knowledge Management System"
    debug: bool = False

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # Database Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"

    # Temporal Configuration
    temporal_host: str = "localhost"
    temporal_port: int = 7233

    # Curation Database
    curation_db_path: str = "curation.db"

    # Processing Configuration
    default_processing_start: str = "06:00"
    default_processing_end: str = "12:00"
    max_status_poll_attempts: int = 10
    status_poll_interval: float = 0.2

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    class Config:
        env_file = ".env"
        env_prefix = "MINERVA_"
        case_sensitive = False


# Singleton instance of settings
settings = Settings()
