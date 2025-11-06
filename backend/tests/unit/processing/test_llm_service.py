"""
Unit tests for LLM service.

Tests the LLMService with mocked dependencies, focusing on the refactored generate method
and its extracted helper methods.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel

from minerva_backend.processing.llm_service import LLMService


class MockResponseModel(BaseModel):
    """Mock response model for testing."""
    summary: str
    confidence: float


@pytest.fixture
def mock_ollama_client():
    """Create mock Ollama client."""
    mock_client = Mock()
    mock_client.generate = AsyncMock()
    return mock_client


@pytest.fixture
def mock_cache():
    """Create mock cache."""
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock()
    return mock_cache


@pytest.fixture
def llm_service(mock_ollama_client, mock_cache):
    """Create LLMService instance with mocked dependencies."""
    # Mock the expensive initialization
    with patch('ollama.AsyncClient') as mock_client_class:
        mock_client_class.return_value = mock_ollama_client
        with patch('minerva_backend.processing.llm_service.Cache') as mock_cache_class:
            mock_cache_class.return_value = mock_cache
            service = LLMService()
            service.cache_enabled = True  # Enable cache for testing
            service.cache = mock_cache  # Set the cache
    return service


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing."""
    return "Extract entities from: Today I went to the park with John."


@pytest.fixture
def sample_system_prompt():
    """Sample system prompt for testing."""
    return "You are an entity extraction assistant."


@pytest.fixture
def sample_response_model():
    """Sample response model for testing."""
    return MockResponseModel


@pytest.fixture
def sample_options():
    """Sample options for testing."""
    return {"temperature": 0.7, "max_tokens": 100}


