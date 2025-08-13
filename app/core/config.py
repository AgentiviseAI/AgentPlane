"""
Core configuration and settings module
"""
import os
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional, List, Union
from dotenv import load_dotenv


def load_environment():
    """Load environment based on ENVIRONMENT variable"""
    # Check for environment from multiple sources
    env = os.getenv("ENVIRONMENT")
    
    # If no environment is set or set to something other than 'prod', default to 'dev'
    if env != "prod":
        env = "dev"
    
    if env == "prod":
        env_file = ".env.prod"
    else:
        env_file = ".env.dev"
    
    # Load the environment file if it exists
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        print(f"Environment file {env_file} not found, using defaults")


# Load environment before creating settings
load_environment()


class Settings(BaseSettings):
    """Application settings"""
    
    # Application settings
    environment: str = Field(default="dev", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")
    
    # Database settings
    database_type: str = Field(default="sqlite", env="DATABASE_TYPE")
    database_url: str = Field(default="sqlite:///./agent_plane.db", env="DATABASE_URL")
    
    # Security settings
    secret_key: str = Field(default="dev-secret-key-not-for-production", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="dev-jwt-secret-key-not-for-production", env="JWT_SECRET_KEY")
    
    # CORS settings
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:3001,http://localhost:5173", env="CORS_ORIGINS")
    
    # API settings
    api_title: str = Field(default="Agent API Server", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_description: str = Field(default="API server for AI agent processing", env="API_DESCRIPTION")
    api_v1_prefix: str = Field(default="/api/v1", env="API_V1_PREFIX")
    
    # Logging settings
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Cache settings
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    # External services
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    auth_service_url: str = Field(default="http://authservice:8000", env="AUTH_SERVICE_URL")
    controltower_url: str = Field(default="http://controltower:8000", env="CONTROLTOWER_URL")

    model_config = {"env_file": ".env", "case_sensitive": False}


# Global settings instance
settings = Settings()
