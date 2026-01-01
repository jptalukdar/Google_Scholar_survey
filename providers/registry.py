from typing import Dict, Type, TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from .provider import Provider

class ProviderRegistry:
    _providers: Dict[str, Type['Provider']] = {}
    _empty_provider: Type['Provider'] = None

    @classmethod
    def register(cls, domain: str):
        def decorator(provider_class):
            cls._providers[domain] = provider_class
            return provider_class
        return decorator
    
    @classmethod
    def register_empty(cls, provider_class):
        cls._empty_provider = provider_class
        return provider_class

    @classmethod
    def get_provider_class(cls, url: str) -> Type['Provider']:
        domain = urlparse(url).netloc
        # Handle subdomains or variations if needed, for now exact match on netloc
        # or simplified matching
        
        # Try exact match
        if domain in cls._providers:
            return cls._providers[domain]
            
        # Try removing www.
        if domain.startswith("www."):
            base_domain = domain[4:]
            if base_domain in cls._providers:
                return cls._providers[base_domain]

        return cls._empty_provider
