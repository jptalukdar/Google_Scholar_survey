from typing import List, Optional
from .base import LLMProvider, ChatMessage

class OllamaProvider(LLMProvider):
    """Ollama LLM provider for local models. (Stub implementation)"""
    
    def __init__(self, model: str = "llama2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        # TODO: Implement Ollama REST API integration

    def is_available(self) -> bool:
        # TODO: Check if Ollama server is running
        return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError("Ollama provider not yet implemented")

    def chat(self, messages: List[ChatMessage]) -> str:
        raise NotImplementedError("Ollama provider not yet implemented")
