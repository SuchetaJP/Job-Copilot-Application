"""
database.py - SQLAlchemy database configuration

This file sets up the database connection and provides:
1. Engine - the connection to the database
2. SessionLocal - a factory for creating database sessions
3. Base - the declarative base class for models
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import get_settings

settings = get_settings()

# Create database engine
# 
# WHY THESE OPTIONS FOR SQLITE?
# - check_same_thread=False: SQLite by default only allows access from
#   the thread that created the connection. FastAPI uses multiple threads,
#   so we disable this check. Safe because SQLAlchemy handles connection pooling.
#
# - connect_args is only needed for SQLite. For Postgres/MySQL, remove it.

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite-specific
)

# SessionLocal is a factory - calling it creates a new database session
#
# WHY THESE OPTIONS?
# - autocommit=False: We want explicit transaction control (commit when ready)
# - autoflush=False: Don't automatically flush changes; we control when
# - bind=engine: Connect sessions to our database engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all database models
# All models inherit from this to get SQLAlchemy's ORM features
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    
    This is a generator function that:
    1. Creates a new session
    2. Yields it to the request handler
    3. Closes it when the request is done
    
    Used with FastAPI's Depends() for dependency injection.
    
    WHY A GENERATOR?
    The 'finally' block ensures the session is closed even if an error occurs.
    This prevents connection leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
