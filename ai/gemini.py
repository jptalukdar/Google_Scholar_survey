from typing import List, Optional
from .base import LLMProvider, ChatMessage

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using google-genai SDK."""
    
    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest"):
        self.api_key = api_key
        self.model = model
        self.client = None
        
        if GENAI_AVAILABLE and api_key:
            self.client = genai.Client(api_key=api_key)

    def is_available(self) -> bool:
        return GENAI_AVAILABLE and self.client is not None and bool(self.api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini provider is not available. Check API key and google-genai installation.")
        
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        
        return response.text

    def chat(self, messages: List[ChatMessage]) -> str:
        if not self.is_available():
            raise RuntimeError("Gemini provider is not available. Check API key and google-genai installation.")
        
        # Convert to genai format
        contents = []
        system_prompt = None
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                role = "user" if msg.role == "user" else "model"
                contents.append(types.Content(role=role, parts=[types.Part(text=msg.content)]))
        
        config = None
        if system_prompt:
            config = types.GenerateContentConfig(system_instruction=system_prompt)
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )
        
        return response.text
