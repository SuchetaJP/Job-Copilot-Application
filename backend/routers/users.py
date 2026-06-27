"""
routers/users.py - User registration and authentication endpoints

Endpoints:
- POST /api/users/register - Create new account
- POST /api/users/login - Get JWT token
- GET /api/users/me - Get current user info
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserCreate, UserResponse, Token
from ..auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from ..config import get_settings

settings = get_settings()

# Create router with prefix and tags for OpenAPI docs
router = APIRouter(prefix="/api/users", tags=["users"])

# @router.post("/register")
# def register(user: UserCreate, db: Session = Depends(get_db)):
#     try:

#         hashed = get_password_hash(user.password)
       
#         new_user = User(
#             email=user.email,
#             hashed_password=hashed
#         )

#         db.add(new_user)
#         db.commit()
#         db.refresh(new_user)

#         return new_user

#     except Exception as e:
#         print("========== ERROR ==========")
#         print(e)
#         raise e
        

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    Args:
        user_data: Email and password from request body
        db: Database session (injected by FastAPI)
    
    Returns:
        The created user (without password)
    
    Raises:
        400 if email already exists
    """

    # Check if email already registered
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user with hashed password
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)  # Refresh to get auto-generated fields (id, created_at)
    
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate and get JWT token.
    
    WHY OAuth2PasswordRequestForm?
    It's the standard format for OAuth2 password flow:
    - Content-Type: application/x-www-form-urlencoded
    - Fields: username, password
    
    We use email as the username.
    
    Returns:
        JWT access token
    
    Raises:
        401 if credentials are invalid
    """
    # form_data.username contains the email
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with user's email as the subject
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user's info.
    
    This is a protected endpoint - requires valid JWT.
    The current_user is injected by the get_current_user dependency.
    """
    return current_user
