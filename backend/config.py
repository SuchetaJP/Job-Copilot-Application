"""
config.py - Application configuration using Pydantic Settings

WHY PYDANTIC SETTINGS?
- Automatically loads from environment variables
- Type validation (catches misconfiguration early)
- Single source of truth for all configuration
- .env file support built-in
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Each attribute corresponds to an environment variable.
    The 'model_config' tells Pydantic where to find the .env file.
    """
    
    # Database
    database_url: str = "sqlite:///./copilot.db"
    
    # JWT Authentication
    secret_key: str  # No default - must be set in .env
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # LLM Providers
    groq_api_key: str  # No default - must be set
    openai_api_key: str = ""  # Optional fallback
    
    # Model settings
    default_model: str = "llama-3.3-70b-versatile"
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # Ignore extra env vars
    }


@lru_cache()  # Cache the settings - only read .env once
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    
    WHY LRU_CACHE?
    Reading .env file is I/O. We only need to do it once.
    lru_cache memoizes the result - subsequent calls return cached value.
    """
    return Settings()

#print("SECRET_KEY =", os.getenv("SECRET_KEY"))

#settings = get_settings()
#print(settings.SECRET_KEY)
#print(settings.SECRET_KEY)
