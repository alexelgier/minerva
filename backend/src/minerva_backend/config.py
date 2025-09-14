"""
Application Configuration
Loads settings from environment variables.
"""
import os

try:
    # It's a good practice to use python-dotenv for local development
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If dotenv is not installed, we'll just rely on system environment variables
    pass


class Settings:
    """Application configuration settings, loaded from environment variables."""
    NEO4J_URI: str = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.environ.get("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.environ.get("NEO4J_PASSWORD", "Alxe342!")


# Singleton instance of settings
settings = Settings()
