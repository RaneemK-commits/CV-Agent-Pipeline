"""Groq provider implementation for fast LLM inference."""

from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq package not installed. Install with: pip install groq")


class GroqProvider(BaseProvider):
    """Provider for Groq API (fast LLM inference)."""
    
    name = "groq"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not GROQ_AVAILABLE:
            raise ImportError("Groq package not installed")
        
        self.client = AsyncGroq(api_key=config.api_key)
    
    async def initialize(self) -> bool:
        """Verify API key is valid."""
        if not self.config.api_key:
            logger.warning("Groq API key not configured")
            return False
        
        try:
            # Simple test request
            await self.client.models.list()
            self._initialized = True
            logger.info("Groq provider initialized")
            return True
        except Exception as e:
            logger.warning(f"Groq initialization failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Groq client."""
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
        """Send chat completion to Groq."""
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
        """Send completion to Groq (using chat API)."""
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
        """Groq doesn't provide embeddings. Raises NotImplementedError."""
        raise NotImplementedError("Groq does not provide embedding models")
