import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, ".data")

# Data subdirectories
SEARCH_DIR = os.path.join(DATA_DIR, "searches")
RESULTS_DIR = os.path.join(DATA_DIR, "results")
DOWNLOAD_DIR = os.path.join(DATA_DIR, "pdfs")
NOTES_DIR = os.path.join(DATA_DIR, "notes")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")

# Ensure directories exist
for d in [DATA_DIR, SEARCH_DIR, RESULTS_DIR, DOWNLOAD_DIR, NOTES_DIR, JOBS_DIR]:
    os.makedirs(d, exist_ok=True)

# Worker Settings
MAX_WORKERS = 4
DEFAULT_TIMEOUT = 300  # seconds

# Job Settings
JOB_POLL_INTERVAL = 1.0  # seconds
