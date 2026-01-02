import requests
import json
import time
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_URL = "http://localhost:8000"
# Get API key from env or set here for testing
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def test_health():
    print("\n[Testing GET /health]")
    resp = requests.get(f"{BASE_URL}/health")
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.json()}")
    assert resp.status_code == 200

def test_jobs_workflow():
    print("\n[Testing Jobs Workflow]")
    
    # 1. Submit Job
    print("Submitting Job...")
    payload = {
        "query": "test query solar energy",
        "max_results": 5,
        "since_year": 2022
    }
    resp = requests.post(f"{BASE_URL}/jobs", json=payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    job = resp.json()
    job_id = job['id']
    print(f"Submitted Job ID: {job_id}")

    # 2. List Jobs
    print("Listing Jobs...")
    resp = requests.get(f"{BASE_URL}/jobs")
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    jobs = resp.json()
    assert any(j['id'] == job_id for j in jobs)
    print(f"Found {len(jobs)} jobs")

    # 3. Get Job Detail
    print(f"Getting Job Detail for {job_id}...")
    resp = requests.get(f"{BASE_URL}/jobs/{job_id}")
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    detail = resp.json()
    print(f"Status: {detail['status']}")
    assert 'logs' in detail
    assert 'results' in detail

    # 4. Cancel Job
    print(f"Cancelling Job {job_id}...")
    resp = requests.post(f"{BASE_URL}/jobs/{job_id}/cancel")
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    print(f"Cancel Response: {resp.json()}")

def test_slr_workflow():
    if not GEMINI_API_KEY:
        print("\n[Skipping SLR Workflow (No GEMINI_API_KEY env var)]")
        return

    print("\n[Testing SLR Workflow]")
    sample_abstract = "This paper explores the impact of blockchain on supply chain transparency in the food industry."

    # 1. Generate Questions
    print("Generating Questions...")
    payload = {
        "abstract": sample_abstract,
        "api_key": GEMINI_API_KEY
    }
    resp = requests.post(f"{BASE_URL}/slr/generate-questions", json=payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    questions = resp.json()
    print(f"Generated {len(questions['questions'])} questions")

    # 2. Refine Questions
    print("Refining Questions...")
    refine_payload = {
        "current_questions": questions,
        "feedback": "Add a focus on cost-effectiveness.",
        "api_key": GEMINI_API_KEY
    }
    resp = requests.post(f"{BASE_URL}/slr/refine-questions", json=refine_payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    refined = resp.json()
    print(f"Refined Topic: {refined['topic']}")

    # 3. Generate Queries
    print("Generating Queries...")
    query_payload = {
        "questions": refined,
        "sites": ["arxiv.org"],
        "api_key": GEMINI_API_KEY
    }
    resp = requests.post(f"{BASE_URL}/slr/generate-queries", json=query_payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    queries_data = resp.json()
    print(f"Generated {len(queries_data['queries'])} queries")

    # 4. Filter Relevance
    print("Filtering Relevance...")
    filter_payload = {
        "papers": [
            {"title": "Blockchain in Food", "abstract": "A study on transparency.", "url": "http://ex.com/1"},
            {"title": "Cooking Recipes", "abstract": "How to make pasta.", "url": "http://ex.com/2"}
        ],
        "questions": refined['questions'],
        "api_key": GEMINI_API_KEY
    }
    resp = requests.post(f"{BASE_URL}/slr/filter-relevance", json=filter_payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    filtered = resp.json()
    print(f"Included: {len(filtered['included'])}, Excluded: {len(filtered['excluded'])}")

    # 5. Download PDFs (Mock)
    print("Testing Zip Creation...")
    dl_payload = {
        "papers": filtered['included'],
        "workflow_id": "test_workflow_123"
    }
    resp = requests.post(f"{BASE_URL}/slr/download-pdfs", json=dl_payload)
    if resp.status_code != 200:
        print(f"Error: {resp.status_code} - {resp.text}")
    assert resp.status_code == 200
    print(f"Download Response: {resp.json()}")

if __name__ == "__main__":
    try:
        test_health()
        test_jobs_workflow()
        test_slr_workflow()
        print("\n[PASS] All tests passed!")
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
