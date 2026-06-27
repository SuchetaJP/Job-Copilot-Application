"""
models.py - SQLAlchemy ORM models

These classes define the database tables and their relationships.
Each class = one table. Each attribute = one column.

TABLE STRUCTURE:
- users: Authentication and user identity
- roles: Job applications (one user has many roles)
- drafts: Generated artifacts (one role has many drafts)
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class DraftType(enum.Enum):
    """
    Enum for the four types of drafts we generate.
    
    WHY AN ENUM?
    - Restricts values to known types (database-level validation)
    - IDE autocomplete and type checking
    - Self-documenting code
    """
    FIT_ANALYSIS = "fit_analysis"
    RESUME_REWRITE = "resume_rewrite"
    COVER_LETTER = "cover_letter"
    INTERVIEW_QA = "interview_qa"


class ApplicationStatus(enum.Enum):
    """Status of a job application."""
    not_yet = "not_yet"
    # APPLIED = "applied"
    applied = "applied"
    rejected = "rejected"
    interviewed = "interviewed"
    #added extra
    
    # REVIEWING = "reviewing"
    # INTERVIEW = "interview"
    # OFFER = "offer"
    # REJECTED = "rejected"


class User(Base):
    """
    User account for authentication.
    
    We keep this minimal - just what's needed for auth.
    Users can have many job applications (roles).
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship: one user has many roles
    # back_populates creates a two-way link (role.user also works)
    roles = relationship("Role", back_populates="user", cascade="all, delete-orphan")


class Role(Base):
    """
    A job application / role the user is applying for.
    
    WHY "ROLE" NOT "APPLICATION"?
    "Application" is overloaded in programming. "Role" is clearer:
    it's the job role they're applying for.
    
    Stores:
    - Original resume text (parsed from PDF)
    - Job description text
    - Company/job title metadata
    - Application status
    """
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    jd_text = Column(Text, nullable=False)  # The job description
    jd_url = Column(String(500))  # Optional: source URL
    
    # Original resume (parsed text, structured as JSON)
    original_resume = Column(Text, nullable=False)
    
    # Status tracking
    status = Column(
        Enum(ApplicationStatus),
        default=ApplicationStatus
    )
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="roles")
    drafts = relationship("Draft", back_populates="role", cascade="all, delete-orphan")


class Draft(Base):
    """
    A generated artifact for a specific role.
    
    Each role can have multiple drafts (one of each type).
    Supports revisions - each new generation creates a new draft
    with an incremented version number.
    """
    __tablename__ = "drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    
    # What type of draft is this?
    draft_type = Column(Enum(DraftType), nullable=False)
    
    # The actual content (markdown/text)
    content = Column(Text, nullable=False)
    
    # Version tracking for regeneration
    version = Column(Integer, default=1)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship back to role
    role = relationship("Role", back_populates="drafts")
