import asyncio
import hashlib
import json
import logging
import typing
from time import time
from typing import ClassVar, Iterable

import ollama
from diskcache import Cache
from graphiti_core.embedder import EmbedderClient
from graphiti_core.llm_client import LLMClient, LLMConfig
from graphiti_core.llm_client.config import ModelSize
from graphiti_core.prompts import Message
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MEDIUM = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest"
SMALL = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:latest"


class MinervaClient(LLMClient):
    # Class-level constants
    MAX_RETRIES: ClassVar[int] = 3

    def __init__(
            self, config: LLMConfig | None = None, cache: bool = False, client: typing.Any = None
    ):
        """
        Initialize the OpenAIClient with the provided configuration, cache setting, and client.

        Args:
            config (LLMConfig | None): The configuration for the LLM client, including API key, model, base URL, temperature, and max tokens.
            cache (bool): Whether to use caching for responses. Defaults to False.
            client (Any | None): An optional async client instance to use. If not provided, a new AsyncOpenAI client is created.

        """

        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)

        self.client = ollama.Client()

        self.cache_enabled = cache
        self.cache = Cache('./llm_cache') if cache else None

    async def _generate_response(
            self,
            messages: list[Message],
            response_model: type[BaseModel] | None = None,
            max_tokens: int = -1,
            model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        raise Exception('_generate_response called in MinervaClient!')

    async def generate_response(
            self,
            messages: list[Message],
            response_model: type[BaseModel] | None = None,
            max_tokens: int | None = -1,
            model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        retry_count = 0

        def detect_exact_repetition(text: str, min_repeat_length: int = 20, min_repetitions: int = 3) -> bool:
            """Detect if text ends with consecutive exact repetitions."""
            # Check if the text is long enough to contain the required repetitions
            required_length = min_repeat_length * min_repetitions
            if len(text) < required_length:
                return False

            # Focus on the end of the text to check for consecutive repetitions
            end_of_text = text[-required_length:]

            # Check for consecutive repetitions of increasing chunk sizes
            for length in range(min_repeat_length, len(end_of_text) // min_repetitions + 1):
                # Extract the potential repeating chunk from the very end
                chunk = end_of_text[-length:]
                # Count how many times this chunk repeats consecutively at the end
                repetitions = 1
                for i in range(2, min_repetitions + 1):
                    start = -i * length
                    end = start + length
                    if end_of_text[start:end] == chunk:
                        repetitions += 1
                    else:
                        break

                # If we found enough consecutive repetitions, return True
                if repetitions >= min_repetitions:
                    logger.warning(f"🔄 Repetition detected! Pattern: '{chunk[:50]}...' repeated {repetitions} times")
                    return True

            return False

        def detect_low_entropy(text: str, window_size: int = 100) -> bool:
            """Detect low entropy (repetitive) content in recent text"""
            if len(text) < window_size:
                return False

            recent = text[-window_size:]
            unique_ratio = len(set(recent)) / len(recent)

            if unique_ratio < 0.15:  # Less than 15% unique characters
                logger.warning(f"🔄 Low entropy detected! Unique ratio: {unique_ratio:.2f}")
                return True
            return False

        while retry_count <= self.MAX_RETRIES:
            try:
                start = time()
                if len(messages) != 2:
                    raise Exception('len(messages) != 2')

                # Check Cache
                cached_resp = None
                if self.cache_enabled:
                    cached_resp = self._get_from_cache(messages, response_model)
                if cached_resp:
                    res = cached_resp
                    logger.debug("Using cached response")
                else:
                    # Stream the response for logging purposes
                    logger.debug("=" * 70)
                    logger.debug("=" * 31 + " LLM REQ " + "=" * 30)
                    logger.debug("=" * 70)
                    logger.debug("System\n" + messages[0].content)
                    logger.debug("Prompt\n" + messages[1].content)
                    logger.debug("=" * 70)
                    logger.debug("🚀 Starting model inference...")
                    logger.debug("📝 Streaming response:")

                    # Use streaming for real-time monitoring
                    full_response = ""
                    token_count = 0
                    last_log_time = time()
                    last_repetition_check = time()
                    effective_max_tokens = max_tokens if max_tokens and max_tokens > 0 else 8192

                    for chunk in self.client.generate(
                            model=MEDIUM if model_size == ModelSize.medium else SMALL,
                            prompt=messages[1].content,
                            system=messages[0].content,
                            format=response_model.model_json_schema() if response_model else None,
                            stream=True,
                            options={
                                "temperature": 0,
                                "num_ctx": 16384 if model_size == ModelSize.medium else 8192,
                                "num_batch": 64,
                                "top_p": 0.9,
                                "top_k": 40,
                                "repeat_penalty": 1.15,
                                "repeat_last_n": 128,
                                "num_predict": effective_max_tokens,
                                # Add hard token limit
                            }):
                        if 'response' in chunk:
                            full_response += chunk['response']
                            token_count += 1

                            current_time = time()

                            # Safety checks
                            # 1. Hard token limit
                            if token_count >= effective_max_tokens:
                                logger.warning(f"🛑 Reached token limit ({effective_max_tokens})")
                                break

                            # 2. Time limit (10 minutes max)
                            if current_time - start > 1800:
                                logger.warning("🛑 Reached time limit (30 minutes)")
                                break

                            # 3. Check for repetition every 30 seconds or 100 tokens
                            if ((current_time - last_repetition_check > 30.0) or
                                (token_count % 100 == 0)) and len(full_response) > 200:

                                if detect_exact_repetition(full_response) or detect_low_entropy(full_response):
                                    logger.error("🛑 Repetitive loop detected - stopping generation")
                                    raise Exception("Model stuck in repetitive loop")

                                last_repetition_check = current_time

                            # Log progress every 25 seconds or every 100 tokens
                            if (current_time - last_log_time > 25.0) or (token_count % 100 == 0):
                                elapsed = current_time - start
                                tokens_per_sec = token_count / (elapsed + 0.001)

                                logger.debug(f"⏰ {int(elapsed // 60)}m{int(elapsed % 60)}s elapsed | "
                                             f"🔢 {token_count} tokens | "
                                             f"📊 {tokens_per_sec:.1f} tokens/sec")
                                logger.debug(f"📄 Last 1000 chars: ...{full_response[-1000:]}")

                                # Warn if generation is unusually slow or fast
                                if elapsed > 60:  # After 1 minute
                                    if tokens_per_sec < 1:
                                        logger.warning(f"⚠️  Generation very slow: {tokens_per_sec:.1f} tokens/sec")
                                    elif tokens_per_sec > 50:
                                        logger.warning(
                                            f"⚠️  Generation very fast (possible loop): {tokens_per_sec:.1f} tokens/sec")

                                last_log_time = current_time

                    logger.debug(f"✅ Generation complete! Total tokens: {token_count}")

                    # Final safety check
                    if not full_response.strip():
                        raise Exception("Empty response received")

                    # Parse the complete response
                    try:
                        res = json.loads(full_response)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        logger.error(f"Raw response length: {len(full_response)}")
                        logger.error(f"First 500 chars: {full_response[:500]}")
                        logger.error(f"Last 500 chars: {full_response[-500:]}")
                        raise Exception(f"JSON parsing failed: {e}")

                end = time()
                duration = end - start

                logger.debug("=" * 70)
                logger.debug("Response\n" + str(res))
                logger.debug(f'🎯 Ollama response completed in {int(duration // 60)}m{int(duration % 60)}s')

                if not cached_resp:
                    logger.debug("💾 Caching response...")
                    self._save_to_cache(messages, res, response_model)

                logger.debug("=" * 70)
                logger.debug("=" * 70)

                return res

            except Exception as e:
                last_error = e
                retry_count += 1

                if retry_count <= self.MAX_RETRIES:
                    wait_time = min(2 ** retry_count, 30)  # Exponential backoff, max 30s
                    logger.warning(f"🔄 Attempt {retry_count} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ All {self.MAX_RETRIES} attempts failed. Last error: {e}")
                    raise last_error

    def _get_cache_key(self,
                       messages: list[str],
                       response_model: type[BaseModel] | None = None,
                       ) -> str:
        # Create a dictionary with all parameters
        key_data = {
            "system": messages[0],
            "user": messages[1],
            "response_model": response_model.__name__ if response_model else None
        }

        # Convert to JSON string with sorted keys for consistency
        key_string = json.dumps(key_data, sort_keys=True, default=str)

        # Generate SHA256 hash
        return hashlib.sha256(key_string.encode()).hexdigest()

    def _get_from_cache(self,
                        messages: list[Message],
                        response_model: type[BaseModel] | None = None,
                        ) -> dict[str, typing.Any] | None:
        cache_key = self._get_cache_key([m.content for m in messages], response_model)
        if cache_key in self.cache:
            print("✅ Cache hit! Returning cached response.")
            return self.cache[cache_key]
        else:
            return None

    def _save_to_cache(self,
                       messages: list[Message],
                       response: dict[str, typing.Any],
                       response_model: type[BaseModel] | None = None,
                       ) -> None:

        cache_key = self._get_cache_key([m.content for m in messages], response_model)
        self.cache[cache_key] = response


class MinervaEmbeddingClient(EmbedderClient):

    def __init__(self):
        super().__init__()
        self.client = ollama.Client()

    async def create(self, input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]]) -> list[float]:
        result = self.client.embed(SMALL, input_data)
        return list(result.embeddings[0])

    async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
        result = self.client.embed(SMALL, input_data_list)
        return [list(e) for e in result.embeddings]
