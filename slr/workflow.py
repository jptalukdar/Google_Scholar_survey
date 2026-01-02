import os
import zipfile
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

from ai.base import LLMProvider
from api.job_manager import JobManager
from workers.job import JobStatus
from core.config import DOWNLOAD_DIR
from providers.provider import Provider

from .question_generator import ResearchQuestionGenerator, ResearchQuestions
from .query_generator import QueryGenerator, SearchQuery
from .relevance_filter import RelevanceFilter

@dataclass
class SLRConfig:
    max_results_per_query: int = 20
    since_year: int = 2020
    sites: List[str] = field(default_factory=list)
    download_pdfs: bool = False
    relevance_threshold: int = 6

@dataclass
class SLRResult:
    id: str
    abstract: str
    research_questions: ResearchQuestions
    queries: List[SearchQuery]
    job_ids: List[str]
    all_papers: List[Dict]
    included_papers: List[Dict]
    excluded_papers: List[Dict]
    zip_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

class SLRWorkflow:
    """Main workflow orchestrator for systematic literature reviews."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.job_manager = JobManager()
        self.question_generator = ResearchQuestionGenerator(llm)
        self.query_generator = QueryGenerator(llm)
        self.relevance_filter = RelevanceFilter(llm)

    def generate_questions(self, abstract: str) -> ResearchQuestions:
        """Step 1: Generate research questions from abstract."""
        return self.question_generator.generate(abstract)

    def refine_questions(self, current: ResearchQuestions, feedback: str) -> ResearchQuestions:
        """Step 1b: Refine questions based on user feedback."""
        return self.question_generator.refine(current, feedback)

    def generate_queries(self, questions: ResearchQuestions, 
                        sites: List[str] = None) -> List[SearchQuery]:
        """Step 2: Generate search queries from research questions."""
        return self.query_generator.generate(
            questions.questions, 
            questions.keywords,
            sites
        )

    def submit_jobs(self, queries: List[SearchQuery], config: SLRConfig) -> List[str]:
        """Step 3: Submit parallel search jobs."""
        job_ids = []
        
        for query in queries:
            # Format query with site restrictions
            formatted_query = self.query_generator.format_query_with_sites(query)
            
            job_id = self.job_manager.submit_job(
                query=formatted_query,
                start=0,
                max_results=config.max_results_per_query,
                since_year=config.since_year,
                sites=query.sites,
                download_pdfs=False  # We'll download after filtering
            )
            job_ids.append(job_id)
        
        return job_ids

    def wait_for_jobs(self, job_ids: List[str], timeout: int = 600) -> bool:
        """Step 4: Wait for all jobs to complete."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            all_done = True
            
            for job_id in job_ids:
                status = self.job_manager.get_job_status(job_id)
                if status not in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    all_done = False
                    break
            
            if all_done:
                return True
            
            time.sleep(2)
        
        return False

    def collect_results(self, job_ids: List[str]) -> List[Dict]:
        """Step 5: Collect all papers from completed jobs."""
        all_papers = []
        seen_titles = set()  # Deduplicate by title
        
        for job_id in job_ids:
            results = self.job_manager.get_job_results(job_id)
            
            for paper in results:
                title = paper.get("title", "").lower().strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    all_papers.append(paper)
        
        return all_papers

    def filter_relevance(self, papers: List[Dict], 
                        questions: List[str]) -> tuple[List[Dict], List[Dict]]:
        """Step 6: Filter papers by relevance."""
        return self.relevance_filter.filter(papers, questions)

    def download_and_zip_pdfs(self, papers: List[Dict], workflow_id: str) -> Optional[str]:
        """Step 7: Download PDFs for included papers and create zip."""
        downloaded_files = []
        
        for paper in papers:
            download_url = paper.get("download_url")
            if not download_url:
                continue
            
            title = paper.get("title", "Unknown")
            filename = Provider.generate_filename(title)
            filepath = os.path.join(DOWNLOAD_DIR, f"{filename}.pdf")
            
            # Check if already downloaded
            if os.path.exists(filepath):
                downloaded_files.append(filepath)
                continue
            
            # Try to download
            try:
                success, path = Provider.download_pdf(title, download_url)
                if success:
                    downloaded_files.append(path)
            except Exception as e:
                print(f"Failed to download {title}: {e}")
        
        if not downloaded_files:
            return None
        
        # Create zip file
        zip_path = os.path.join(DOWNLOAD_DIR, f"slr_{workflow_id}.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filepath in downloaded_files:
                arcname = os.path.basename(filepath)
                zipf.write(filepath, arcname)
        
        return zip_path

    def run_full_workflow(self, abstract: str, config: SLRConfig,
                          questions: ResearchQuestions = None) -> SLRResult:
        """Run the complete SLR workflow."""
        import uuid
        workflow_id = str(uuid.uuid4())[:8]
        
        # Step 1: Generate questions (or use provided)
        if questions is None:
            questions = self.generate_questions(abstract)
        
        # Step 2: Generate queries
        queries = self.generate_queries(questions, config.sites)
        
        # Step 3: Submit jobs
        job_ids = self.submit_jobs(queries, config)
        
        # Step 4: Wait for completion
        self.wait_for_jobs(job_ids)
        
        # Step 5: Collect results
        all_papers = self.collect_results(job_ids)
        
        # Step 6: Filter relevance
        self.relevance_filter.threshold = config.relevance_threshold
        included, excluded = self.filter_relevance(all_papers, questions.questions)
        
        # Step 7: Download PDFs if requested
        zip_path = None
        if config.download_pdfs and included:
            zip_path = self.download_and_zip_pdfs(included, workflow_id)
        
        return SLRResult(
            id=workflow_id,
            abstract=abstract,
            research_questions=questions,
            queries=queries,
            job_ids=job_ids,
            all_papers=all_papers,
            included_papers=included,
            excluded_papers=excluded,
            zip_path=zip_path
        )
