"""Base provider interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os


class ProviderConfig(BaseModel):
    """Configuration for a provider."""
    
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    default_model: str = Field(..., description="Default model to use")
    api_key_env: Optional[str] = Field(None, description="Environment variable for API key")
    base_url: Optional[str] = Field(None, description="Base URL for API (for local providers)")
    embedding_model: Optional[str] = Field(None, description="Model for embeddings")
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment."""
        if self.api_key_env:
            return os.getenv(self.api_key_env)
        return None


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str = "base"
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._initialized = False
    
    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send a text completion request.
        
        Args:
            prompt: Text prompt for completion
            model: Model to use (overrides default)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific arguments
            
        Returns:
            Generated text response
        """
        pass
    
    @abstractmethod
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings for text.
        
        Args:
            text: Text to embed
            model: Embedding model to use
            **kwargs: Additional provider-specific arguments
            
        Returns:
            List of embedding values
        """
        pass
    
    async def initialize(self) -> bool:
        """Initialize the provider connection.
        
        Returns:
            True if initialization successful
        """
        self._initialized = True
        return True
    
    async def close(self) -> None:
        """Close provider connections."""
        self._initialized = False
    
    def is_available(self) -> bool:
        """Check if provider is available.
        
        Returns:
            True if provider is configured and ready
        """
        if not self.config.enabled:
            return False
        if self.config.api_key_env and not self.config.api_key:
            return False
        return True
    
    def get_model(self, model: Optional[str] = None) -> str:
        """Get model name, using default if not specified.
        
        Args:
            model: Model name or None to use default
            
        Returns:
            Model name to use
        """
        return model or self.config.default_model
