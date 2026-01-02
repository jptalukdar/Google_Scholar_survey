from typing import List, Dict, Any
from dataclasses import dataclass
import json
import re

from ai.base import LLMProvider

@dataclass
class ResearchQuestions:
    topic: str
    questions: List[str]
    keywords: List[str]
    raw_response: str

SYSTEM_PROMPT = """You are an expert in computer science research methodology. 
Your task is to help researchers formulate research questions for systematic literature reviews.
Focus on creating clear, specific, and answerable research questions suitable for CS research.
Always respond in valid JSON format."""

QUESTION_GENERATION_PROMPT = """Given the following research abstract/topic, generate research questions for a systematic literature review.

Abstract/Topic:
{abstract}

Please generate:
1. 3-5 focused research questions (RQs) that address the key aspects of this topic
2. A list of 5-10 key search terms/keywords relevant to this research

The research questions should:
- Be answerable through literature analysis
- Cover different aspects (e.g., techniques, applications, challenges, comparisons)
- Be specific enough to guide paper selection
- Follow the format "RQ1: What/How/Which..."

Respond in this exact JSON format:
{{
    "topic_summary": "A one-line summary of the research topic",
    "research_questions": [
        "RQ1: ...",
        "RQ2: ...",
        "RQ3: ..."
    ],
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}
"""

class ResearchQuestionGenerator:
    """Generates research questions from an abstract using AI."""
    
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def generate(self, abstract: str) -> ResearchQuestions:
        """Generate research questions from the given abstract."""
        
        prompt = QUESTION_GENERATION_PROMPT.format(abstract=abstract)
        
        response = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)
        
        # Parse JSON from response
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return ResearchQuestions(
                topic=data.get("topic_summary", ""),
                questions=data.get("research_questions", []),
                keywords=data.get("keywords", []),
                raw_response=response
            )
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: try to extract questions manually
            questions = re.findall(r'RQ\d+:.*', response)
            return ResearchQuestions(
                topic=abstract[:100] + "...",
                questions=questions if questions else [response],
                keywords=[],
                raw_response=response
            )

    def refine(self, current_questions: ResearchQuestions, user_feedback: str) -> ResearchQuestions:
        """Refine research questions based on user feedback."""
        
        refinement_prompt = f"""Current research questions:
{json.dumps(current_questions.questions, indent=2)}

User feedback: {user_feedback}

Please update the research questions based on the feedback. Keep the same JSON format:
{{
    "topic_summary": "{current_questions.topic}",
    "research_questions": [
        "RQ1: ...",
        "RQ2: ..."
    ],
    "keywords": {json.dumps(current_questions.keywords)}
}}
"""
        
        response = self.llm.generate(refinement_prompt, system_prompt=SYSTEM_PROMPT)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("No JSON found in response")
            
            return ResearchQuestions(
                topic=data.get("topic_summary", current_questions.topic),
                questions=data.get("research_questions", current_questions.questions),
                keywords=data.get("keywords", current_questions.keywords),
                raw_response=response
            )
        except:
            return current_questions
