"""
SLR Tools - Callable functions for MCP/Tool-based invocation.
These tools can be called by LLMs or external systems to orchestrate SLR workflows.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

from ai import get_provider, LLMProvider
from .workflow import SLRWorkflow, SLRConfig, SLRResult
from .question_generator import ResearchQuestions
from .query_generator import SearchQuery

@dataclass
class ToolResult:
    success: bool
    data: Any
    error: Optional[str] = None

class SLRTools:
    """Collection of SLR tools that can be invoked."""
    
    def __init__(self, api_key: str, provider: str = "gemini"):
        self.llm = get_provider(provider, api_key=api_key)
        self.workflow = SLRWorkflow(self.llm)
        
        # Store workflow state
        self._current_questions: Optional[ResearchQuestions] = None
        self._current_queries: Optional[List[SearchQuery]] = None
        self._job_ids: Optional[List[str]] = None

    def generate_research_questions(self, abstract: str) -> ToolResult:
        """
        Tool: generate_research_questions
        Description: Generate research questions from an abstract for systematic literature review.
        Parameters:
            abstract (str): The research abstract or topic description.
        Returns:
            Research questions, keywords, and topic summary.
        """
        try:
            questions = self.workflow.generate_questions(abstract)
            self._current_questions = questions
            
            return ToolResult(
                success=True,
                data={
                    "topic": questions.topic,
                    "research_questions": questions.questions,
                    "keywords": questions.keywords
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def refine_research_questions(self, feedback: str) -> ToolResult:
        """
        Tool: refine_research_questions
        Description: Refine previously generated research questions based on user feedback.
        Parameters:
            feedback (str): User's feedback or modification request.
        Returns:
            Updated research questions.
        """
        if not self._current_questions:
            return ToolResult(success=False, data=None, 
                            error="No research questions to refine. Generate questions first.")
        
        try:
            questions = self.workflow.refine_questions(self._current_questions, feedback)
            self._current_questions = questions
            
            return ToolResult(
                success=True,
                data={
                    "topic": questions.topic,
                    "research_questions": questions.questions,
                    "keywords": questions.keywords
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def generate_search_queries(self, sites: List[str] = None) -> ToolResult:
        """
        Tool: generate_search_queries
        Description: Generate search queries from research questions.
        Parameters:
            sites (List[str], optional): List of sites to restrict search to.
        Returns:
            List of search queries with their corresponding research questions.
        """
        if not self._current_questions:
            return ToolResult(success=False, data=None,
                            error="No research questions available. Generate questions first.")
        
        try:
            queries = self.workflow.generate_queries(self._current_questions, sites)
            self._current_queries = queries
            
            return ToolResult(
                success=True,
                data={
                    "queries": [
                        {
                            "query": q.query,
                            "research_question": q.research_question,
                            "sites": q.sites
                        }
                        for q in queries
                    ]
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def submit_search_jobs(self, max_results: int = 20, since_year: int = 2020) -> ToolResult:
        """
        Tool: submit_search_jobs
        Description: Submit parallel search jobs for all generated queries.
        Parameters:
            max_results (int): Maximum results per query (default: 20).
            since_year (int): Only include papers from this year onwards (default: 2020).
        Returns:
            List of job IDs.
        """
        if not self._current_queries:
            return ToolResult(success=False, data=None,
                            error="No queries available. Generate queries first.")
        
        try:
            config = SLRConfig(
                max_results_per_query=max_results,
                since_year=since_year
            )
            job_ids = self.workflow.submit_jobs(self._current_queries, config)
            self._job_ids = job_ids
            
            return ToolResult(
                success=True,
                data={"job_ids": job_ids, "count": len(job_ids)}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def check_job_status(self) -> ToolResult:
        """
        Tool: check_job_status
        Description: Check the status of submitted search jobs.
        Returns:
            Status of each job (pending, running, completed, failed).
        """
        if not self._job_ids:
            return ToolResult(success=False, data=None,
                            error="No jobs submitted yet.")
        
        try:
            statuses = []
            for job_id in self._job_ids:
                job = self.workflow.job_manager.get_job(job_id)
                if job:
                    statuses.append({
                        "job_id": job_id,
                        "status": job.status.value,
                        "progress": job.progress,
                        "results": job.total_results
                    })
            
            all_done = all(s["status"] in ["completed", "failed", "cancelled"] for s in statuses)
            
            return ToolResult(
                success=True,
                data={"jobs": statuses, "all_completed": all_done}
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def filter_papers_by_relevance(self, threshold: int = 6) -> ToolResult:
        """
        Tool: filter_papers_by_relevance
        Description: Filter collected papers by relevance to research questions using AI.
        Parameters:
            threshold (int): Minimum relevance score (0-10) to include paper (default: 6).
        Returns:
            Included and excluded papers with relevance scores.
        """
        if not self._job_ids or not self._current_questions:
            return ToolResult(success=False, data=None,
                            error="Missing jobs or research questions.")
        
        try:
            # Collect results
            all_papers = self.workflow.collect_results(self._job_ids)
            
            # Filter
            self.workflow.relevance_filter.threshold = threshold
            included, excluded = self.workflow.filter_relevance(
                all_papers, 
                self._current_questions.questions
            )
            
            return ToolResult(
                success=True,
                data={
                    "total_papers": len(all_papers),
                    "included_count": len(included),
                    "excluded_count": len(excluded),
                    "included": [
                        {
                            "title": p.get("title"),
                            "score": p.get("relevance_score"),
                            "justification": p.get("relevance_justification")
                        }
                        for p in included
                    ],
                    "excluded": [
                        {
                            "title": p.get("title"),
                            "score": p.get("relevance_score")
                        }
                        for p in excluded[:10]  # Limit excluded list
                    ]
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

    def download_relevant_pdfs(self, workflow_id: str = "manual") -> ToolResult:
        """
        Tool: download_relevant_pdfs
        Description: Download PDFs for relevant papers and create a zip file.
        Parameters:
            workflow_id (str): Identifier for the zip file name.
        Returns:
            Path to the created zip file.
        """
        if not self._job_ids or not self._current_questions:
            return ToolResult(success=False, data=None,
                            error="No workflow data available.")
        
        try:
            all_papers = self.workflow.collect_results(self._job_ids)
            included, _ = self.workflow.filter_relevance(
                all_papers, 
                self._current_questions.questions
            )
            
            zip_path = self.workflow.download_and_zip_pdfs(included, workflow_id)
            
            if zip_path:
                return ToolResult(
                    success=True,
                    data={"zip_path": zip_path, "paper_count": len(included)}
                )
            else:
                return ToolResult(
                    success=True,
                    data={"zip_path": None, "message": "No downloadable PDFs found"}
                )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))


# Tool definitions for MCP/function calling
TOOL_DEFINITIONS = [
    {
        "name": "generate_research_questions",
        "description": "Generate research questions from an abstract for systematic literature review.",
        "parameters": {
            "type": "object",
            "properties": {
                "abstract": {
                    "type": "string",
                    "description": "The research abstract or topic description."
                }
            },
            "required": ["abstract"]
        }
    },
    {
        "name": "refine_research_questions",
        "description": "Refine previously generated research questions based on user feedback.",
        "parameters": {
            "type": "object",
            "properties": {
                "feedback": {
                    "type": "string",
                    "description": "User's feedback or modification request."
                }
            },
            "required": ["feedback"]
        }
    },
    {
        "name": "generate_search_queries",
        "description": "Generate search queries from research questions.",
        "parameters": {
            "type": "object",
            "properties": {
                "sites": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of sites to restrict search to."
                }
            }
        }
    },
    {
        "name": "submit_search_jobs",
        "description": "Submit parallel search jobs for all generated queries.",
        "parameters": {
            "type": "object",
            "properties": {
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results per query (default: 20)."
                },
                "since_year": {
                    "type": "integer",
                    "description": "Only include papers from this year onwards."
                }
            }
        }
    },
    {
        "name": "check_job_status",
        "description": "Check the status of submitted search jobs.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "filter_papers_by_relevance",
        "description": "Filter collected papers by relevance to research questions using AI.",
        "parameters": {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "integer",
                    "description": "Minimum relevance score (0-10) to include paper."
                }
            }
        }
    },
    {
        "name": "download_relevant_pdfs",
        "description": "Download PDFs for relevant papers and create a zip file.",
        "parameters": {
            "type": "object",
            "properties": {
                "workflow_id": {
                    "type": "string",
                    "description": "Identifier for the zip file name."
                }
            }
        }
    }
]
