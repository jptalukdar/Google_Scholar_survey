import time
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup driver path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
driver_bin = os.path.join(current_dir, "driver")
if driver_bin not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + driver_bin

from api import JobManager
from workers.job import JobStatus

def main():
    manager = JobManager()
    
    # Define queries
    queries = [
        "generative ai in education",
        "large language models security"
    ]
    
    print(f"Submitting {len(queries)} jobs...")
    
    job_ids = []
    for query in queries:
        job_id = manager.submit_job(
            query=query,
            start=0,
            max_results=5, # Fetch 20 results
            download_pdfs=False # Don't download PDFs for this quick test
        )
        job_ids.append(job_id)
        print(f"Submitted job {job_id} for query: '{query}'")
    
    print("\nMonitoring jobs...")
    
    try:
        while True:
            all_done = True
            
            # Clear screen (optional, works in some terminals)
            # os.system('cls' if os.name == 'nt' else 'clear')
            
            print(f"\nStatus Report - {time.strftime('%H:%M:%S')}")
            print("-" * 50)
            
            for job_id in job_ids:
                job = manager.get_job(job_id)
                if not job:
                    print(f"Job {job_id}: Not found")
                    continue
                
                status_symbol = {
                    JobStatus.PENDING: "⏳",
                    JobStatus.RUNNING: "🔄",
                    JobStatus.COMPLETED: "✅",
                    JobStatus.FAILED: "❌",
                    JobStatus.CANCELLED: "🚫"
                }.get(job.status, "?")
                
                print(f"[{status_symbol}] Job {job_id[:8]}... | Status: {job.status.value:<10} | Progress: {job.progress*100:5.1f}% | Results: {job.total_results}")
                
                if job.status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    all_done = False
            
            if all_done:
                print("\nAll jobs completed!")
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("Stopping monitor...")

    # Display results summary
    print("\nResults Summary:")
    for job_id in job_ids:
        results = manager.get_job_results(job_id)
        job = manager.get_job(job_id)
        print(f"Query: '{job.query}' -> {len(results)} papers found.")

if __name__ == "__main__":
    main()
