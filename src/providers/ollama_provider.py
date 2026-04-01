"""Ollama provider implementation for local LLM inference."""

import httpx
from typing import Optional, List, Dict, Any
from loguru import logger

from src.providers.base_provider import BaseProvider, ProviderConfig


class OllamaProvider(BaseProvider):
    """Provider for Ollama local LLM runtime."""
    
    name = "ollama"
    
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=60.0)
    
    async def initialize(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            response = await self.client.get("/api/tags")
            if response.status_code == 200:
                self._initialized = True
                logger.info(f"Ollama connected at {self.base_url}")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available at {self.base_url}: {e}")
        return False
    
    async def close(self) -> None:
        """Close HTTP client."""
        await self.client.aclose()
        self._initialized = False
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send chat completion to Ollama."""
        model = self.get_model(model)
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        response = await self.client.post("/api/chat", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["message"]["content"]
    
    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """Send text completion to Ollama."""
        model = self.get_model(model)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        response = await self.client.post("/api/generate", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["response"]
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
        **kwargs: Any,
    ) -> List[float]:
        """Generate embeddings using Ollama."""
        model = model or self.config.embedding_model or "nomic-embed-text"
        
        payload = {
            "model": model,
            "prompt": text,
        }
        
        response = await self.client.post("/api/embeddings", json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result["embedding"]
