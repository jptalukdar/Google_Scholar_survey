from typing import List, Optional
from .base import LLMProvider, ChatMessage

class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider. (Stub implementation)"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        # TODO: Implement OpenAI SDK integration

    def is_available(self) -> bool:
        # TODO: Check API key validity
        return False

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError("OpenAI provider not yet implemented")

    def chat(self, messages: List[ChatMessage]) -> str:
        raise NotImplementedError("OpenAI provider not yet implemented")
