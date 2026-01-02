from typing import List, Dict, Tuple
from dataclasses import dataclass
import json
import re

from ai.base import LLMProvider

@dataclass
class RelevanceResult:
    paper_index: int
    title: str
    score: int  # 0-10
    relevant: bool
    justification: str

SYSTEM_PROMPT = """You are an expert systematic literature review researcher.
Your task is to assess paper relevance based on titles and abstracts.
Be rigorous but fair in your assessment.
Always respond in valid JSON format."""

RELEVANCE_PROMPT = """Assess the relevance of these papers to the research questions.

Research Questions:
{questions}

Papers to assess:
{papers}

For each paper, provide:
- score: 0-10 (0=completely irrelevant, 10=highly relevant)
- relevant: true if score >= {threshold}
- justification: brief reason for the score

Respond in this exact JSON format:
{{
    "assessments": [
        {{
            "paper_index": 0,
            "title": "paper title",
            "score": 7,
            "relevant": true,
            "justification": "Directly addresses RQ1 regarding..."
        }},
        ...
    ]
}}
"""

class RelevanceFilter:
    """Filters papers by relevance to research questions using AI."""
    
    def __init__(self, llm: LLMProvider, threshold: int = 6):
        self.llm = llm
        self.threshold = threshold
        self.batch_size = 10  # Process papers in batches

    def filter(self, papers: List[Dict], questions: List[str]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter papers by relevance.
        Returns (included_papers, excluded_papers)
        """
        included = []
        excluded = []
        
        # Process in batches
        for i in range(0, len(papers), self.batch_size):
            batch = papers[i:i + self.batch_size]
            results = self._assess_batch(batch, questions, start_index=i)
            
            for result in results:
                paper = papers[result.paper_index]
                paper["relevance_score"] = result.score
                paper["relevance_justification"] = result.justification
                
                if result.relevant:
                    included.append(paper)
                else:
                    excluded.append(paper)
        
        return included, excluded

    def _assess_batch(self, papers: List[Dict], questions: List[str], 
                      start_index: int = 0) -> List[RelevanceResult]:
        """Assess a batch of papers."""
        
        # Format papers for prompt
        papers_text = "\n".join([
            f"{i + start_index}. Title: {p.get('title', 'Unknown')}\n   Abstract: {p.get('abstract', 'N/A')[:300]}..."
            for i, p in enumerate(papers)
        ])
        
        prompt = RELEVANCE_PROMPT.format(
            questions="\n".join(questions),
            papers=papers_text,
            threshold=self.threshold
        )
        
        response = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        
        results = []
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                for item in data.get("assessments", []):
                    results.append(RelevanceResult(
                        paper_index=item.get("paper_index", 0),
                        title=item.get("title", ""),
                        score=item.get("score", 0),
                        relevant=item.get("relevant", False),
                        justification=item.get("justification", "")
                    ))
        except (json.JSONDecodeError, ValueError):
            # Fallback: include all papers if parsing fails
            for i, p in enumerate(papers):
                results.append(RelevanceResult(
                    paper_index=i + start_index,
                    title=p.get("title", ""),
                    score=self.threshold,
                    relevant=True,
                    justification="Assessment failed - included by default"
                ))
        
        return results
