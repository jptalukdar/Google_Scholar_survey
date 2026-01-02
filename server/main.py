from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import logging
import traceback
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("server")

# Load environment variables from .env file
load_dotenv()

from shared.schemas import (
    SearchQueryRequest, JobResponse, JobDetailResponse, CancelJobResponse,
    SLRGenerateRequest, ResearchQuestionsModel, SLRRefineRequest,
    SLRQueryRequest, SLRQueryResponse, SLRFilterRequest, FilterResponse,
    DownloadRequest, DownloadResponse, SearchQueryModel
)

from api.job_manager import JobManager
from workers.job import JobStatus
from slr.question_generator import ResearchQuestionGenerator, ResearchQuestions
from slr.query_generator import QueryGenerator
from slr.relevance_filter import RelevanceFilter
from slr.workflow import SLRWorkflow
from slr.workflow import SLRWorkflow
from ai import get_provider
from server.extension import router as extension_router

app = FastAPI(title="SLR Worker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For extension development, allow all. Prod should restrict.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(extension_router)

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return HTTPException(status_code=500, detail="Internal Server Error")

# --- Service Instances ---
job_manager = JobManager()

# --- Job Routes ---

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/jobs", response_model=JobResponse)
def submit_job(req: SearchQueryRequest):
    logger.info(f"Submitting job: query='{req.query}', max_results={req.max_results}")
    job_id = job_manager.submit_job(
        query=req.query,
        max_results=req.max_results,
        since_year=req.since_year,
        sites=req.sites,
        download_pdfs=req.download_pdfs
    )
    logger.info(f"Job submitted successfully: {job_id}")
    # Return initial status
    job = job_manager.get_job(job_id)
    return _map_job_to_response(job)

@app.get("/jobs", response_model=List[JobResponse])
def list_jobs():
    jobs = job_manager.list_jobs()
    return [_map_job_to_response(j) for j in jobs]

@app.get("/jobs/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get extra details
    logs_raw = job_manager.read_logs(job_id)
    logs = logs_raw.splitlines() if logs_raw else []
    results = job_manager.get_job_results(job_id)
    
    # Map to detail response
    base_data = _map_job_to_response(job).model_dump()
    return JobDetailResponse(**base_data, logs=logs, results=results)

@app.post("/jobs/{job_id}/cancel", response_model=CancelJobResponse)
def cancel_job(job_id: str):
    success = job_manager.cancel_job(job_id)
    if success:
        logger.info(f"Job cancelled: {job_id}")
        return CancelJobResponse(success=True, message="Job cancellation requested")
    else:
        logger.warning(f"Failed to cancel job: {job_id} (not found or finished)")
        return CancelJobResponse(success=False, message="Job not found or already completed")

def _map_job_to_response(job) -> JobResponse:
    # Helper to map internal Job object to Pydantic model
    return JobResponse(
        id=job.id,
        query=job.query,
        status=job.status.value,
        progress=job.progress,
        total_results=job.total_results,
        created_at=job.created_at.isoformat(),
        error=job.error
    )

# --- SLR Routes ---

@app.post("/slr/generate-questions", response_model=ResearchQuestionsModel)
def generate_questions(req: SLRGenerateRequest):
    print("Generating questions...")
    print(req)
    try:
        llm = get_provider(req.provider, api_key=req.api_key)
        logger.info(f"Generating questions using model: {getattr(llm, 'model', 'unknown')}")
        generator = ResearchQuestionGenerator(llm)
        questions = generator.generate(req.abstract)
        
        return ResearchQuestionsModel(
            topic=questions.topic,
            questions=questions.questions,
            keywords=questions.keywords
        )
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slr/refine-questions", response_model=ResearchQuestionsModel)
def refine_questions(req: SLRRefineRequest):
    try:
        llm = get_provider(req.provider, api_key=req.api_key)
        logger.info(f"Refining questions using model: {getattr(llm, 'model', 'unknown')}")
        generator = ResearchQuestionGenerator(llm)
        
        # Reconstruct internal object
        current = ResearchQuestions(
            topic=req.current_questions.topic,
            questions=req.current_questions.questions,
            keywords=req.current_questions.keywords,
            raw_response=""
        )
        
        updated = generator.refine(current, req.feedback)
        
        return ResearchQuestionsModel(
            topic=updated.topic,
            questions=updated.questions,
            keywords=updated.keywords
        )
    except Exception as e:
        logger.error(f"Error refining questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slr/generate-queries", response_model=SLRQueryResponse)
def generate_queries(req: SLRQueryRequest):
    try:
        llm = get_provider(req.provider, api_key=req.api_key)
        logger.info(f"Generating queries using model: {getattr(llm, 'model', 'unknown')}")
        generator = QueryGenerator(llm)
        
        queries = generator.generate(
            req.questions.questions, 
            req.questions.keywords, 
            req.sites
        )
        
        return SLRQueryResponse(
            queries=[
                SearchQueryModel(
                    query=q.query,
                    research_question=q.research_question,
                    sites=q.sites
                ) for q in queries
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slr/filter-relevance", response_model=FilterResponse)
def filter_relevance(req: SLRFilterRequest):
    try:
        llm = get_provider(req.provider, api_key=req.api_key)
        filter_engine = RelevanceFilter(llm, threshold=req.threshold)
        
        included, excluded = filter_engine.filter(req.papers, req.questions)
        
        return FilterResponse(included=included, excluded=excluded)
    except Exception as e:
        logger.error(f"Error in SLR relevance filter: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/slr/download-pdfs", response_model=DownloadResponse)
def download_pdfs(req: DownloadRequest):
    try:
        # We need a dummy LLM provider just to init workflow, or decouple download logic
        # For simplicity, we'll re-use SLRWorkflow logic but with dummy LLM if needed
        # Actually workflow needs an LLM to init... let's decouple or pass dummy
        
        # Hack: Pass dummy LLM since we don't need it for download
        class DummyLLM:
            pass
        
        workflow = SLRWorkflow(DummyLLM())
        zip_path = workflow.download_and_zip_pdfs(req.papers, req.workflow_id)
        
        if zip_path:
            return DownloadResponse(success=True, zip_path=zip_path)
        else:
            return DownloadResponse(success=True, message="No PDFs downloaded")
            
    except Exception as e:
        return DownloadResponse(success=False, message=str(e))

# Explicitly export app for uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
