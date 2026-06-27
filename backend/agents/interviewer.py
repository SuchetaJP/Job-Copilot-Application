"""
agents/interviewer.py - Generates mock interview questions with answers

This agent:
1. Predicts likely interview questions based on role and resume
2. Creates sample answers grounded in candidate's actual experience
3. Includes behavioral, technical, and situational questions
4. Addresses potential weaknesses proactively
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel


INTERVIEWER_SYSTEM_PROMPT = """You are an expert interview coach and former hiring manager. Generate realistic interview questions and sample answers.

For each question:
1. Explain WHY the interviewer would ask this
2. Provide a sample answer using the candidate's actual experience
3. Include tips for delivery

Question categories to include:
- 2-3 behavioral questions (STAR format answers)
- 2-3 role-specific technical questions
- 2-3 situational/problem-solving questions
- 1-2 questions that address potential weaknesses in the fit

Output format in markdown:
## Question 1: [Question text]
**Why they ask this:** [Brief explanation]

**Sample answer:**
[Detailed answer using candidate's background]

**Delivery tips:**
- [Tip 1]
- [Tip 2]

---

[Repeat for all questions]"""


async def generate_interview_qa(
    llm: BaseChatModel,
    resume_text: str,
    jd_text: str,
    fit_analysis: dict,
    job_title: str,
    company: str
) -> str:
    """
    Generate mock interview questions with sample answers.
    
    Args:
        llm: Language model to use
        resume_text: Candidate's resume
        jd_text: Job description
        fit_analysis: Analysis showing strengths and gaps
        job_title: Target position
        company: Target company
    
    Returns:
        Interview prep document as markdown string
    """
    # Identify potential weakness questions from fit analysis
    gaps = fit_analysis.get("requirements_not_met", [])
    partial = fit_analysis.get("requirements_partial", [])
    
    gap_context = ""
    if gaps or partial:
        gap_context = f"""
## POTENTIAL WEAKNESS AREAS TO ADDRESS:
{chr(10).join(f"- {g}" for g in (gaps + partial)[:3])}
"""

    user_message = f"""Create 10 likely interview questions for {job_title} at {company}.

## JOB DESCRIPTION:
{jd_text}

## CANDIDATE'S BACKGROUND:
{resume_text}

## FIT SUMMARY:
- Score: {fit_analysis.get('overall_fit_score', 'N/A')}%
- Key strengths: {', '.join(fit_analysis.get('requirements_met', [])[:3])}
{gap_context}

Generate 10 questions with detailed sample answers grounded in this specific candidate's experience. Include questions that help them address potential concerns about gaps."""

    messages = [
        SystemMessage(content=INTERVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=user_message)
    ]
    
    response = await llm.ainvoke(messages)
    return response.content
