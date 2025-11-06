"""
Ollama integration utilities for testing.

Provides utilities for checking Ollama availability and managing
Ollama connections for integration tests.
"""

import asyncio
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest"


class OllamaTestManager:
    """Manages Ollama integration for testing."""
    
    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = OLLAMA_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = None
    
    async def check_availability(self) -> bool:
        """Check if Ollama is running and available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    logger.info("Ollama is available for testing")
                    return True
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    async def check_model_available(self) -> bool:
        """Check if the required model is available."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in models]
                    is_available = any(self.model in name for name in model_names)
                    if is_available:
                        logger.info(f"Model {self.model} is available")
                    else:
                        logger.warning(f"Model {self.model} not found. Available: {model_names}")
                    return is_available
                else:
                    logger.warning(f"Failed to get model list: {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"Failed to check model availability: {e}")
            return False
    
    async def test_generation(self, prompt: str = "Hello, world!") -> bool:
        """Test if Ollama can generate responses."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=30.0
                )
                if response.status_code == 200:
                    result = response.json()
                    if "response" in result:
                        logger.info("Ollama generation test successful")
                        return True
                    else:
                        logger.warning("Ollama response missing 'response' field")
                        return False
                else:
                    logger.warning(f"Ollama generation failed: {response.status_code}")
                    return False
        except Exception as e:
            logger.warning(f"Ollama generation test failed: {e}")
            return False
    
    async def is_ready_for_testing(self) -> bool:
        """Check if Ollama is ready for integration testing."""
        availability = await self.check_availability()
        if not availability:
            return False
        
        model_available = await self.check_model_available()
        if not model_available:
            return False
        
        generation_works = await self.test_generation()
        return generation_works


async def check_ollama_availability() -> bool:
    """Check if Ollama is available for testing."""
    manager = OllamaTestManager()
    return await manager.is_ready_for_testing()


def pytest_configure(config):
    """Configure pytest to check Ollama availability."""
    # This will be called during pytest configuration
    pass


def pytest_collection_modifyitems(config, items):
    """Modify test items based on Ollama availability."""
    # Only check Ollama availability for integration tests, not unit tests
    # Check if we're running unit tests by looking at the test paths
    unit_test_paths = [item for item in items if "unit" in str(item.fspath)]
    if unit_test_paths and len(unit_test_paths) == len(items):
        # All tests are unit tests, skip Ollama checks
        return
    
    # Check Ollama availability synchronously for pytest
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ollama_available = loop.run_until_complete(check_ollama_availability())
        loop.close()
    except Exception:
        ollama_available = False
    
    # Mark tests that require Ollama
    for item in items:
        if "ollama" in item.keywords:
            if not ollama_available:
                item.add_marker(pytest.mark.skip(reason="Ollama not available"))
            else:
                item.add_marker(pytest.mark.ollama)


# Import pytest here to avoid circular imports
import pytest
