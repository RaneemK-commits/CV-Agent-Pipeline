"""OpenAI provider implementation."""

from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI package not installed. Install with: pip install openai")


class OpenAIProvider(BaseProvider):
    """Provider for OpenAI API."""
    
    name = "openai"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed")
        
        self.client = AsyncOpenAI(api_key=config.api_key)
    
    async def initialize(self) -> bool:
        """Verify API key is valid."""
        if not self.config.api_key:
            logger.warning("OpenAI API key not configured")
            return False
        
        try:
            # Simple test request
            await self.client.models.list()
            self._initialized = True
            logger.info("OpenAI provider initialized")
            return True
        except Exception as e:
            logger.warning(f"OpenAI initialization failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close OpenAI client."""
        await self.client.close()
        self._initialized = False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send chat completion to OpenAI."""
        model = self.get_model(model)
        
        response = await self.client.chat.completions.create(
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
        """Send completion to OpenAI (using chat API)."""
        model = self.get_model(model)
        
        messages = [{"role": "user", "content": prompt}]
        
        response = await self.client.chat.completions.create(
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
        """Generate embeddings using OpenAI."""
        model = model or self.config.embedding_model or "text-embedding-3-small"
        
        response = await self.client.embeddings.create(
            model=model,
            input=text,
            **kwargs,
        )
        
        return response.data[0].embedding
