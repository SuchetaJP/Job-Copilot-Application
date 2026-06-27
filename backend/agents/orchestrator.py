"""
orchestrator.py - LangGraph multi-agent pipeline

This module defines:
1. The shared state that flows through the pipeline
2. The graph structure connecting agents
3. Functions to run the full pipeline or individual agents

LangGraph KEY CONCEPTS:
- StateGraph: A graph where nodes share and update a common state
- Nodes: Functions that process state and return updates
- Edges: Connections between nodes (can be conditional)
- START/END: Special nodes marking entry and exit points
"""

import json
from typing import TypedDict, List, Optional, Annotated
import operator

from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

from ..config import get_settings
from .fit_analyst import analyze_fit
from .resume_writer import rewrite_resume
from .cover_letter import write_cover_letter
from .interviewer import generate_interview_qa

settings = get_settings()


# ============================================================
# PIPELINE STATE
# ============================================================

class PipelineState(TypedDict):
    """
    Shared state that flows through all agents.
    
    WHY TypedDict?
    - Type hints for IDE support and documentation
    - LangGraph uses these types for state validation
    
    Each agent reads from and writes to this state.
    The Annotated[..., operator.add] syntax means list fields
    get appended to rather than replaced (useful for collecting results).
    """
    # Inputs (set once at start)
    resume_text: str
    jd_text: str
    job_title: str
    company: str
    
    # Fit analysis output (used by other agents)
    fit_analysis: Optional[dict]
    
    # Final outputs
    resume_rewrite: Optional[str]
    cover_letter: Optional[str]
    interview_qa: Optional[str]
    
    # Error tracking
    errors: Annotated[List[str], operator.add]


# ============================================================
# LLM CONFIGURATION
# ============================================================

