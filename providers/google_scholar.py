from functools import cache
import json
import os
import requests
import hashlib
from typing import Tuple

from .provider import Provider, SEARCH_DIR, RESULTS_DIR, DefaultEncoder
from .registry import ProviderRegistry
from .emptyprovider import EmptyProvider

class GoogleScholarProvider(Provider):
    def parse_results(self, entry, download=False):
        title = entry.find("h3", class_="gs_rt").text
        url = (
            entry.find("h3", class_="gs_rt").a["href"]
            if entry.find("h3", class_="gs_rt") is not None
            else None
        )
        gg_ = entry.find("div", class_="gs_or_ggsm")
        download_link = gg_.a["href"] if gg_ is not None else None
        author = entry.find("div", class_="gs_a").text
        snippet = (
            entry.find("div", class_="gs_rs").text
            if entry.find("div", class_="gs_rs") is not None
            else None
        )
        
        # We need to resolve the provider for the paper URL
        # This used to be a recursive call to parse_provider, now we use Registry
        try:
            # Import here to avoid circular dependency if ProviderRegistry uses this file
            # But ProviderRegistry is separate now
            provider_class = ProviderRegistry.get_provider_class(url)
            provider = provider_class(url, cache=True)
        except Exception as e:
            print(f"Error in {url}: {e}")
            provider = EmptyProvider(url, cache=True)
        
        return {
            "title": title,
            "author": author,
            "url": url,
            "download_url": download_link,
            "snippet": snippet,
            "provider": provider.__class__.__name__,
            "provider_class": str(provider),
            "abstract": provider.get_abstract(),
        }

    def save_results(self, res):
        url_hash = self.get_url_hash()
        cache_file = os.path.join(
            SEARCH_DIR, f"{self.__class__.__name__}_{url_hash}.json"
        )
        with open(cache_file, "w") as f:
            json.dump(res, f, indent=4, cls=DefaultEncoder)

    def get_all_papers(self, logger=None, download=False):
        # Note: This method was originally doing too much (printing, saving, downloading)
        # We will simplify it to just yield results, and let the caller handle the rest
        # But to maintain some compatibility or logic, we'll return a list
        
        papers = []
        if not self.soup:
            return papers
            
        for entry in self.soup.find_all("div", class_="gs_r gs_or gs_scl"):
            try:
                res = self.parse_results(entry)
                
                # We can save individual paper results here if we want
                # Or let the engine handle it. The original code saved it immediately.
                
                # Original: parse_results_saver(res)
                # We'll adapt that logic here or in the caller. 
                # For now, let's return the dict.
                
                papers.append(res)
                
                if logger:
                    logger.info(f"Found: {res['title']}")
                
            except Exception as e:
                if logger:
                    logger.error(f"Error parsing entry: {e}")
                else:
                    print(f"Error parsing entry: {e}")
                    
        return papers

