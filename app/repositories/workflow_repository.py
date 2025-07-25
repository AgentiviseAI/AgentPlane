"""
Workflow Repository implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.workflow import Workflow


class WorkflowRepository:
    """Repository for Workflow operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID"""
        result = await self.db.execute(select(Workflow).where(Workflow.id == workflow_id))
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Workflow]:
        """Get workflow by name"""
        result = await self.db.execute(select(Workflow).where(Workflow.name == name))
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[Workflow]:
        """Get all workflows"""
        result = await self.db.execute(select(Workflow))
        return result.scalars().all()
    
    async def get_by_agent_id(self, agent_id: str) -> List[Workflow]:
        """Get workflows by agent ID"""
        result = await self.db.execute(select(Workflow).where(Workflow.agent_id == agent_id))
        return result.scalars().all()
