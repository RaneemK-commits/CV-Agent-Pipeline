"""Anthropic provider implementation."""

from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic package not installed. Install with: pip install anthropic")


class AnthropicProvider(BaseProvider):
    """Provider for Anthropic API (Claude models)."""
    
    name = "anthropic"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not installed")
        
        self.client = AsyncAnthropic(api_key=config.api_key)
    
    async def initialize(self) -> bool:
        """Verify API key is valid."""
        if not self.config.api_key:
            logger.warning("Anthropic API key not configured")
            return False
        
        try:
            # Simple test - count tokens
            await self.client.messages.count_tokens(
                model=self.config.default_model,
                messages=[{"role": "user", "content": "test"}]
            )
            self._initialized = True
            logger.info("Anthropic provider initialized")
            return True
        except Exception as e:
            logger.warning(f"Anthropic initialization failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close Anthropic client."""
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
        """Send message to Claude."""
        model = self.get_model(model)
        
        # Convert OpenAI format to Anthropic format
        system_messages = [m for m in messages if m["role"] == "system"]
        other_messages = [m for m in messages if m["role"] != "system"]
        
        system_prompt = "\n".join([m["content"] for m in system_messages]) if system_messages else None
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens or 2000,
            system=system_prompt,
            messages=other_messages,
            temperature=temperature,
            **kwargs,
        )
        
        return response.content[0].text
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send completion to Claude."""
        model = self.get_model(model)
        
        response = await self.client.messages.create(
            model=model,
            max_tokens=max_tokens or 2000,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            **kwargs,
        )
        
        return response.content[0].text
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Anthropic doesn't provide embeddings. Raises NotImplementedError."""
        raise NotImplementedError("Anthropic does not provide embedding models")
