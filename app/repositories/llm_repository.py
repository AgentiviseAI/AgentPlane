"""
LLM Repository implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.llm import LLM


class LLMRepository:
    """Repository for LLM operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_enabled_llms(self) -> List[LLM]:
        """Get all enabled LLMs"""
        result = await self.db.execute(select(LLM).where(LLM.enabled == True))
        return result.scalars().all()
    
    async def get_by_hosting_environment(self, hosting_environment: str) -> List[LLM]:
        """Get LLMs by hosting environment"""
        result = await self.db.execute(select(LLM).where(LLM.hosting_environment == hosting_environment))
        return result.scalars().all()
    
    async def get_by_id(self, llm_id: str) -> Optional[LLM]:
        """Get LLM by ID"""
        result = await self.db.execute(select(LLM).where(LLM.id == llm_id))
        return result.scalar_one_or_none()
