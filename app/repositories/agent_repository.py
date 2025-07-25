"""
Agent Repository implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.agent import AIAgent


class AgentRepository:
    """Repository for Agent operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, agent_id: str) -> Optional[AIAgent]:
        """Get agent by ID"""
        result = await self.db.execute(select(AIAgent).where(AIAgent.id == agent_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[AIAgent]:
        """Get agent by name"""
        result = await self.db.execute(select(AIAgent).where(AIAgent.name == name))
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AIAgent]:
        """Get all agents with pagination"""
        query = select(AIAgent).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_enabled_agents(self) -> List[AIAgent]:
        """Get all enabled agents"""
        result = await self.db.execute(select(AIAgent).where(AIAgent.enabled == True))
        return result.scalars().all()