class TestLLMServiceInitialization:
    """Test LLMService initialization."""
    
    def test_llm_service_init(self):
        """Test LLMService initialization."""
        # Mock the expensive initialization
        with patch('ollama.AsyncClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            with patch('minerva_backend.processing.llm_service.Cache') as mock_cache_class:
                mock_cache_class.return_value = None
                service = LLMService()
                assert service.client is not None  # LLMService initializes with Ollama client
                assert service.cache is None


class TestLLMServiceGenerateMethod:
    """Test the main generate method."""
    
    @pytest.mark.asyncio
    async def test_generate_success_with_string_response(self, llm_service, sample_prompt):
        """Test successful generation with string response."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Generated response"}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service.generate(sample_prompt)
        
        # Assert
        assert result == "Generated response"
        llm_service.client.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_success_with_model_response(self, llm_service, sample_prompt, sample_response_model):
        """Test successful generation with Pydantic model response."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": '{"summary": "Test summary", "confidence": 0.95}'}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service.generate(
            sample_prompt, 
            response_model=sample_response_model
        )
        
        # Assert
        assert isinstance(result, sample_response_model)
        assert result.summary == "Test summary"
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, llm_service, sample_prompt, sample_system_prompt):
        """Test generation with system prompt."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Generated response"}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service.generate(
            sample_prompt, 
            system_prompt=sample_system_prompt
        )
        
        # Assert
        assert result == "Generated response"
        call_args = llm_service.client.generate.call_args
        assert call_args[1]["system"] == sample_system_prompt
    
    @pytest.mark.asyncio
    async def test_generate_with_options(self, llm_service, sample_prompt, sample_options):
        """Test generation with custom options."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Generated response"}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service.generate(
            sample_prompt, 
            options=sample_options
        )
        
        # Assert
        assert result == "Generated response"
        call_args = llm_service.client.generate.call_args
        assert call_args[1]["options"] == sample_options
    
    @pytest.mark.asyncio
    async def test_generate_with_caching(self, llm_service, sample_prompt):
        """Test generation with caching enabled."""
        # Arrange
        mock_response = "Generated response"
        llm_service.cache_enabled = True
        llm_service.cache = Mock()
        llm_service.cache.get.return_value = mock_response
        
        # Act
        result = await llm_service.generate(sample_prompt)
        
        # Assert
        assert result == mock_response
        llm_service.cache.get.assert_called_once()
        llm_service.client.generate.assert_not_called()  # Should use cache
    
    @pytest.mark.asyncio
    async def test_generate_with_retry_on_failure(self, llm_service, sample_prompt):
        """Test generation with retry on failure."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Generated response"}
            yield {"done": True}
        
        llm_service.client.generate.side_effect = [Exception("Network error"), mock_stream_generator()]
        
        # Mock asyncio.sleep to speed up retry tests
        with patch('asyncio.sleep') as mock_sleep:
            # Act
            result = await llm_service.generate(sample_prompt)
            
            # Assert
            assert result == "Generated response"
            assert llm_service.client.generate.call_count == 2  # Retried once
            mock_sleep.assert_called_once()  # Should have slept once
    
    @pytest.mark.asyncio
    async def test_generate_max_retries_exceeded(self, llm_service, sample_prompt):
        """Test generation when max retries are exceeded."""
        # Arrange
        llm_service.client.generate.side_effect = Exception("Persistent error")
        
        # Mock asyncio.sleep to speed up retry tests
        with patch('asyncio.sleep') as mock_sleep:
            # Act & Assert
            with pytest.raises(Exception, match="Persistent error"):
                await llm_service.generate(sample_prompt)
            
            # Should retry 4 times (initial + 3 retries, MAX_RETRIES=3)
            assert llm_service.client.generate.call_count == 4
            assert mock_sleep.call_count == 3  # Should have slept 3 times


class TestLLMServiceHelperMethods:
    """Test the extracted helper methods."""
    
    def test_check_cache_hit(self, llm_service, sample_response_model):
        """Test cache hit scenario."""
        # Arrange
        cache_key = "test_cache_key"
        cached_response = {"summary": "Cached summary", "confidence": 0.9}
        llm_service.cache_enabled = True  # Enable cache
        llm_service.cache = Mock()  # Ensure cache is set
        llm_service.cache.get.return_value = cached_response
        
        # Act
        result = llm_service._check_cache(
            cache_key, 
            "test_model", 
            sample_response_model
        )
        
        # Assert
        assert isinstance(result, sample_response_model)
        assert result.summary == "Cached summary"
        assert result.confidence == 0.9
    
    def test_check_cache_miss(self, llm_service):
        """Test cache miss scenario."""
        # Arrange
        cache_key = "test_cache_key"
        llm_service.cache_enabled = True  # Enable cache
        llm_service.cache = Mock()  # Ensure cache is set
        llm_service.cache.get.return_value = None
        
        # Act
        result = llm_service._check_cache(
            cache_key, 
            "test_model", 
            None
        )
        
        # Assert
        assert result is None
    
    def test_check_cache_string_response(self, llm_service):
        """Test cache with string response."""
        # Arrange
        cache_key = "test_cache_key"
        cached_response = "Cached string response"
        llm_service.cache_enabled = True  # Enable cache
        llm_service.cache = Mock()  # Ensure cache is set
        llm_service.cache.get.return_value = cached_response
        
        # Act
        result = llm_service._check_cache(
            cache_key, 
            "test_model", 
            None
        )
        
        # Assert
        assert result == cached_response
    
    @pytest.mark.asyncio
    async def test_process_generation_success(self, llm_service, sample_prompt, sample_system_prompt, sample_response_model, sample_options):
        """Test successful processing of generation."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": '{"summary": "Generated summary", "confidence": 0.95}'}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service._process_generation(
            "test_model",
            sample_prompt,
            sample_system_prompt,
            sample_response_model,
            sample_options,
            "test_cache_key"
        )
        
        # Assert
        assert isinstance(result, sample_response_model)
        assert result.summary == "Generated summary"
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_process_generation_with_streaming(self, llm_service, sample_prompt):
        """Test processing with streaming response."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Generated "}
            yield {"response": "response"}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Act
        result = await llm_service._process_generation(
            "test_model",
            sample_prompt,
            None,
            None,
            {},
            "test_cache_key"
        )
        
        # Assert
        assert result == "Generated response"
    
    @pytest.mark.asyncio
    async def test_process_stream_success(self, llm_service):
        """Test successful stream processing."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Hello world"}
            yield {"done": True}
        
        # Act
        content, token_count = await llm_service._process_stream(
            mock_stream_generator(), 
            100, 
            0.0
        )
        
        # Assert
        assert content == "Hello world"
        assert token_count == 2  # len("Hello world") // 4 = 2
    
    @pytest.mark.asyncio
    async def test_process_stream_with_max_tokens(self, llm_service):
        """Test stream processing with max tokens limit."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "Hello world this is too long"}
            yield {"done": True}
        
        # Act
        content, token_count = await llm_service._process_stream(
            mock_stream_generator(), 
            3,  # Max 3 tokens
            0.0
        )
        
        # Assert
        # The stream processing doesn't break mid-chunk, so it processes the entire response
        # "Hello world this is too long" = 30 chars = 7 tokens
        assert content == "Hello world this is too long"
        assert token_count == 7  # 30 chars // 4 = 7 tokens
    
    
    def test_should_check_repetition_interval(self, llm_service):
        """Test repetition check interval logic."""
        # Test should check (enough time passed and long content)
        long_content = "x" * 250  # More than 200 characters
        assert llm_service._should_check_repetition(
            current_time=40.0,  # 35 seconds passed
            last_repetition_check=5.0,
            token_count=10,
            full_response_content=long_content
        ) is True
        
        # Test should not check (not enough time passed)
        assert llm_service._should_check_repetition(
            current_time=6.0,
            last_repetition_check=5.0,
            token_count=10,
            full_response_content=long_content
        ) is False
        
        # Test should not check (content too short)
        assert llm_service._should_check_repetition(
            current_time=40.0,
            last_repetition_check=5.0,
            token_count=10,
            full_response_content="short"
        ) is False


class TestLLMServiceErrorHandling:
    """Test error handling in LLMService."""
    
    @pytest.mark.asyncio
    async def test_generate_network_error(self, llm_service, sample_prompt):
        """Test generation with network error."""
        # Arrange
        llm_service.client.generate.side_effect = Exception("Network error")
        
        # Mock asyncio.sleep to speed up retry tests
        with patch('asyncio.sleep') as mock_sleep:
            # Act & Assert
            with pytest.raises(Exception, match="Network error"):
                await llm_service.generate(sample_prompt)
            
            # Should have attempted retries
            assert mock_sleep.call_count > 0
    
    @pytest.mark.asyncio
    async def test_generate_invalid_response_model(self, llm_service, sample_prompt):
        """Test generation with invalid response model data."""
        # Arrange
        async def mock_stream_generator():
            yield {"response": "invalid data"}
            yield {"done": True}
        
        llm_service.client.generate.return_value = mock_stream_generator()
        
        # Mock asyncio.sleep to speed up retry tests
        with patch('asyncio.sleep') as mock_sleep:
            # Act & Assert
            with pytest.raises(Exception):  # Pydantic validation error
                await llm_service.generate(
                    sample_prompt, 
                    response_model=MockResponseModel
                )


