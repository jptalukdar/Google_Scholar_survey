from .registry import ProviderRegistry
from .provider import Provider, DefaultEncoder
from .emptyprovider import EmptyProvider

from .sciencedirect import ScienceDirectProvider
from .arxiv import ArxivProvider
from .ieeexplore import IEEEXplore
from .springer import SpringerProvider
from .multi_providers import Wiley, Frontiers, MDPI
from .acm import ACMProvider
from .google_scholar import GoogleScholarProvider

# Register Providers
ProviderRegistry.register("www.sciencedirect.com")(ScienceDirectProvider)
ProviderRegistry.register("arxiv.org")(ArxivProvider)
ProviderRegistry.register("ieeexplore.ieee.org")(IEEEXplore)
ProviderRegistry.register("link.springer.com")(SpringerProvider)
ProviderRegistry.register("www.mdpi.com")(MDPI)
ProviderRegistry.register("onlinelibrary.wiley.com")(Wiley)
ProviderRegistry.register("www.frontiersin.org")(Frontiers)
ProviderRegistry.register("dl.acm.org")(ACMProvider)
ProviderRegistry.register("scholar.google.com")(GoogleScholarProvider) 

ProviderRegistry.register_empty(EmptyProvider)
