# minerva_backend/processing/llm_service.py

import asyncio
import hashlib
import json
import logging
from time import time
from typing import Any, ClassVar, Dict, List, Optional, Type, Union

from diskcache import Cache
from pydantic import BaseModel

from minerva_backend.utils.logging import get_llm_logger

logger = logging.getLogger(__name__)
llm_logger = get_llm_logger()


class LLMService:
    """Service for handling LLM generation and embeddings with caching, retries, and monitoring."""

    MAX_RETRIES: ClassVar[int] = 3

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        cache: bool = False,
        model: str = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest",
        embedding_model: str = "mxbai-embed-large:latest",
    ):
        # Initialize without importing ollama to avoid blocking
        self.ollama_url = ollama_url
        self.cache_enabled = cache
        self.cache = Cache("./llm_cache") if cache else None
        self.model = model
        self.embedding_model = embedding_model
        self.client = None  # Will be initialized in async_init

    async def async_init(self):
        """Async initialization to avoid blocking the event loop."""
        # Move the ollama import to a separate thread to avoid blocking
        def _import_and_create_client():
            import ollama
            return ollama.AsyncClient(host=self.ollama_url)
        
        try:
            self.client = await asyncio.to_thread(_import_and_create_client)
        except Exception as e:
            raise

    @classmethod
    async def create(
        cls,
        ollama_url: str = "http://localhost:11434",
        cache: bool = False,
        model: str = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest",
        embedding_model: str = "mxbai-embed-large:latest",
    ) -> "LLMService":
        """Factory method to create and initialize LLMService asynchronously."""
        instance = cls(ollama_url, cache, model, embedding_model)
        await instance.async_init()
        return instance

    async def generate(
        self,
        prompt: str,
        model: str = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest",
        system_prompt: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[BaseModel, Dict[str, Any], str]:
        """
        Generate LLM response with streaming, monitoring, caching, and retry logic.
        """
        # Log request submission
        llm_logger.log_request(model, prompt, system_prompt)

        merged_options = options or {}
        cache_key = _get_cache_key(
            model, prompt, system_prompt, response_model, merged_options
        )

        # Check cache first
        cached_result = self._check_cache(cache_key, model, response_model)
        if cached_result is not None:
            return cached_result

        # Generate with retry logic
        return await self._generate_with_retry(
            model, prompt, system_prompt, response_model, merged_options, cache_key
        )

    def _check_cache(
        self, cache_key: str, model: str, response_model: Optional[Type[BaseModel]]
    ) -> Optional[Union[BaseModel, Dict[str, Any], str]]:
        """Check cache for existing response and return if found."""
        if not self.cache_enabled:
            return None

        cached_resp = self.cache.get(cache_key) if self.cache else None
        if not cached_resp:
            return None

        # Log cached response
        llm_logger.log_response(model, str(cached_resp), 0, 0)

        if response_model and isinstance(cached_resp, dict):
            return response_model.model_validate(cached_resp)
        elif not response_model and isinstance(cached_resp, str):
            return cached_resp

        return None

    async def _generate_with_retry(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        response_model: Optional[Type[BaseModel]],
        merged_options: Dict[str, Any],
        cache_key: str,
    ) -> Union[BaseModel, Dict[str, Any], str]:
        """Generate response with retry logic."""
        retry_count = 0
        last_error = None

        while retry_count <= self.MAX_RETRIES:
            try:
                return await self._process_generation(
                    model,
                    prompt,
                    system_prompt,
                    response_model,
                    merged_options,
                    cache_key,
                )
            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.MAX_RETRIES:
                    wait_time = min(2**retry_count, 30)
                    await asyncio.sleep(wait_time)
                else:
                    # Truncate error message to prevent large payloads in Temporal
                    error_msg = (
                        str(last_error)[:200] + "..."
                        if len(str(last_error)) > 200
                        else str(last_error)
                    )
                    raise Exception(
                        f"LLM generation failed after {retry_count} attempts: {error_msg}"
                    )
        # This should never be reached, but mypy needs it
        raise RuntimeError("Unexpected end of retry loop")  # type: ignore[return-value]

    async def _process_generation(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        response_model: Optional[Type[BaseModel]],
        merged_options: Dict[str, Any],
        cache_key: str,
    ) -> Union[BaseModel, Dict[str, Any], str]:
        """Process a single generation attempt."""
        start_time = time()

        # Validate client
        if self.client is None:
            raise Exception("self.client is None!")

        # Get effective max tokens
        effective_max_tokens = self._get_effective_max_tokens(merged_options)

        # Generate stream
        stream = await self.client.generate(
            model=model,
            prompt=prompt,
            system=system_prompt,
            stream=True,
            format=(response_model.model_json_schema() if response_model else None),
            options=merged_options,
        )

        # Process stream
        full_response_content, token_count = await self._process_stream(
            stream, effective_max_tokens, start_time
        )

        # Validate response
        if not full_response_content.strip():
            raise Exception("Empty response received")

        # Log response completion
        duration_ms = (time() - start_time) * 1000
        llm_logger.log_response(model, full_response_content, duration_ms, token_count)

        # Validate and cache response
        return self._validate_and_cache_response(
            full_response_content, response_model, cache_key
        )

    def _get_effective_max_tokens(self, merged_options: Dict[str, Any]) -> int:
        """Get effective max tokens from options."""
        effective_max_tokens = merged_options.get("num_predict", -1)
        if effective_max_tokens is None or effective_max_tokens <= 0:
            effective_max_tokens = 8192
        return effective_max_tokens

    async def _process_stream(
        self, stream, effective_max_tokens: int, start_time: float
    ) -> tuple[str, int]:
        """Process the streaming response and return content and token count."""
        full_response_content = ""
        token_count = 0
        last_repetition_check = time()

        async for chunk in stream:
            if "response" in chunk:
                full_response_content += chunk["response"]
                # Estimate tokens based on text length (rough approximation: 1 token ≈ 4 characters)
                token_count = len(full_response_content) // 4

            current_time = time()

            # Check limits
            if token_count >= effective_max_tokens:
                break
            if current_time - start_time > 1800:  # 30 minutes timeout
                break

            # Check for repetition
            if self._should_check_repetition(
                current_time, last_repetition_check, token_count, full_response_content
            ):
                if _detect_exact_repetition(
                    full_response_content
                ) or _detect_low_entropy(full_response_content):
                    raise Exception("Model stuck in repetitive loop")
                last_repetition_check = current_time

            if chunk.get("done"):
                break

        return full_response_content, token_count

    def _should_check_repetition(
        self,
        current_time: float,
        last_repetition_check: float,
        token_count: int,
        full_response_content: str,
    ) -> bool:
        """Determine if we should check for repetition."""
        return (
            (current_time - last_repetition_check > 30.0)
            or (token_count > 0 and token_count % 50 == 0)
        ) and len(full_response_content) > 200

    def _validate_and_cache_response(
        self,
        full_response_content: str,
        response_model: Optional[Type[BaseModel]],
        cache_key: str,
    ) -> Union[BaseModel, Dict[str, Any], str]:
        """Validate response and cache if enabled."""
        if response_model:
            try:
                result = json.loads(full_response_content)
                validated_result = response_model.model_validate(result)
                if self.cache_enabled and self.cache:
                    self.cache.set(cache_key, result)
                return validated_result
            except (json.JSONDecodeError, ValueError) as e:
                raise e
        else:
            if self.cache_enabled and self.cache:
                self.cache.set(cache_key, full_response_content)
            return full_response_content

    async def create_embedding(
        self, text: str, model: str = None, options: dict = None
    ) -> List[float]:
        """Generate an embedding for a single piece of text."""
        if model is None:
            model = self.embedding_model

        result = await self.client.embeddings(model=model, prompt=text, options=options)
        return result["embedding"]

    async def create_embeddings_batch(
        self, texts: List[str], model: str
    ) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        # Note: ollama-python async client doesn't have a batch embed method.
        # We run them concurrently.
        tasks = [self.create_embedding(text, model) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        return list(embeddings)

    async def embeddings(
        self, text: str, model: str = None, options: dict = None
    ) -> List[float]:
        """Generate embeddings for text (alias for create_embedding)."""
        if model is None:
            model = self.embedding_model
        return await self.create_embedding(text, model, options)

    async def health_check(self) -> bool:
        """Check if the LLM service is healthy."""
        try:
            # Simple test to check if service is responsive
            await self.client.list()
            return True
        except Exception as e:
            return False


def _get_cache_key(
    model: str,
    prompt: str,
    system_prompt: Optional[str],
    response_model: Optional[Type[BaseModel]],
    options: Optional[Dict[str, Any]],
) -> str:
    key_data = {
        "model": model,
        "prompt": prompt,
        "system_prompt": system_prompt,
        "response_model": response_model.__name__ if response_model else None,
        "options": options or {},
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_string.encode()).hexdigest()


def _detect_exact_repetition(
    text: str, min_repeat_length: int = 20, min_repetitions: int = 3
) -> bool:
    """Detect if text ends with consecutive exact repetitions."""
    required_length = min_repeat_length * min_repetitions
    if len(text) < required_length:
        return False
    end_of_text = text[-required_length:]
    for length in range(min_repeat_length, len(end_of_text) // min_repetitions + 1):
        chunk = end_of_text[-length:]
        repetitions = 1
        for i in range(2, min_repetitions + 1):
            start_idx = -i * length
            end_idx = start_idx + length
            if end_of_text[start_idx:end_idx] == chunk:
                repetitions += 1
            else:
                break
        if repetitions >= min_repetitions:
            return True
    return False


def _detect_low_entropy(text: str, window_size: int = 100) -> bool:
    """Detect low entropy (repetitive) content in recent text"""
    if len(text) < window_size:
        return False
    recent = text[-window_size:]
    unique_ratio = len(set(recent)) / len(recent)
    if unique_ratio < 0.15:
        return True
    return False
