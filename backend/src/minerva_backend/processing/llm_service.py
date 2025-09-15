# minerva_backend/processing/llm_service.py

import asyncio
import hashlib
import json
import logging
from time import time
from typing import Optional, List, ClassVar

import ollama
from diskcache import Cache
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LLMRequest(BaseModel):
    model: str
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.0
    max_tokens: Optional[int] = -1  # -1 for unlimited
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    repeat_penalty: Optional[float] = 1.15
    repeat_last_n: Optional[int] = 128
    num_ctx: Optional[int] = 16384
    response_format: Optional[str] = None  # e.g., 'json'


class LLMResponse(BaseModel):
    text: str
    model: str
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None


class LLMService:
    """Service for handling LLM generation and embeddings with caching, retries, and monitoring."""
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(self, ollama_url: str = "http://localhost:11434", cache: bool = False):
        self.client = ollama.AsyncClient(host=ollama_url)
        self.cache_enabled = cache
        self.cache = Cache('./llm_cache') if cache else None

    @staticmethod
    def _detect_exact_repetition(text: str, min_repeat_length: int = 20, min_repetitions: int = 3) -> bool:
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
                logger.warning(f"🔄 Repetition detected! Pattern: '{chunk[:50]}...' repeated {repetitions} times")
                return True
        return False

    @staticmethod
    def _detect_low_entropy(text: str, window_size: int = 100) -> bool:
        """Detect low entropy (repetitive) content in recent text"""
        if len(text) < window_size:
            return False
        recent = text[-window_size:]
        unique_ratio = len(set(recent)) / len(recent)
        if unique_ratio < 0.15:
            logger.warning(f"🔄 Low entropy detected! Unique ratio: {unique_ratio:.2f}")
            return True
        return False

    def _get_cache_key(self, request: LLMRequest) -> str:
        key_data = request.model_dump()
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate LLM response with streaming, monitoring, caching, and retry logic.
        """
        retry_count = 0
        last_error = None

        # Check Cache
        cache_key = self._get_cache_key(request)
        if self.cache_enabled and self.cache.get(cache_key):
            cached_resp_dict = self.cache.get(cache_key)
            logger.debug("✅ Using cached response")
            return LLMResponse(**cached_resp_dict)

        while retry_count <= self.MAX_RETRIES:
            try:
                start_time = time()
                messages = []
                if request.system_prompt:
                    messages.append({'role': 'system', 'content': request.system_prompt})
                messages.append({'role': 'user', 'content': request.prompt})

                options = {
                    'temperature': request.temperature,
                    'num_predict': request.max_tokens,
                    'top_p': request.top_p,
                    'top_k': request.top_k,
                    'repeat_penalty': request.repeat_penalty,
                    'repeat_last_n': request.repeat_last_n,
                    'num_ctx': request.num_ctx,
                }
                # Filter out None values
                options = {k: v for k, v in options.items() if v is not None}

                logger.debug("=" * 70)
                logger.debug("=" * 31 + " LLM REQ " + "=" * 30)
                logger.debug(f"Model: {request.model}, Options: {options}")
                logger.debug(f"System Prompt:\n{request.system_prompt}")
                logger.debug(f"User Prompt:\n{request.prompt}")
                logger.debug("=" * 70)
                logger.debug("🚀 Starting model inference...")

                full_response_content = ""
                token_count = 0
                last_log_time = time()
                last_repetition_check = time()
                effective_max_tokens = request.max_tokens if request.max_tokens and request.max_tokens > 0 else 8192

                stream = await self.client.chat(
                    model=request.model,
                    messages=messages,
                    stream=True,
                    format=request.response_format,
                    options=options
                )

                final_response_dict = {}
                async for chunk in stream:
                    if 'message' in chunk and 'content' in chunk['message']:
                        full_response_content += chunk['message']['content']
                        token_count += 1

                    current_time = time()
                    if token_count >= effective_max_tokens:
                        logger.warning(f"🛑 Reached token limit ({effective_max_tokens})")
                        break
                    if current_time - start_time > 1800:
                        logger.warning("🛑 Reached time limit (30 minutes)")
                        break

                    if ((current_time - last_repetition_check > 30.0) or (token_count % 100 == 0)) and len(
                            full_response_content) > 200:
                        if self._detect_exact_repetition(full_response_content) or self._detect_low_entropy(
                                full_response_content):
                            raise Exception("Model stuck in repetitive loop")
                        last_repetition_check = current_time

                    if (current_time - last_log_time > 25.0) or (token_count % 100 == 0):
                        elapsed = current_time - start_time
                        tokens_per_sec = token_count / (elapsed + 0.001)
                        logger.debug(f"⏰ {int(elapsed // 60)}m{int(elapsed % 60)}s | "
                                     f"🔢 {token_count} tokens | "
                                     f"📊 {tokens_per_sec:.1f} tokens/sec")
                        last_log_time = current_time

                    if chunk.get('done'):
                        final_response_dict = chunk
                        break
                
                logger.debug(f"✅ Generation complete! Total tokens: {token_count}")

                if not full_response_content.strip():
                    raise Exception("Empty response received")

                response = LLMResponse(
                    text=full_response_content,
                    model=final_response_dict.get('model', request.model),
                    total_duration=final_response_dict.get('total_duration'),
                    load_duration=final_response_dict.get('load_duration'),
                )

                if self.cache_enabled:
                    logger.debug("💾 Caching response...")
                    self.cache.set(cache_key, response.model_dump())
                
                duration = time() - start_time
                logger.debug(f'🎯 Ollama response completed in {int(duration // 60)}m{int(duration % 60)}s')
                return response

            except Exception as e:
                last_error = e
                retry_count += 1
                if retry_count <= self.MAX_RETRIES:
                    wait_time = min(2 ** retry_count, 30)
                    logger.warning(f"🔄 Attempt {retry_count} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ All {self.MAX_RETRIES} attempts failed. Last error: {e}")
                    raise last_error

    async def create_embedding(self, text: str, model: str) -> List[float]:
        """Generate an embedding for a single piece of text."""
        result = await self.client.embeddings(model=model, prompt=text)
        return result['embedding']

    async def create_embeddings_batch(self, texts: List[str], model: str) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        # Note: ollama-python async client doesn't have a batch embed method.
        # We run them concurrently.
        tasks = [self.create_embedding(text, model) for text in texts]
        embeddings = await asyncio.gather(*tasks)
        return embeddings

    async def close(self):
        """Cleanup HTTP client and cache."""
        await self.client._client.aclose()
        if self.cache_enabled:
            self.cache.close()
