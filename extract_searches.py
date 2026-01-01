import os
import json
import hashlib
from typing import List, Callable, Optional
from string import Template

from core.config import RESULTS_DIR, DOWNLOAD_DIR
from core.logging import JobLogger
from workers.job import JobConfig

from providers import GoogleScholarProvider, ProviderRegistry, DefaultEncoder
from providers.provider import Provider

class SearchEngine:
    def __init__(self):
        pass

    def search(self, query: str, config: JobConfig, 
               progress_callback: Callable[[float, int], None] = None,
               stop_check: Callable[[], bool] = None,
               logger: JobLogger = None) -> List[dict]:
        """
        Execute a search query and return results.
        params:
            progress_callback: function(progress: float, count: int)
            stop_check: function() -> bool. If returns True, stop search.
        """
        if logger:
            logger.info(f"Starting search for: {query}")

        # Handle site restrictions
        full_query = query
        if config.sites:
            site_query = " OR ".join([f"site:{site}" for site in config.sites])
            full_query = f"{query} {site_query}"
            if logger:
                logger.info(f"Modified query with site restrictions: {full_query}")

        query_formatted = full_query.replace(" ", "+")
        base_url = "https://scholar.google.com/scholar?start=$index&q=$query&hl=en&as_sdt=0,5&as_ylo=$since_year&as_vis=1"
        
        all_papers = []
        total_steps = (config.max_results - config.start) // config.step
        # avoid division by zero
        if total_steps < 1: total_steps = 1
        
        current_step = 0
        
        for i in range(config.start, config.max_results, config.step):
            # Check for cancellation
            if stop_check and stop_check():
                if logger:
                    logger.info("Search cancelled by user.")
                break

            url = Template(base_url).substitute(
                index=i, 
                query=query_formatted, 
                since_year=config.since_year
            )
            
            if logger:
                logger.info(f"Fetching page {current_step+1}/{total_steps}: {url}")
            
            try:
                # Use GoogleScholarProvider to fetch search results
                provider = GoogleScholarProvider(url, cache=True)
                papers = provider.get_all_papers(logger=logger)
                
                for paper in papers:
                    # Save individual result (compatibility with old logic)
                    self._save_result(paper)
                    
                    # Store in list
                    all_papers.append(paper)
                    
                    # Download PDF if requested
                    if config.download_pdfs and paper.get("download_url"):
                        self._handle_download(paper, logger)

                # Update progress
                current_step += 1
                if progress_callback:
                    progress_callback(current_step / total_steps, len(all_papers))
                    
            except Exception as e:
                if logger:
                    logger.error(f"Error processing batch starting at {i}: {e}")
        
        if logger:
            logger.info(f"Search completed. Found {len(all_papers)} papers.")
            
        return all_papers

    def _save_result(self, res: dict):
        # This matches the old parse_results_saver logic
        url_hash = hashlib.md5(res["url"].encode()).hexdigest()
        cache_file = os.path.join(RESULTS_DIR, f"{res['provider']}_{url_hash}.json")
        with open(cache_file, "w") as f:
            json.dump(res, f, indent=4, cls=DefaultEncoder)

    def _handle_download(self, res: dict, logger: Optional[JobLogger]):
        title = res["title"]
        url = res["download_url"]
        
        if not url:
            return

        try:
            # Determine provider for download
            # We can use the provider instance in res['provider_class'] if available
            # Or assume we need to use the static methods on the class based on domain
            
            provider_class = ProviderRegistry.get_provider_class(url)
            
            if logger:
                logger.info(f"Attempting download: {title}")
                
            ok, path = provider_class.download_pdf(title, url)
            
            if ok and logger:
                logger.info(f"Downloaded to {path}")
            elif not ok and logger:
                logger.warning(f"Failed download: {title}")
                
        except Exception as e:
            if logger:
                logger.error(f"Download error for {url}: {e}")
