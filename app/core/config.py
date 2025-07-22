import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/ai_platform"
    
    # Logging
    log_level: str = "INFO"
    
    # Cache
    cache_ttl: int = 3600  # 1 hour default TTL
    
    # API
    api_title: str = "Agent API Server"
    api_version: str = "1.0.0"
    api_description: str = "API server for AI agent processing"
    
    # Environment
    environment: str = "development"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
