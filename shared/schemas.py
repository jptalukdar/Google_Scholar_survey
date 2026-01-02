from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

# --- Enums (Mirrored from core/workers) ---

class JobStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

# --- Common Models ---

class SearchQueryRequest(BaseModel):
    query: str
    max_results: int = 20
    since_year: int = 2020
    sites: List[str] = []
    download_pdfs: bool = False

class JobResponse(BaseModel):
    id: str
    query: str
    status: JobStatusEnum
    progress: float
    total_results: int
    created_at: str
    error: Optional[str] = None
    
class JobDetailResponse(JobResponse):
    logs: List[str] = []
    results: List[Dict[str, Any]] = []

class CancelJobResponse(BaseModel):
    success: bool
    message: str

# --- SLR Models ---

class SLRGenerateRequest(BaseModel):
    abstract: str
    api_key: str
    provider: str = "gemini"

class ResearchQuestionsModel(BaseModel):
    topic: str
    questions: List[str]
    keywords: List[str]

class SLRRefineRequest(BaseModel):
    current_questions: ResearchQuestionsModel
    feedback: str
    api_key: str
    provider: str = "gemini"

class SLRQueryRequest(BaseModel):
    questions: ResearchQuestionsModel
    sites: List[str] = []
    api_key: str
    provider: str = "gemini"

class SearchQueryModel(BaseModel):
    query: str
    research_question: str
    sites: List[str]

class SLRQueryResponse(BaseModel):
    queries: List[SearchQueryModel]

class SLRFilterRequest(BaseModel):
    papers: List[Dict[str, Any]]
    questions: List[str]
    threshold: int = 6
    api_key: str
    provider: str = "gemini"

class FilterResponse(BaseModel):
    included: List[Dict[str, Any]]
    excluded: List[Dict[str, Any]]

class DownloadRequest(BaseModel):
    papers: List[Dict[str, Any]]
    workflow_id: str

class DownloadResponse(BaseModel):
    success: bool
    zip_path: Optional[str] = None
    message: Optional[str] = None
