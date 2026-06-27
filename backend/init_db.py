# backend/init_db.py
"""
Script to create all database tables.

Run this once before starting the application:
    python -m backend.init_db
"""

from .database import engine, Base
from . import models  # Import models so SQLAlchemy knows about them

def init_database():
    """Create all tables defined in models.py"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Done! Database initialized.")

if __name__ == "__main__":
    init_database()
