"""
auth.py - JWT authentication utilities

This module handles:
1. Password hashing (using bcrypt)
2. JWT token creation and verification
3. Getting the current user from a request

WHY JWT?
- Stateless: server doesn't need to store session data
- Scalable: works across multiple servers
- Standard: widely supported, well-understood
"""

import bcrypt

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import get_settings
from .database import get_db
from .models import User

settings = get_settings()

# Password hashing context
# bcrypt is the industry standard - slow by design to resist brute force
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme - tells FastAPI to look for "Authorization: Bearer <token>"
# tokenUrl is the endpoint where clients can get a token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a hashed password.
    
    WHY NOT COMPARE DIRECTLY?
    Passwords are stored hashed. We hash the input and compare hashes.
    bcrypt handles this comparison in constant time to prevent timing attacks.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.
    
    bcrypt automatically:
    - Generates a random salt
    - Applies multiple rounds of hashing (configurable, default ~12)
    - Encodes everything in a standard format
    """

    print("Password:", password)
    print("Length:", len(password))
    print("Type:", type(password))
    print("Bytes =", len(password.encode("utf-8")))#added extra
    print("bcrypt version =", bcrypt.__version__)    #added extra

    return pwd_context.hash(password)  


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary of claims to encode (e.g., {"sub": "user@email.com"})
        expires_delta: How long until the token expires
    
    Returns:
        Encoded JWT string
    
    JWT STRUCTURE:
    - Header: Algorithm and token type (added automatically)
    - Payload: Our data + expiration time
    - Signature: Cryptographic signature using SECRET_KEY
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode.update({"exp": expire})
    
    # Create the JWT
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that extracts and validates the current user from JWT.
    
    This is used in protected endpoints:
        @app.get("/protected")
        def protected_route(user: User = Depends(get_current_user)):
            ...
    
    FastAPI's Depends() handles:
    1. Extracting the token from Authorization header
    2. Passing it to this function
    3. Passing the result (User) to the route handler
    
    Raises HTTPException if token is invalid or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        
        # Extract user identifier from "sub" claim
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
            
    except JWTError:
        # Invalid token (expired, tampered, malformed)
        raise credentials_exception
    
    # Look up user in database
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verify credentials and return user if valid.
    
    Returns None if:
    - User doesn't exist
    - Password is wrong
    
    WHY RETURN NONE INSTEAD OF RAISING?
    The caller decides how to handle auth failure.
    Different contexts might want different error messages.
    """
    user = db.query(User).filter(User.email == email).first()
    #extra added
    if not user:
        return None

    print(user.hashed_password) #extra added
    print(len(user.hashed_password)) #extra added
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user
