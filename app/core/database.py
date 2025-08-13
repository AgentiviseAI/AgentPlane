from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from dotenv import load_dotenv
from app.core.logging import logger
from app.core.config import settings

load_dotenv()

# Use settings instead of hardcoded default
DATABASE_URL = settings.database_url

# Convert to async URL if needed (only for PostgreSQL)
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
elif DATABASE_URL.startswith("sqlite:///"):
    # For SQLite, use aiosqlite async driver
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(DATABASE_URL, echo=False)  # Disable SQL echo in production
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables"""
    from sqlalchemy import text
    logger.info("Initializing database...")
    
    try:
        async with engine.begin() as conn:
            # Check if conversations table exists (database-agnostic approach)
            if settings.database_type.lower() == "postgresql":
                # PostgreSQL-specific query
                result = await conn.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'conversations')"
                ))
                conversations_exists = result.scalar()
            else:
                # SQLite-specific query
                result = await conn.execute(text(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
                ))
                conversations_exists = result.fetchone() is not None
            
            if not conversations_exists:
                # Create all tables using Base metadata
                await conn.run_sync(Base.metadata.create_all)
                logger.info("[SUCCESS] Database tables created")
            else:
                logger.info("[SUCCESS] Database tables already exist")
                
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db():
    """Dependency to get database session"""
    async with SessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_session():
    """Get database session context manager"""
    return SessionLocal()


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
