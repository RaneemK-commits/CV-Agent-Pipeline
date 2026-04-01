"""Mistral provider implementation."""

from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig

try:
    from mistralai.async_client import MistralAsyncClient
    MISTRAL_AVAILABLE = True
except ImportError:
    MISTRAL_AVAILABLE = False
    logger.warning("Mistral package not installed. Install with: pip install mistralai")


class MistralProvider(BaseProvider):
    """Provider for Mistral AI API."""
    
    name = "mistral"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not MISTRAL_AVAILABLE:
            raise ImportError("Mistral package not installed")
        
        self.client = MistralAsyncClient(api_key=config.api_key)
    
    async def initialize(self) -> bool:
        """Verify API key is valid."""
        if not self.config.api_key:
            logger.warning("Mistral API key not configured")
            return False
        
        try:
            # Simple test request
            await self.client.list_models()
            self._initialized = True
            logger.info("Mistral provider initialized")
            return True
        except Exception as e:
            logger.warning(f"Mistral initialization failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Mistral client."""
        self._initialized = False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send chat completion to Mistral."""
        model = self.get_model(model)
        
        response = await self.client.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        return response.choices[0].message.content
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send completion to Mistral (using chat API)."""
        model = self.get_model(model)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.chat(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        
        return response.choices[0].message.content
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings using Mistral."""
        model = model or "mistral-embed"
        
        response = await self.client.embeddings(
            model=model,
            input=text,
            **kwargs,
        )
        
        return response.data[0].embedding
