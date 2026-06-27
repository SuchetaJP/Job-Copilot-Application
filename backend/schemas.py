"""
schemas.py - Pydantic models for API request/response validation

WHY SEPARATE FROM SQLALCHEMY MODELS?
1. SQLAlchemy models = database structure
2. Pydantic schemas = API contract (what clients send/receive)

They often look similar but serve different purposes:
- API might expose less than DB stores (hide hashed_password)
- API might transform data (combine fields, format dates)
- Pydantic validates incoming data before it hits the database
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================================
# ENUMS (must match database enums)
# ============================================================

class DraftType(str, Enum):
    """Draft type enum for API."""
    FIT_ANALYSIS = "fit_analysis"
    RESUME_REWRITE = "resume_rewrite"
    COVER_LETTER = "cover_letter"
    INTERVIEW_QA = "interview_qa"


class ApplicationStatus(str, Enum):
    """Application status enum for API."""
    not_yet = "not_yet"
    applied = "applied"
    rejected = "rejected"
    interviewed = "interviewed"


# ============================================================
# USER SCHEMAS
# ============================================================

class UserCreate(BaseModel):
    """
    Schema for user registration.
    
    EmailStr validates that the email is properly formatted.
    Field(...) with min_length ensures password has at least 8 chars.
    """
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """
    Schema for returning user data.
    
    NOTE: No password field! Never expose passwords in responses.
    
    model_config with from_attributes=True allows creating this
    from a SQLAlchemy model instance directly.
    """
    id: int
    email: str
    created_at: datetime
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


# ============================================================
# DRAFT SCHEMAS
# ============================================================

class DraftBase(BaseModel):
    """Base schema for drafts."""
    draft_type: DraftType
    content: str


class DraftCreate(DraftBase):
    """Schema for creating a draft (internal use)."""
    role_id: int
    version: int = 1


class DraftResponse(DraftBase):
    """Schema for returning draft data."""
    id: int
    role_id: int
    version: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


# ============================================================
# ROLE SCHEMAS
# ============================================================

class RoleCreate(BaseModel):
    """
    Schema for creating a new job application.
    
    The resume comes as a file upload (handled separately).
    This schema handles the text fields.
    """
    job_title: str = Field(..., min_length=1, max_length=255)
    company: str = Field(..., min_length=1, max_length=255)
    jd_text: str = Field(..., min_length=50)  # JD should have some content
    jd_url: Optional[str] = None


class RoleUpdate(BaseModel):
    """Schema for updating role status."""
    status: ApplicationStatus


class RoleResponse(BaseModel):
    """Schema for returning role data."""
    id: int
    job_title: str
    company: str
    jd_text: str
    jd_url: Optional[str]
    original_resume: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: Optional[datetime]
    drafts: List[DraftResponse] = []
    
    model_config = {"from_attributes": True}


class RoleListItem(BaseModel):
    """Simplified role data for list views."""
    id: int
    job_title: str
    company: str
    status: ApplicationStatus
    created_at: datetime
    draft_count: int = 0
    
    model_config = {"from_attributes": True}


# ============================================================
# APPLICATION PIPELINE SCHEMAS
# ============================================================

class PipelineInput(BaseModel):
    """
    Input for the multi-agent pipeline.
    
    This is what gets passed to LangGraph orchestrator.
    """
    resume_text: str
    jd_text: str
    job_title: str
    company: str


class FitAnalysisResult(BaseModel):
    """Output from the fit analysis agent."""
    requirements_met: List[str]
    requirements_not_met: List[str]
    requirements_partial: List[str]
    emphasis_recommendations: List[str]
    overall_fit_score: int = Field(..., ge=0, le=100)
    summary: str


class PipelineOutput(BaseModel):
    """Complete output from the multi-agent pipeline."""
    fit_analysis: FitAnalysisResult
    resume_rewrite: str
    cover_letter: str
    interview_qa: str  # Formatted as markdown with Q&A pairs
