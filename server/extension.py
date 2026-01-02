from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
import json
import os
from pydantic import BaseModel
from shared.schemas import ExtensionPaper, ExtensionProject

# Create router
router = APIRouter(prefix="/extension", tags=["Extension"])

# Simple JSON storage for now
DATA_FILE = "slr_extension_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {"projects": [{"id": "default", "name": "Default Project"}], "papers": []}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"projects": [{"id": "default", "name": "Default Project"}], "papers": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@router.get("/health")
def extension_health():
    return {"status": "connected", "version": "1.0"}

@router.get("/projects", response_model=List[ExtensionProject])
def get_projects():
    data = load_data()
    return data["projects"]

@router.post("/projects", response_model=ExtensionProject)
def create_project(project: ExtensionProject):
    data = load_data()
    if any(p["id"] == project.id for p in data["projects"]):
        raise HTTPException(status_code=400, detail="Project ID already exists")
    data["projects"].append(project.dict())
    save_data(data)
    return project

@router.get("/papers", response_model=List[ExtensionPaper])
def get_papers(project_id: str = "default"):
    data = load_data()
    # Filter by project_id if we had it in schema, for now return all or filter 
    # Logic: return papers that match project_id (need to add project_id to paper schema or store relation)
    # For MVP, assuming papers have project_id field
    return [p for p in data["papers"] if p.get("project_id") == project_id]

@router.post("/papers", response_model=ExtensionPaper)
def save_paper(paper: ExtensionPaper):
    data = load_data()
    # Check if exists
    existing = next((p for p in data["papers"] if p["id"] == paper.id), None)
    if existing:
        # Update
        data["papers"] = [p if p["id"] != paper.id else paper.dict() for p in data["papers"]]
    else:
        # Add
        data["papers"].append(paper.dict())
    
    save_data(data)
    return paper

@router.delete("/papers/{paper_id}")
def delete_paper(paper_id: str):
    data = load_data()
    initial_len = len(data["papers"])
    data["papers"] = [p for p in data["papers"] if p["id"] != paper_id]
    if len(data["papers"]) == initial_len:
        raise HTTPException(status_code=404, detail="Paper not found")
    save_data(data)
    return {"success": True}

# --- New Endpoints for Enhanced Extension ---

@router.get("/check-duplicate")
def check_duplicate(doi: Optional[str] = None, title: Optional[str] = None, project_id: str = "default"):
    """Check if a paper already exists in the project."""
    data = load_data()
    papers = [p for p in data["papers"] if p.get("project_id") == project_id]
    
    for paper in papers:
        # Check by DOI if provided
        if doi and paper.get("doi") == doi:
            return {"exists": True, "paper_id": paper["id"]}
        
        # Check by normalized title
        if title:
            normalized_title = title.lower().strip()
            paper_title = paper.get("title", "").lower().strip()
            if normalized_title == paper_title:
                return {"exists": True, "paper_id": paper["id"]}
    
    return {"exists": False, "paper_id": None}

@router.post("/check-duplicates-batch")
def check_duplicates_batch(papers: List[Dict[str, Any]], project_id: str = "default"):
    """Check multiple papers for duplicates in one request."""
    data = load_data()
    saved_papers = [p for p in data["papers"] if p.get("project_id") == project_id]
    
    # Create lookup sets
    saved_titles = {p.get("title", "").lower().strip() for p in saved_papers}
    saved_ids = {p.get("id") for p in saved_papers}
    
    results = {}
    for paper in papers:
        paper_id = paper.get("id", "")
        paper_title = paper.get("title", "").lower().strip()
        
        if paper_id in saved_ids or paper_title in saved_titles:
            results[paper_id] = {"exists": True}
        else:
            results[paper_id] = {"exists": False}
    
    return results

@router.patch("/papers/{paper_id}/status")
def update_paper_status(paper_id: str, status: str):
    """Update paper read status (unread/reviewed)."""
    data = load_data()
    for paper in data["papers"]:
        if paper["id"] == paper_id:
            paper["status"] = status
            save_data(data)
            return {"success": True, "status": status}
    raise HTTPException(status_code=404, detail="Paper not found")

# --- Query History ---

@router.get("/query-history")
def get_query_history(project_id: str = "default"):
    """Get query history for a project."""
    data = load_data()
    history = data.get("query_history", {}).get(project_id, [])
    return history

@router.post("/query-history")
def add_query_to_history(query: str, project_id: str = "default"):
    """Log a query to history."""
    data = load_data()
    if "query_history" not in data:
        data["query_history"] = {}
    if project_id not in data["query_history"]:
        data["query_history"][project_id] = []
    
    # Add with timestamp
    from datetime import datetime
    entry = {
        "query": query,
        "timestamp": datetime.now().isoformat()
    }
    data["query_history"][project_id].insert(0, entry)  # Most recent first
    
    # Keep only last 50 queries
    data["query_history"][project_id] = data["query_history"][project_id][:50]
    
    save_data(data)
    return {"success": True}

# --- Query Generation (LLM-powered) ---

@router.post("/generate-queries")
def generate_queries(request: Dict[str, Any]):
    """Generate search queries from abstract using LLM."""
    from ai import get_provider
    from slr.query_generator import QueryGenerator
    
    abstract = request.get("abstract", "")
    strategy = request.get("strategy", "specific")  # broad, specific, snowball
    sites = request.get("sites", [])
    api_key = request.get("api_key", "")
    
    if not abstract:
        raise HTTPException(status_code=400, detail="Abstract is required")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required")
    
    try:
        llm = get_provider("gemini", api_key=api_key)
        generator = QueryGenerator(llm)
        
        # Generate keywords based on strategy
        strategy_prompts = {
            "broad": "Extract 3-5 high-level, general keywords",
            "specific": "Extract 5-8 specific technical terms and methodologies",
            "snowball": "Identify seminal concepts and foundational terms for finding influential papers"
        }
        
        # Simple keyword extraction for now
        keywords = abstract.split()[:10]  # Placeholder - LLM will refine
        
        # Generate queries
        questions = [f"Find papers related to: {abstract[:200]}"]
        queries = generator.generate(questions, keywords, sites)
        
        return {
            "queries": [
                {
                    "query": q.query,
                    "description": q.research_question,
                    "sites": q.sites
                }
                for q in queries
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
