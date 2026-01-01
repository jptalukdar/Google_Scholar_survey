import json
import os
from typing import List, Optional
from core.config import JOBS_DIR
from .job import Job, JobStatus
from providers.provider import DefaultEncoder

class JobStorage:
    @staticmethod
    def _get_job_dir(job_id: str) -> str:
        return os.path.join(JOBS_DIR, job_id)

    @staticmethod
    def _get_metadata_path(job_id: str) -> str:
        return os.path.join(JobStorage._get_job_dir(job_id), "metadata.json")
    
    @staticmethod
    def _get_results_path(job_id: str) -> str:
        return os.path.join(JobStorage._get_job_dir(job_id), "results.json")

    @staticmethod
    def save_job(job: Job):
        job_dir = JobStorage._get_job_dir(job.id)
        os.makedirs(job_dir, exist_ok=True)
        
        with open(JobStorage._get_metadata_path(job.id), "w") as f:
            json.dump(job.to_dict(), f, indent=4)

    @staticmethod
    def load_job(job_id: str) -> Optional[Job]:
        path = JobStorage._get_metadata_path(job_id)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r") as f:
                data = json.load(f)
            return Job.from_dict(data)
        except Exception:
            return None

    @staticmethod
    def list_jobs() -> List[Job]:
        jobs = []
        if not os.path.exists(JOBS_DIR):
            return []
            
        for job_id in os.listdir(JOBS_DIR):
            job = JobStorage.load_job(job_id)
            if job:
                jobs.append(job)
        
        # Sort by creation time, newest first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    @staticmethod
    def save_results(job_id: str, results: List[dict]):
        job_dir = JobStorage._get_job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        with open(JobStorage._get_results_path(job_id), "w") as f:
            json.dump(results, f, indent=4, cls=DefaultEncoder)

    @staticmethod
    def get_results(job_id: str) -> List[dict]:
        path = JobStorage._get_results_path(job_id)
        if not os.path.exists(path):
            return []
        
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []
