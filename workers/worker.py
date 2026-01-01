import traceback
import os
from datetime import datetime
from typing import Optional

from core.logging import JobLogger
from core.config import JOBS_DIR
from extract_searches import SearchEngine
from .job import Job, JobStatus
from .job_storage import JobStorage

class SearchWorker:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job: Optional[Job] = JobStorage.load_job(job_id)
        self.logger = JobLogger(job_id, os.path.join(JOBS_DIR, job_id, "logs"))

    def run(self):
        if not self.job:
            self.logger.error(f"Job not found: {self.job_id}")
            return

        try:
            self.logger.info(f"Worker started for job {self.job_id}")
            self._update_status(JobStatus.RUNNING, started_at=datetime.now())

            engine = SearchEngine()
            
            # Define stop check callback
            def stop_check():
                # Reload job status from storage to check for external cancellation
                current_job = JobStorage.load_job(self.job_id)
                if current_job and current_job.status in [JobStatus.CANCELLED, JobStatus.FAILED]:
                    return True
                return False

            # Define progress callback
            def on_progress(progress, count):
                self.job.progress = progress
                self.job.total_results = count
                # Persist periodic updates? Or just keeping in memory if needed
                # For file storage, detailed updates might be I/O heavy, 
                # but let's save metadata for monitoring
                JobStorage.save_job(self.job)

            results = engine.search(
                query=self.job.query,
                config=self.job.config,
                progress_callback=on_progress,
                stop_check=stop_check,
                logger=self.logger
            )

            # Check if we stopped because of cancellation
            if stop_check():
                self.logger.info("Job execution stopped due to cancellation.")
                return

            JobStorage.save_results(self.job_id, results)
            
            self.job.total_results = len(results)
            self._update_status(JobStatus.COMPLETED, completed_at=datetime.now(), progress=1.0)
            self.logger.info("Job completed successfully")

        except Exception as e:
            err_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.logger.error(f"Job failed: {err_msg}")
            self.job.error = str(e)
            self._update_status(JobStatus.FAILED, completed_at=datetime.now())

        finally:
            self.logger.close()

    def _update_status(self, status: JobStatus, **kwargs):
        self.job.status = status
        for k, v in kwargs.items():
            setattr(self.job, k, v)
        JobStorage.save_job(self.job)