def get_llm():
    """
    Get configured LLM client.
    
    Using Groq with Llama 3.3 70B:
    - Free tier available
    - Very fast inference
    - Capable enough for all our tasks
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model_name=settings.default_model,
        temperature=0.7,  # Some creativity for writing tasks
        max_tokens=4096,
    )


# ============================================================
# AGENT NODE FUNCTIONS
# ============================================================

async def fit_analysis_node(state: PipelineState) -> dict:
    """
    Run fit analysis on resume vs job description.
    
    This MUST run first - other agents depend on its output.
    
    Returns:
        Dict with keys to update in state
    """
    try:
        llm = get_llm()
        result = await analyze_fit(
            llm=llm,
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            job_title=state["job_title"],
            company=state["company"]
        )
        return {"fit_analysis": result}
    except Exception as e:
        return {"errors": [f"Fit analysis failed: {str(e)}"]}


async def resume_writer_node(state: PipelineState) -> dict:
    """
    Rewrite resume based on fit analysis.
    
    Uses fit analysis to know which skills to emphasize
    and which JD keywords to incorporate.
    """
    try:
        llm = get_llm()
        result = await rewrite_resume(
            llm=llm,
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            fit_analysis=state["fit_analysis"],
            job_title=state["job_title"]
        )
        return {"resume_rewrite": result}
    except Exception as e:
        return {"errors": [f"Resume rewrite failed: {str(e)}"]}


async def cover_letter_node(state: PipelineState) -> dict:
    """
    Generate tailored cover letter.
    
    Uses fit analysis to highlight strongest matches.
    """
    try:
        llm = get_llm()
        result = await write_cover_letter(
            llm=llm,
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            fit_analysis=state["fit_analysis"],
            job_title=state["job_title"],
            company=state["company"]
        )
        return {"cover_letter": result}
    except Exception as e:
        return {"errors": [f"Cover letter failed: {str(e)}"]}


async def interviewer_node(state: PipelineState) -> dict:
    """
    Generate mock interview questions with sample answers.
    
    Questions are grounded in the specific role and resume.
    """
    try:
        llm = get_llm()
        result = await generate_interview_qa(
            llm=llm,
            resume_text=state["resume_text"],
            jd_text=state["jd_text"],
            fit_analysis=state["fit_analysis"],
            job_title=state["job_title"],
            company=state["company"]
        )
        return {"interview_qa": result}
    except Exception as e:
        return {"errors": [f"Interview Q&A failed: {str(e)}"]}


# ============================================================
# BUILD THE GRAPH
# ============================================================

def build_pipeline_graph() -> StateGraph:
    """
    Construct the LangGraph workflow.
    
    Graph structure:
    #START -> fit_analysis -> [resume_writer, cover_letter, interviewer] -> END
    START
    ↓
    fit_analysis_agent
        ├── resume_writer_agent
        ├── cover_letter_agent
        └── interviewer_agent
              ↓
            END
    The three writer agents run in parallel after fit analysis completes.
    """
    # Create graph with our state schema
    workflow = StateGraph(PipelineState)
    
    # Add nodes (each node is a function that updates state)
    workflow.add_node("fit_analysis_agent", fit_analysis_node)#added extra changed from fit_analysis to fit_analysis_agent
    workflow.add_node("resume_writer_agent", resume_writer_node)#added extra changed from resume_writer to resume_writer_agent
    workflow.add_node("cover_letter_agent", cover_letter_node)#added extra changed from cover_letter to cover_letter_agent
    workflow.add_node("interviewer_agent", interviewer_node)#added extra changed from interviewer to interviewer_agent
    
    # Define edges
    # START -> fit_analysis_agent (always runs first)
    workflow.add_edge(START, "fit_analysis_agent")#added extra changed from fit_analysis to fit_analysis_agent
    
    # fit_analysis_agent -> all three writers (parallel)
    # Using add_edge creates sequential flow
    # For true parallel execution, you'd use a fan-out pattern
    workflow.add_edge("fit_analysis_agent", "resume_writer_agent")#added extra changed from fit_analysis to fit_analysis_agent
    workflow.add_edge("fit_analysis_agent", "cover_letter_agent")#added extra changed from fit_analysis to fit_analysis_agent
    workflow.add_edge("fit_analysis_agent", "interviewer_agent")#added extra changed from fit_analysis to fit_analysis_agent
    
    # All writers -> END
    workflow.add_edge("resume_writer_agent", END)#added extra changed from resume_writer to resume_writer_agent
    workflow.add_edge("cover_letter_agent", END)#added extra changed from cover_letter to cover_letter_agent
    workflow.add_edge("interviewer_agent", END)#added extra changed from interviewer to interviewer_agent
    
    return workflow


# Compile the graph (do this once at module load)
pipeline_graph = build_pipeline_graph().compile()


# ============================================================
# RUN FUNCTIONS
# ============================================================

async def run_pipeline(
    resume_text: str,
    jd_text: str,
    job_title: str,
    company: str
) -> dict:
    """
    Run the full multi-agent pipeline.
    
    Args:
        resume_text: Parsed resume content
        jd_text: Job description text
        job_title: Target position
        company: Target company
    
    Returns:
        Dict with all generated artifacts:
        - fit_analysis: dict
        - resume_rewrite: str
        - cover_letter: str
        - interview_qa: str
    
    Raises:
        Exception if pipeline fails
    """
    # Initialize state
    initial_state: PipelineState = {
        "resume_text": resume_text,
        "jd_text": jd_text,
        "job_title": job_title,
        "company": company,
        "fit_analysis": None,
        "resume_rewrite": None,
        "cover_letter": None,
        "interview_qa": None,
        "errors": [],
    }
    
    # Run the graph
    # ainvoke runs asynchronously, returning final state
    result = await pipeline_graph.ainvoke(initial_state)
    
    # Check for errors
    if result.get("errors"):
        raise Exception("; ".join(result["errors"]))
    
    return {
        "fit_analysis": result["fit_analysis"],
        "resume_rewrite": result["resume_rewrite"],
        "cover_letter": result["cover_letter"],
        "interview_qa": result["interview_qa"],
    }


async def run_single_agent(
    agent_type: str,
    resume_text: str,
    jd_text: str,
    job_title: str,
    company: str,
    fit_analysis: dict = None
) -> str:
    """
    Run a single agent (for regeneration).
    
    If regenerating resume/cover_letter/interview_qa without
    existing fit_analysis, we run fit_analysis first.
    """
    llm = get_llm()
    
    # Get fit analysis if needed
    if fit_analysis is None and agent_type != "fit_analysis":
        fit_analysis = await analyze_fit(
            llm=llm,
            resume_text=resume_text,
            jd_text=jd_text,
            job_title=job_title,
            company=company
        )
    
    # Run the requested agent
    if agent_type == "fit_analysis":
        result = await analyze_fit(llm, resume_text, jd_text, job_title, company)
        return json.dumps(result)
    
    elif agent_type == "resume_rewrite":
        return await rewrite_resume(llm, resume_text, jd_text, fit_analysis, job_title)
    
    elif agent_type == "cover_letter":
        return await write_cover_letter(llm, resume_text, jd_text, fit_analysis, job_title, company)
    
    elif agent_type == "interview_qa":
        return await generate_interview_qa(llm, resume_text, jd_text, fit_analysis, job_title, company)
    
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")
