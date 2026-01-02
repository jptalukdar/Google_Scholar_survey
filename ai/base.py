from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ChatMessage:
    role: str  # "user" or "assistant" or "system"
    content: str

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a text completion from a single prompt."""
        pass
    
    @abstractmethod
    def chat(self, messages: List[ChatMessage]) -> str:
        """Generate a response from a multi-turn conversation."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is configured and available."""
        pass
