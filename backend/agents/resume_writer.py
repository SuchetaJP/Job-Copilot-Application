"""
agents/resume_writer.py - Rewrites resume bullets for target role

This agent:
1. Takes original resume and fit analysis
2. Rewrites bullet points to emphasize relevant skills
3. Incorporates keywords from JD naturally
4. Maintains truthfulness (doesn't invent experience)
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


RESUME_WRITER_SYSTEM_PROMPT = """You are an expert resume writer who specializes in ATS optimization and compelling bullet points.

Your task is to rewrite the candidate's resume to better target the specific job description, while:
1. NEVER inventing experience - only reframe what exists
2. Using action verbs and quantified achievements
3. Naturally incorporating relevant keywords from the JD
4. Emphasizing the strengths identified in the fit analysis
5. De-emphasizing (but not removing) less relevant experience

Output format:
- Use clear markdown sections (## for headers)
- Each experience should have 3-5 punchy bullet points
- Lead with the most relevant experiences
- Keep total length appropriate for the candidate's experience level

Write the complete rewritten resume in markdown format."""


async def rewrite_resume(
    llm: BaseChatModel,
    resume_text: str,
    jd_text: str,
    fit_analysis: dict,
    job_title: str
) -> str:
    """
    Rewrite resume to better target the job description.
    
    Args:
        llm: Language model to use
        resume_text: Original resume text
        jd_text: Target job description
        fit_analysis: Output from fit analyst (guides emphasis)
        job_title: Target position
    
    Returns:
        Rewritten resume as markdown string
    """
    # Format fit analysis for context
    fit_context = f"""
## FIT ANALYSIS SUMMARY:
- Overall fit score: {fit_analysis.get('overall_fit_score', 'N/A')}%
- Key strengths to emphasize: {', '.join(fit_analysis.get('emphasis_recommendations', [])[:3])}
- Requirements met: {len(fit_analysis.get('requirements_met', []))}
- Requirements to address: {len(fit_analysis.get('requirements_not_met', []))}
"""

    user_message = f"""Rewrite this resume for the {job_title} position.

## TARGET JOB DESCRIPTION:
{jd_text}

{fit_context}

## ORIGINAL RESUME:
{resume_text}

Rewrite the resume to maximize fit while staying truthful to the candidate's actual experience.
Output the complete rewritten resume in markdown format."""

    messages = [
        SystemMessage(content=RESUME_WRITER_SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    response = await llm.ainvoke(messages)
    return response.content
