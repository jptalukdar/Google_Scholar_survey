import threading
import queue
import time
from typing import Dict

from core.config import MAX_WORKERS
from .worker import SearchWorker

class WorkerPool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(WorkerPool, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.job_queue = queue.Queue()
        self.running = True
        self.workers = []
        self._start_workers()
        self._initialized = True

    def _start_workers(self):
        for _ in range(MAX_WORKERS):
            t = threading.Thread(target=self._worker_loop, daemon=True)
            t.start()
            self.workers.append(t)

    def _worker_loop(self):
        while self.running:
            try:
                job_id = self.job_queue.get(timeout=1.0)
                worker = SearchWorker(job_id)
                worker.run()
                self.job_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker pool error: {e}")

    def submit_job(self, job_id: str):
        self.job_queue.put(job_id)

    def stop(self):
        self.running = False
        for t in self.workers:
            t.join(timeout=1.0)
