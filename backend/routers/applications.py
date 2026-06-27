"""
routers/applications.py - Main application endpoints

Endpoints:
- POST /api/applications - Upload resume + JD, trigger pipeline
- GET /api/applications - List all roles for current user
- GET /api/applications/{id} - Get specific role with drafts
- PATCH /api/applications/{id} - Update role status
- POST /api/applications/{id}/regenerate/{type} - Regenerate specific draft
"""

import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Role, Draft, DraftType, ApplicationStatus
from ..schemas import (
    RoleResponse,
    RoleListItem,
    RoleUpdate,
    DraftResponse,
    DraftType as DraftTypeSchema,
)
from ..auth import get_current_user
from ..services.pdf_parser import parse_resume_pdf
from ..services.jd_scraper import scrape_jd_from_url
from ..agents.orchestrator import run_pipeline

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    resume: UploadFile = File(...),
    job_title: str = Form(...),
    company: str = Form(...),
    jd_text: str = Form(None),
    jd_url: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new job application and run the AI pipeline.
    
    This is the main endpoint that:
    1. Accepts resume PDF + job description
    2. Parses the resume
    3. Optionally scrapes JD from URL
    4. Runs the multi-agent pipeline
    5. Saves everything to database
    
    Args:
        resume: PDF file upload
        job_title: Target job title
        company: Company name
        jd_text: Job description text (OR jd_url, one required)
        jd_url: URL to scrape JD from
    
    Returns:
        Created role with all generated drafts
    """
    # Validate: need either jd_text or jd_url
    if not jd_text and not jd_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either jd_text or jd_url is required"
        )
    
    # Validate file type
    if not resume.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be a PDF file"
        )
    
    # Step 1: Parse resume PDF
    try:
        resume_content = await resume.read()
        parsed_resume = parse_resume_pdf(resume_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse resume: {str(e)}"
        )
    
    # Step 2: Get JD text (scrape if URL provided)
    if jd_url and not jd_text:
        try:
            jd_text = scrape_jd_from_url(jd_url)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to scrape JD from URL: {str(e)}"
            )
    
    # Step 3: Run the multi-agent pipeline
    try:
        pipeline_result = await run_pipeline(
            resume_text=parsed_resume["text"],
            jd_text=jd_text,
            job_title=job_title,
            company=company
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failed: {str(e)}"
        )
    
    # Step 4: Save to database
    role = Role(
        user_id=current_user.id,
        job_title=job_title,
        company=company,
        jd_text=jd_text,
        jd_url=jd_url,
        original_resume=json.dumps(parsed_resume),
        status=ApplicationStatus.not_yet,
    )
    db.add(role)
    db.flush()  # Get the role.id without committing
    
    # Create drafts for each pipeline output
    drafts_data = [
        (DraftType.FIT_ANALYSIS, json.dumps(pipeline_result["fit_analysis"])),
        (DraftType.RESUME_REWRITE, pipeline_result["resume_rewrite"]),
        (DraftType.COVER_LETTER, pipeline_result["cover_letter"]),
        (DraftType.INTERVIEW_QA, pipeline_result["interview_qa"]),
    ]
    
    for draft_type, content in drafts_data:
        draft = Draft(
            role_id=role.id,
            draft_type=draft_type,
            content=content,
            version=1
        )
        db.add(draft)
    
    db.commit()
    db.refresh(role)
    
    return role


@router.get("", response_model=List[RoleListItem])
def list_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all job applications for the current user.
    
    Returns simplified role data for list views (no full content).
    """
    roles = db.query(Role).filter(Role.user_id == current_user.id).order_by(
        Role.created_at.desc()
    ).all()
    
    # Add draft count to each role
    result = []
    for role in roles:
        item = RoleListItem(
            id=role.id,
            job_title=role.job_title,
            company=role.company,
            status=role.status,
            created_at=role.created_at,
            draft_count=len(role.drafts)
        )
        result.append(item)
    
    return result


@router.get("/{role_id}", response_model=RoleResponse)
def get_application(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific job application with all its drafts.
    """
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.user_id == current_user.id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    return role


@router.patch("/{role_id}", response_model=RoleResponse)
def update_application(
    role_id: int,
    update_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update application status.
    """
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.user_id == current_user.id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    role.status = update_data.status
    db.commit()
    db.refresh(role)
    
    return role


@router.post("/{role_id}/regenerate/{draft_type}", response_model=DraftResponse)
async def regenerate_draft(
    role_id: int,
    draft_type: DraftTypeSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate a specific draft for a role.
    
    Creates a new version rather than overwriting.
    This allows viewing history and rolling back.
    """
    role = db.query(Role).filter(
        Role.id == role_id,
        Role.user_id == current_user.id
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Get current version number
    current_draft = db.query(Draft).filter(
        Draft.role_id == role_id,
        Draft.draft_type == DraftType(draft_type.value)
    ).order_by(Draft.version.desc()).first()
    
    new_version = (current_draft.version + 1) if current_draft else 1
    
    # Parse stored resume
    parsed_resume = json.loads(role.original_resume)
    
    # Run single agent based on type
    from ..agents.orchestrator import run_single_agent
    
    try:
        content = await run_single_agent(
            agent_type=draft_type.value,
            resume_text=parsed_resume["text"],
            jd_text=role.jd_text,
            job_title=role.job_title,
            company=role.company
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration failed: {str(e)}"
        )
    
    # Create new draft version
    new_draft = Draft(
        role_id=role_id,
        draft_type=DraftType(draft_type.value),
        content=content,
        version=new_version
    )
    db.add(new_draft)
    db.commit()
    db.refresh(new_draft)
    
    return new_draft
