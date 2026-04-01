"""Provider manager for handling multiple LLM providers."""

from typing import Dict, Optional, List, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig
from src.providers.ollama_provider import OllamaProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.anthropic_provider import AnthropicProvider
from src.providers.groq_provider import GroqProvider
from src.providers.mistral_provider import MistralProvider
from src.providers.mock_provider import MockProvider


class ProviderManager:
    """Manages multiple LLM providers with fallback support."""
    
    PROVIDER_CLASSES = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "groq": GroqProvider,
        "mistral": MistralProvider,
        "mock": MockProvider,
    }
    
    def __init__(self, providers_config: Dict[str, Any], fallback_chain: Optional[List[str]] = None):
        """Initialize provider manager.
        
        Args:
            providers_config: Configuration dict for all providers
            fallback_chain: List of provider names in fallback order
        """
        self.providers: Dict[str, BaseProvider] = {}
        self.fallback_chain = fallback_chain or ["ollama"]
        self._load_providers(providers_config)
    
    def _load_providers(self, config: Dict[str, Any]) -> None:
        """Load and initialize providers from config."""
        for provider_name, provider_config in config.items():
            if provider_name not in self.PROVIDER_CLASSES:
                logger.warning(f"Unknown provider: {provider_name}")
                continue
            
            if not provider_config.get("enabled", False):
                logger.info(f"Provider {provider_name} is disabled")
                continue
            
            try:
                provider_class = self.PROVIDER_CLASSES[provider_name]
                provider_instance = provider_class(ProviderConfig(**provider_config))
                self.providers[provider_name] = provider_instance
                logger.info(f"Loaded provider: {provider_name}")
            except Exception as e:
                logger.warning(f"Failed to load provider {provider_name}: {e}")
    
    async def initialize_all(self) -> List[str]:
        """Initialize all loaded providers.
        
        Returns:
            List of successfully initialized provider names
        """
        available = []
        for name, provider in self.providers.items():
            try:
                if await provider.initialize():
                    available.append(name)
            except Exception as e:
                logger.warning(f"Provider {name} failed to initialize: {e}")
        
        logger.info(f"Available providers: {available}")
        return available
    
    async def close_all(self) -> None:
        """Close all provider connections."""
        for provider in self.providers.values():
            try:
                await provider.close()
            except Exception as e:
                logger.warning(f"Error closing provider: {e}")
    
    def get_provider(self, name: str) -> Optional[BaseProvider]:
        """Get a specific provider by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider instance or None if not available
        """
        provider = self.providers.get(name)
        if provider and provider.is_available():
            return provider
        return None
    
    def get_available_provider(self) -> Optional[BaseProvider]:
        """Get first available provider from fallback chain.
        
        Returns:
            First available provider or None
        """
        for name in self.fallback_chain:
            provider = self.get_provider(name)
            if provider:
                logger.info(f"Using provider: {name}")
                return provider
        
        logger.warning("No providers available in fallback chain")
        return None
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        provider_name: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs: Any,
    ) -> str:
        """Send chat request with optional fallback.
        
        Args:
            messages: Chat messages
            provider_name: Specific provider to use
            use_fallback: Whether to try fallback providers on failure
            **kwargs: Additional arguments for chat method
            
        Returns:
            Generated response
        """
        providers_to_try = []
        
        if provider_name:
            providers_to_try.append(provider_name)
            if use_fallback:
                providers_to_try.extend(self.fallback_chain)
        else:
            providers_to_try = self.fallback_chain
        
        last_error = None
        
        for name in providers_to_try:
            provider = self.get_provider(name)
            if not provider:
                continue
            
            try:
                response = await provider.chat(messages, **kwargs)
                logger.debug(f"Successful response from provider: {name}")
                return response
            except Exception as e:
                logger.warning(f"Provider {name} failed: {e}")
                last_error = e
        
        if last_error:
            raise last_error
        raise RuntimeError("No providers available")
    
    async def complete(
        self,
        prompt: str,
        provider_name: Optional[str] = None,
        use_fallback: bool = True,
        **kwargs: Any,
    ) -> str:
        """Send completion request with optional fallback.
        
        Args:
            prompt: Text prompt
            provider_name: Specific provider to use
            use_fallback: Whether to try fallback providers on failure
            **kwargs: Additional arguments for complete method
            
        Returns:
            Generated response
        """
        providers_to_try = []
        
        if provider_name:
            providers_to_try.append(provider_name)
            if use_fallback:
                providers_to_try.extend(self.fallback_chain)
        else:
            providers_to_try = self.fallback_chain
        
        last_error = None
        
        for name in providers_to_try:
            provider = self.get_provider(name)
            if not provider:
                continue
            
            try:
                response = await provider.complete(prompt, **kwargs)
                logger.debug(f"Successful response from provider: {name}")
                return response
            except Exception as e:
                logger.warning(f"Provider {name} failed: {e}")
                last_error = e
        
        if last_error:
            raise last_error
        raise RuntimeError("No providers available")
    
    async def embed(
        self,
        text: str,
        provider_name: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings.
        
        Args:
            text: Text to embed
            provider_name: Specific provider to use
            **kwargs: Additional arguments for embed method
            
        Returns:
            Embedding vector
        """
        if provider_name:
            provider = self.get_provider(provider_name)
            if provider:
                return await provider.embed(text, **kwargs)
        
        # Try providers in fallback chain
        for name in self.fallback_chain:
            provider = self.get_provider(name)
            if not provider:
                continue
            
            try:
                return await provider.embed(text, **kwargs)
            except NotImplementedError:
                continue
            except Exception as e:
                logger.warning(f"Provider {name} embed failed: {e}")
        
        raise RuntimeError("No embedding provider available")
