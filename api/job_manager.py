import uuid
from datetime import datetime
from typing import List, Iterator, Optional, Dict
import os

from core.logging import JobLogger, LogStream
from core.config import JOBS_DIR
from workers.job import Job, JobConfig, JobStatus
from workers.job_storage import JobStorage
from workers.worker_pool import WorkerPool

class JobManager:
    """Main entry point for job submission and management."""
    
    def __init__(self):
        self.pool = WorkerPool()

    def submit_job(self, query: str, 
                   start: int = 0, max_results: int = 10, step: int = 10,
                   since_year: int = 2020, download_pdfs: bool = False,
                   sites: List[str] = None) -> str:
        """Submit a new search job. Returns job_id."""
        
        job_id = str(uuid.uuid4())
        
        config = JobConfig(
            start=start,
            max_results=max_results,
            step=step,
            since_year=since_year,
            download_pdfs=download_pdfs,
            sites=sites or []
        )
        
        job = Job(
            id=job_id,
            query=query,
            status=JobStatus.PENDING,
            config=config,
            created_at=datetime.now()
        )
        
        JobStorage.save_job(job)
        self.pool.submit_job(job_id)
        
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        return JobStorage.load_job(job_id)

    def get_job_status(self, job_id: str) -> JobStatus:
        job = self.get_job(job_id)
        return job.status if job else JobStatus.FAILED

    def get_job_progress(self, job_id: str) -> float:
        job = self.get_job(job_id)
        return job.progress if job else 0.0

    def get_job_results(self, job_id: str) -> List[dict]:
        return JobStorage.get_results(job_id)

    def get_log_file_path(self, job_id: str) -> str:
         return os.path.join(JOBS_DIR, job_id, "logs", "job.log")

    def read_logs(self, job_id: str) -> str:
        """Reads the full log file content."""
        log_path = self.get_log_file_path(job_id)
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def cancel_job(self, job_id: str) -> bool:
        """Cancels a running or pending job."""
        job = self.get_job(job_id)
        if not job:
            return False
            
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False
            
        # Update status to CANCELLED in storage
        # The worker will pick this up in its next loop iteration
        job.status = JobStatus.CANCELLED
        JobStorage.save_job(job)
        return True

    def list_jobs(self, status: Optional[JobStatus] = None) -> List[Job]:
        all_jobs = JobStorage.list_jobs()
        if status:
            return [j for j in all_jobs if j.status == status]
        return all_jobs
