"""Base agent class for all CV pipeline agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from loguru import logger

from src.providers.provider_manager import ProviderManager


class AgentConfig(BaseModel):
    """Base configuration for agents."""
    
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000
    system_prompt: Optional[str] = None
    retry_count: int = 3


class BaseAgent(ABC):
    """Abstract base class for all agents in the pipeline."""
    
    name: str = "base_agent"
    default_system_prompt: str = ""
    
    def __init__(
        self,
        provider_manager: ProviderManager,
        config: Optional[AgentConfig] = None,
    ):
        """Initialize agent.
        
        Args:
            provider_manager: Provider manager for LLM access
            config: Agent-specific configuration
        """
        self.provider_manager = provider_manager
        self.config = config or AgentConfig()
        self.system_prompt = self.config.system_prompt or self.default_system_prompt
    
    def _build_messages(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Build message list for LLM.
        
        Args:
            user_message: User's message content
            system_prompt: Optional system prompt override
            
        Returns:
            List of message dicts
        """
        messages = []
        
        system = system_prompt or self.system_prompt
        if system:
            messages.append({"role": "system", "content": system})
        
        messages.append({"role": "user", "content": user_message})
        return messages
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        **kwargs: Any,
    ) -> str:
        """Call LLM with retry logic.
        
        Args:
            messages: Message list
            **kwargs: Additional arguments for provider
            
        Returns:
            LLM response
        """
        last_error = None
        
        for attempt in range(self.config.retry_count):
            try:
                response = await self.provider_manager.chat(
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    **kwargs,
                )
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"{self.name} LLM call failed (attempt {attempt + 1}): {e}")
        
        raise last_error or RuntimeError(f"{self.name} LLM call failed after {self.config.retry_count} attempts")
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the agent's main task.
        
        Returns:
            Agent-specific result
        """
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
