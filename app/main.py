"""
Main application entry point
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Set default environment for direct Python execution
if not os.getenv("ENVIRONMENT"):
    os.environ["ENVIRONMENT"] = "dev"

from app.core import init_db, close_db, logger, settings, get_db
from app.core.di_container import init_container, cache_service
from app.startup.init import initialize_mcp_tools_at_startup
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting Agent API Server in {settings.environment.upper()} environment...")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Log level: {settings.log_level}")
    
    try:
        await init_db()
        logger.info("✅ Database initialized successfully")
        
        # Initialize DI container with database session
        # Get a database session for DI container initialization
        async for db_session in get_db():
            init_container(db_session, cache_service)
            logger.info("✅ DI Container initialized successfully")
            break
        
        # Initialize MCP tools and establish connections
        await initialize_mcp_tools_at_startup()
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # Don't exit in production, but log the error
    
    yield
    
    # Shutdown
    logger.info("Shutting down Agent API Server...")
    try:
        await close_db()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Database shutdown failed: {e}")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan
)

# CORS middleware using settings
origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(
    router,
    prefix=settings.api_v1_prefix
)


if __name__ == "__main__":
    logger.info(f"Starting server on 0.0.0.0:8001")
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower()
    )
