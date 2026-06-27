"""
main.py - FastAPI application entry point

This is where everything comes together:
- CORS configuration for frontend access
- Route registration
- Startup events
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import users, applications
import traceback

# Create all database tables on startup
# In production, you'd use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title="Job Application Co-Pilot",
    description="AI-powered job application assistant",
    version="1.0.0",
)


@app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    traceback.print_exc()
    raise exc

# Configure CORS
# 
# WHAT IS CORS?
# Cross-Origin Resource Sharing - security feature that restricts
# web pages from making requests to different domains.
# 
# Our frontend (localhost:5500) needs to call backend (localhost:8000).
# Without CORS config, browser blocks these requests.
#
# WHY THESE SETTINGS?
# - allow_origins: List of allowed frontend URLs
# - allow_credentials: Allow cookies/auth headers
# - allow_methods: HTTP methods allowed
# - allow_headers: HTTP headers allowed

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        #"[localhost](http://localhost:5500)",      # VS Code Live Server
        "[127.0.0.1](http://127.0.0.1:5500)",
        #"[localhost](http://localhost:3000)",       # If using other dev server
        #"[localhost](http://localhost:8080)",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Register routers
app.include_router(users.router)
app.include_router(applications.router)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Job Application Co-Pilot"}


@app.get("/health")
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
