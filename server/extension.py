from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
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
