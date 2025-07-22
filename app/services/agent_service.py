from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import AIAgent
from app.schemas import AIAgentCreate, AIAgentUpdate, AIAgentResponse
from app.core.logging import logger
from app.core.metrics import metrics, time_operation


class AgentService:
    """Service for managing AI agents"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @time_operation("agent_service.get_by_id")
    async def get_by_id(self, agent_id: str) -> Optional[AIAgent]:
        """Get agent by ID"""
        try:
            logger.debug(f"Fetching agent by ID: {agent_id}")
            
            # First try to find by ID (which is a string UUID)
            result = await self.session.execute(
                select(AIAgent).where(AIAgent.id == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if agent:
                logger.debug(f"Found agent by ID: {agent.name}")
                metrics.increment_counter("agent_service.get_by_id", 1, {"method": "id", "status": "found"})
                return agent
            
            # If not found by ID, try by name
            logger.debug(f"Agent not found by ID, trying by name: {agent_id}")
            result = await self.session.execute(
                select(AIAgent).where(AIAgent.name == agent_id)
            )
            agent = result.scalar_one_or_none()
            
            if agent:
                logger.debug(f"Found agent by name: {agent.name}")
                metrics.increment_counter("agent_service.get_by_id", 1, {"method": "name", "status": "found"})
            else:
                logger.warning(f"Agent not found: {agent_id}")
                metrics.increment_counter("agent_service.get_by_id", 1, {"method": "both", "status": "not_found"})
            
            return agent
            
        except Exception as e:
            logger.error(f"Error getting agent by id {agent_id}: {e}")
            metrics.increment_counter("agent_service.get_by_id", 1, {"status": "error"})
            raise
    
    @time_operation("agent_service.get_all")
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[AIAgent]:
        """Get all agents with pagination"""
        try:
            logger.debug(f"Fetching agents with skip={skip}, limit={limit}")
            
            result = await self.session.execute(
                select(AIAgent).offset(skip).limit(limit)
            )
            agents = result.scalars().all()
            
            logger.debug(f"Found {len(agents)} agents")
            metrics.increment_counter("agent_service.get_all", 1, {"count": str(len(agents))})
            
            return list(agents)
            
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            metrics.increment_counter("agent_service.get_all", 1, {"status": "error"})
            raise
    
    @time_operation("agent_service.create")
    async def create(self, agent_data: AIAgentCreate) -> AIAgent:
        """Create a new agent"""
        try:
            logger.info(f"Creating new agent: {agent_data.name}")
            
            agent = AIAgent(
                name=agent_data.name,
                description=agent_data.description,
                pipeline_id=agent_data.pipeline_id
            )
            
            self.session.add(agent)
            await self.session.commit()
            await self.session.refresh(agent)
            
            logger.info(f"Agent created successfully: {agent.id}")
            metrics.increment_counter("agent_service.create", 1, {"status": "success"})
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent: {e}")
            metrics.increment_counter("agent_service.create", 1, {"status": "error"})
            await self.session.rollback()
            raise
    
    @time_operation("agent_service.update")
    async def update(self, agent_id: str, agent_data: AIAgentUpdate) -> Optional[AIAgent]:
        """Update an existing agent"""
        try:
            logger.info(f"Updating agent: {agent_id}")
            
            agent = await self.get_by_id(agent_id)
            if not agent:
                logger.warning(f"Agent not found for update: {agent_id}")
                return None
            
            # Update only provided fields
            update_data = agent_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(agent, field, value)
            
            await self.session.commit()
            await self.session.refresh(agent)
            
            logger.info(f"Agent updated successfully: {agent.id}")
            metrics.increment_counter("agent_service.update", 1, {"status": "success"})
            
            return agent
            
        except Exception as e:
            logger.error(f"Error updating agent {agent_id}: {e}")
            metrics.increment_counter("agent_service.update", 1, {"status": "error"})
            await self.session.rollback()
            raise
    
    @time_operation("agent_service.delete")
    async def delete(self, agent_id: str) -> bool:
        """Delete an agent"""
        try:
            logger.info(f"Deleting agent: {agent_id}")
            
            agent = await self.get_by_id(agent_id)
            if not agent:
                logger.warning(f"Agent not found for deletion: {agent_id}")
                return False
            
            await self.session.delete(agent)
            await self.session.commit()
            
            logger.info(f"Agent deleted successfully: {agent_id}")
            metrics.increment_counter("agent_service.delete", 1, {"status": "success"})
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting agent {agent_id}: {e}")
            metrics.increment_counter("agent_service.delete", 1, {"status": "error"})
            await self.session.rollback()
            raise
