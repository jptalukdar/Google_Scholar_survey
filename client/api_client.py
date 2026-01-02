import requests
import json
from typing import List, Dict, Optional, Any
import os

# Import schemas for typing (optional but good for IDE)
# from shared.schemas import ... 

class ApiClient:
    """Client for SLR Worker API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def get_health(self) -> bool:
        try:
            resp = requests.get(self._url("/health"), timeout=2)
            return resp.status_code == 200
        except:
            return False

    # --- Job Management ---

    def submit_job(self, query: str, max_results: int = 20, 
                  since_year: int = 2020, sites: List[str] = None, 
                  download_pdfs: bool = False) -> str:
        
        payload = {
            "query": query,
            "max_results": max_results,
            "since_year": since_year,
            "sites": sites or [],
            "download_pdfs": download_pdfs
        }
        resp = requests.post(self._url("/jobs"), json=payload)
        resp.raise_for_status()
        return resp.json()["id"]

    def list_jobs(self) -> List[Dict]:
        resp = requests.get(self._url("/jobs"))
        resp.raise_for_status()
        return resp.json()

    def get_job(self, job_id: str) -> Optional[Dict]:
        try:
            resp = requests.get(self._url(f"/jobs/{job_id}"))
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException:
            return None

    def cancel_job(self, job_id: str) -> bool:
        resp = requests.post(self._url(f"/jobs/{job_id}/cancel"))
        if resp.status_code == 200:
            return resp.json().get("success", False)
        return False

    # --- SLR Workflow ---

    def generate_questions(self, abstract: str, api_key: str, provider: str = "gemini") -> Dict:
        payload = {
            "abstract": abstract,
            "api_key": api_key,
            "provider": provider
        }
        resp = requests.post(self._url("/slr/generate-questions"), json=payload)
        resp.raise_for_status()
        return resp.json()

    def refine_questions(self, current_questions: Dict, feedback: str, api_key: str, provider: str = "gemini") -> Dict:
        payload = {
            "current_questions": current_questions,  # Expects matching schema
            "feedback": feedback,
            "api_key": api_key,
            "provider": provider
        }
        resp = requests.post(self._url("/slr/refine-questions"), json=payload)
        resp.raise_for_status()
        return resp.json()

    def generate_queries(self, questions: Dict, sites: List[str], api_key: str, provider: str = "gemini") -> List[Dict]:
        payload = {
            "questions": questions,
            "sites": sites or [],
            "api_key": api_key,
            "provider": provider
        }
        resp = requests.post(self._url("/slr/generate-queries"), json=payload)
        resp.raise_for_status()
        return resp.json()["queries"]

    def filter_relevance(self, papers: List[Dict], questions: List[str], threshold: int, api_key: str, provider: str = "gemini") -> Dict:
        payload = {
            "papers": papers,
            "questions": questions,
            "threshold": threshold,
            "api_key": api_key,
            "provider": provider
        }
        resp = requests.post(self._url("/slr/filter-relevance"), json=payload)
        resp.raise_for_status()
        return resp.json()  # {included: [], excluded: []}

    def download_pdfs(self, papers: List[Dict], workflow_id: str) -> Optional[str]:
        payload = {
            "papers": papers,
            "workflow_id": workflow_id
        }
        resp = requests.post(self._url("/slr/download-pdfs"), json=payload)
        resp.raise_for_status()
        data = resp.json()
        if data.get("success"):
            return data.get("zip_path")
        return None
