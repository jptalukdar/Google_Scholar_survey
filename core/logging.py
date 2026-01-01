import logging
import os
import queue
import datetime
from typing import Iterator

class LogStream:
    """A thread-safe log stream that allows reading logs as they are written."""
    def __init__(self):
        self._queue = queue.Queue()
        self._closed = False

    def write(self, record: str):
        if not self._closed:
            self._queue.put(record)

    def read(self, block=False, timeout=None) -> Iterator[str]:
        """Yields logs from the queue. If block is False, yields empty if empty."""
        try:
            while True:
                line = self._queue.get(block=block, timeout=timeout)
                yield line
                self._queue.task_done()
        except queue.Empty:
            pass

    def close(self):
        self._closed = True


class JobLogger:
    """Logger for a specific job that writes to file and a stream."""
    
    def __init__(self, job_id: str, log_dir: str):
        self.job_id = job_id
        self.log_file = os.path.join(log_dir, "job.log")
        self.stream = LogStream()
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup file handler
        self._setup_logger()

    def _setup_logger(self):
        # We don't use the root logger to avoid conflicts
        self.logger = logging.getLogger(f"job_{self.job_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = [] # Clear existing handlers
        
        # File Handler
        fh = logging.FileHandler(self.log_file, mode='a', encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(fh)

    def log(self, level: int, message: str):
        """Log a message and push to stream."""
        self.logger.log(level, message)
        
        # Format for stream
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        levelname = logging.getLevelName(level)
        formatted_message = f"[{timestamp}] [{levelname}] {message}"
        
        self.stream.write(formatted_message)

    def info(self, message: str):
        self.log(logging.INFO, message)

    def error(self, message: str):
        self.log(logging.ERROR, message)

    def warning(self, message: str):
        self.log(logging.WARNING, message)

    def debug(self, message: str):
        self.log(logging.DEBUG, message)

    def close(self):
        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)
        self.stream.close()
