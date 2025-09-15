# minerva_backend/processing/llm_service.py

from typing import Optional, Dict, Any
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
        self.client = ollama.AsyncClient(host=ollama_url)

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generic LLM generation - just handles the HTTP call"""
        messages = []
        if request.system_prompt:
            messages.append({'role': 'system', 'content': request.system_prompt})
        messages.append({'role': 'user', 'content': request.prompt})

        options = {}
        if request.temperature is not None:
            options['temperature'] = request.temperature
        if request.max_tokens is not None:
            options['num_predict'] = request.max_tokens

        response = await self.client.chat(
            model=request.model,
            messages=messages,
            options=options
        )

        return LLMResponse(
            text=response['message']['content'],
            model=response['model'],
            total_duration=response.get('total_duration'),
            load_duration=response.get('load_duration'),
        )

    async def close(self):
        """Cleanup HTTP client"""
        await self.client._client.aclose()
