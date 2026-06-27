"""
agents/cover_letter.py - Generates tailored cover letters

This agent:
1. Creates compelling, personalized cover letters
2. Matches company tone based on JD language
3. Highlights most relevant qualifications
4. Follows professional cover letter structure
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


COVER_LETTER_SYSTEM_PROMPT = """You are an expert cover letter writer. Create compelling, personalized cover letters that:

1. Open with a hook - not "I am writing to apply for..."
2. Show genuine interest in the specific company and role
3. Highlight 2-3 most relevant qualifications with brief evidence
4. Match the company's tone (formal for law firms, dynamic for startups)
5. Close with confident but not presumptuous call to action
6. Stay under one page (about 300-400 words)

Avoid:
- Generic openings
- Repeating the resume verbatim
- Self-deprecation or over-confidence
- Mentioning salary
- "I believe I would be a great fit" without specifics

Output the cover letter in clean markdown format, properly formatted as a professional letter."""


async def write_cover_letter(
    llm: BaseChatModel,
    resume_text: str,
    jd_text: str,
    fit_analysis: dict,
    job_title: str,
    company: str
) -> str:
    """
    Generate a tailored cover letter.
    
    Args:
        llm: Language model to use
        resume_text: Candidate's resume
        jd_text: Job description
        fit_analysis: Analysis of resume-JD fit
        job_title: Target position
        company: Target company name
    
    Returns:
        Cover letter as markdown string
    """
    # Extract top strengths for the letter
    strengths = fit_analysis.get("requirements_met", [])[:3]
    emphasis = fit_analysis.get("emphasis_recommendations", [])[:2]
    
    user_message = f"""Write a cover letter for {job_title} at {company}.

## JOB DESCRIPTION:
{jd_text}

## CANDIDATE'S BACKGROUND (from resume):
{resume_text}

## KEY STRENGTHS TO HIGHLIGHT:
{chr(10).join(f"- {s}" for s in strengths)}

## EMPHASIS RECOMMENDATIONS:
{chr(10).join(f"- {e}" for e in emphasis)}

Write a compelling, personalized cover letter that would make a hiring manager want to meet this candidate."""

    messages = [
        SystemMessage(content=COVER_LETTER_SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    response = await llm.ainvoke(messages)
    return response.content
