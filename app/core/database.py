from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from dotenv import load_dotenv
from app.core.logging import logger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/ai_platform")

# Convert to async URL if needed
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)  # Disable SQL echo in production
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Initialize database tables"""
    from sqlalchemy import text
    logger.info("Initializing database...")
    
    try:
        async with engine.begin() as conn:
            # Check if conversations table exists
            result = await conn.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'conversations')"
            ))
            conversations_exists = result.scalar()
            
            if not conversations_exists:
                # Only create conversations table if it doesn't exist
                from app.models import Conversation
                await conn.run_sync(Conversation.__table__.create)
                logger.info("✅ Conversations table created")
            else:
                logger.info("✅ Conversations table already exists")
                
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


async def close_db():
    """Close database connections"""
    await engine.dispose()
    logger.info("Database connections closed")
