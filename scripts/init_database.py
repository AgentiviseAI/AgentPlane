import asyncio
import sys
import os

# Add the parent directory to the path so we can import app modules
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

from app.core.database import init_db
from app.core.logging import logger


async def main():
    """Main function to initialize database"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database setup complete!")


if __name__ == "__main__":
    asyncio.run(main())
