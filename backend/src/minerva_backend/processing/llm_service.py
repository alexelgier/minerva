# minerva_backend/processing/llm_service.py

from typing import Optional, Dict, Any
import httpx
from pydantic import BaseModel
import ollama

class LLMRequest(BaseModel):
    model: str
    prompt: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None


class LLMResponse(BaseModel):
    text: str
    model: str
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None


class LLMService:
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.client = httpx.AsyncClient()

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generic LLM generation - just handles the HTTP call"""
        # Format request for Ollama API
        # Handle HTTP errors, timeouts
        # Parse response
        # Return structured response
        pass

    async def close(self):
        """Cleanup HTTP client"""
        await self.client.aclose()