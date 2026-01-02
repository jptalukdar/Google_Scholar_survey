from typing import List, Dict
from dataclasses import dataclass
import json
import re

from ai.base import LLMProvider


@dataclass
class SearchQuery:
    query: str
    research_question: str
    sites: List[str]


SYSTEM_PROMPT = """You are an expert in academic database search strategies.
Your task is to convert research questions into effective search queries for Google Scholar.
Use Google search operators appropriately (OR, AND, quotes for exact phrases, site:).
Always respond in valid JSON format."""

QUERY_GENERATION_PROMPT = """Convert these research questions into Google Scholar search queries.

Research Questions:
{questions}

Keywords to consider:
{keywords}

For each research question, create 1-2 search queries using:
- Double quotes for exact phrases
- OR between synonyms/alternatives
- AND (implicit) between required terms
- Parentheses for grouping

Keep it as simple as possible without compounding too many terms.  

Respond in this exact JSON format:
{{
    "queries": [
        {{
            "research_question": "RQ1: ...",
            "search_query": "exact phrase" OR synonym1 OR synonym2 keyword1 keyword2
        }},
        ...
    ]
}}
"""


class QueryGenerator:
    """Generates search queries from research questions using AI."""

    # Default academic databases for CS research
    DEFAULT_SITES = [
        "sciencedirect.com",
        "ieeexplore.ieee.org",
        "link.springer.com",
        "dl.acm.org",
        "arxiv.org",
    ]

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate(
        self, questions: List[str], keywords: List[str], sites: List[str] = []
    ) -> List[SearchQuery]:
        """Generate search queries from research questions."""

        prompt = QUERY_GENERATION_PROMPT.format(
            questions="\n".join(questions), keywords=", ".join(keywords)
        )

        response = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        # Parse response
        queries = []
        selected_sites = sites if sites else []

        try:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group())

                for item in data.get("queries", []):
                    queries.append(
                        SearchQuery(
                            query=item.get("search_query", ""),
                            research_question=item.get("research_question", ""),
                            sites=selected_sites,
                        )
                    )
        except (json.JSONDecodeError, ValueError):
            # Fallback: create basic queries from keywords
            for rq in questions:
                query = " ".join(keywords[:5])  # Use first 5 keywords
                queries.append(
                    SearchQuery(query=query, research_question=rq, sites=selected_sites)
                )

        return queries

    def format_query_with_sites(self, query: SearchQuery) -> str:
        """Format query with site restrictions for Google Scholar."""
        base_query = query.query

        if query.sites:
            site_clause = " OR ".join([f"site:{site}" for site in query.sites])
            return f"{base_query} {site_clause}"

        return base_query
