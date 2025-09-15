# minerva_backend/processing/llm_service.py

import asyncio
import hashlib
import json
import logging
from time import time
from typing import Optional, List, ClassVar, Dict, Any, Type, Union

import ollama
from diskcache import Cache
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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

    def _get_cache_key(self, model: str, prompt: str, system_prompt: Optional[str],
                         response_model: Optional[Type[BaseModel]], options: Optional[Dict[str, Any]]) -> str:
        key_data = {
            "model": model,
            "prompt": prompt,
            "system_prompt": system_prompt,
            "response_model": response_model.__name__ if response_model else None,
            "options": options or {}
        }
        key_string = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def generate(self, model: str, prompt: str, system_prompt: Optional[str] = None,
                         response_model: Optional[Type[BaseModel]] = None,
                         options: Optional[Dict[str, Any]] = None) -> Union[Dict[str, Any], str]:
        """
        Generate LLM response with streaming, monitoring, caching, and retry logic.
        """
        retry_count = 0
        last_error = None
        merged_options = options or {}

        # Check Cache
        cache_key = self._get_cache_key(model, prompt, system_prompt, response_model, merged_options)
        if self.cache_enabled and self.cache.get(cache_key):
            cached_resp = self.cache.get(cache_key)
            logger.debug("✅ Using cached response")
            if response_model and isinstance(cached_resp, dict):
                return cached_resp
            elif not response_model and isinstance(cached_resp, str):
                return cached_resp

        while retry_count <= self.MAX_RETRIES:
            try:
                start_time = time()

                logger.debug("=" * 70)
                logger.debug("=" * 31 + " LLM REQ " + "=" * 30)
                logger.debug(f"Model: {model}, Options: {merged_options}")
                logger.debug(f"System Prompt:\n{system_prompt}")
                logger.debug(f"User Prompt:\n{prompt}")
                logger.debug("=" * 70)
                logger.debug("🚀 Starting model inference...")

                full_response_content = ""
                token_count = 0
                last_log_time = time()
                last_repetition_check = time()
                effective_max_tokens = merged_options.get('num_predict', -1)
                if effective_max_tokens is None or effective_max_tokens <= 0:
                    effective_max_tokens = 8192

                stream = await self.client.generate(
                    model=model,
                    prompt=prompt,
                    system=system_prompt,
                    stream=True,
                    format='json' if response_model else None,
                    options=merged_options
                )

                async for chunk in stream:
                    if 'response' in chunk:
                        full_response_content += chunk['response']
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
                        break

                logger.debug(f"✅ Generation complete! Total tokens: {token_count}")

                if not full_response_content.strip():
                    raise Exception("Empty response received")

                if response_model:
                    try:
                        result = json.loads(full_response_content)
                        response_model.model_validate(result)  # Validate against the model
                        if self.cache_enabled:
                            logger.debug("💾 Caching structured response...")
                            self.cache.set(cache_key, result)
                        return result
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"❌ Failed to parse or validate JSON response: {e}")
                        logger.error(f"Raw response: {full_response_content[:500]}...")
                        raise e
                else:
                    if self.cache_enabled:
                        logger.debug("💾 Caching raw text response...")
                        self.cache.set(cache_key, full_response_content)
                    return full_response_content

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
