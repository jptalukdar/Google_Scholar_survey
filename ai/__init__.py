from typing import Optional
from .base import LLMProvider, ChatMessage
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

def get_provider(provider_name: str, api_key: Optional[str] = None, **kwargs) -> LLMProvider:
    """Factory function to get an LLM provider by name."""
    
    providers = {
        "gemini": lambda: GeminiProvider(api_key=api_key, **kwargs),
        "ollama": lambda: OllamaProvider(**kwargs),
        "openai": lambda: OpenAIProvider(api_key=api_key, **kwargs),
    }
    
    if provider_name.lower() not in providers:
        raise ValueError(f"Unknown provider: {provider_name}. Available: {list(providers.keys())}")
    
    return providers[provider_name.lower()]()

__all__ = [
    "LLMProvider",
    "ChatMessage", 
    "GeminiProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "get_provider"
]
