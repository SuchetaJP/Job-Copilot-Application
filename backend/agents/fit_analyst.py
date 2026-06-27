"""
agents/fit_analyst.py - Analyzes resume fit against job description

This agent:
1. Extracts requirements from the JD
2. Matches them against resume content
3. Identifies gaps and strengths
4. Provides recommendations for emphasis

Output is structured JSON for use by other agents.
"""

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


# System prompt that defines the agent's role and output format
FIT_ANALYST_SYSTEM_PROMPT = """You are an expert career coach and hiring manager. 
Your job is to analyze how well a candidate's resume matches a job description.

You must:
1. Extract all explicit and implicit requirements from the job description
2. Match each requirement against the candidate's experience
3. Identify gaps that need addressing
4. Recommend what to emphasize to maximize fit

Output ONLY valid JSON in this exact format:
{
    "requirements_met": ["requirement 1 with evidence from resume", ...],
    "requirements_not_met": ["requirement with no evidence in resume", ...],
    "requirements_partial": ["requirement with some but incomplete evidence", ...],
    "emphasis_recommendations": [
        "Emphasize X because it directly maps to Y requirement",
        ...
    ],
    "overall_fit_score": 75,
    "summary": "2-3 sentence overall assessment"
}

Be specific and cite evidence from the resume when matching requirements.
The fit score should be 0-100 based on how many requirements are met and their importance."""


async def analyze_fit(
    llm: BaseChatModel,
    resume_text: str,
    jd_text: str,
    job_title: str,
    company: str
) -> dict:
    """
    Analyze how well a resume matches a job description.
    
    Args:
        llm: Language model to use
        resume_text: Full text of resume
        jd_text: Job description text
        job_title: Target position
        company: Target company name
    
    Returns:
        Dict with analysis results (see system prompt for structure)
    """
    # Construct the analysis request
    user_message = f"""Analyze this candidate's fit for the {job_title} position at {company}.

## JOB DESCRIPTION:
{jd_text}

## CANDIDATE'S RESUME:
{resume_text}

Provide your analysis as JSON only."""

    messages = [
        SystemMessage(content=FIT_ANALYST_SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    # Get response from LLM
    response = await llm.ainvoke(messages)
    
    # Parse JSON response
    # LLMs sometimes wrap JSON in markdown code blocks, so we clean that
    content = response.content.strip()
    
    # Remove markdown code block if present
    if content.startswith("```"):
        # Find the JSON content between code blocks
        lines = content.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.startswith("```") and not in_json:
                in_json = True
                continue
            elif line.startswith("```") and in_json:
                break
            elif in_json:
                json_lines.append(line)
        content = "\n".join(json_lines)
    
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        # If parsing fails, return a structured error
        return {
            "requirements_met": [],
            "requirements_not_met": ["Unable to parse JD requirements"],
            "requirements_partial": [],
            "emphasis_recommendations": ["Please check the job description format"],
            "overall_fit_score": 0,
            "summary": f"Analysis failed: {str(e)}. Raw response: {content[:500]}"
        }
