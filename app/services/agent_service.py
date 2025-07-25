from typing import Optional, List
from app.models import AIAgent
from app.repositories import AgentRepository
from app.core.logging import logger
from app.core.metrics import metrics, time_operation


class AgentService:
    """Service for managing AI agents"""
    
    def __init__(self, agent_repository: AgentRepository):
        self.agent_repository = agent_repository
    
    @time_operation("agent_service.get_by_id")
    async def get_by_id(self, agent_id: str) -> Optional[AIAgent]:
        """Get agent by ID"""
        try:
            logger.debug(f"Fetching agent by ID: {agent_id}")
            
            # First try to find by ID (which is a string UUID)
            agent = await self.agent_repository.get_by_id(agent_id)
            
            if agent:
                logger.debug(f"Found agent by ID: {agent.name}")
                metrics.increment_counter("agent_service.get_by_id", 1, {"method": "id", "status": "found"})
                return agent
            
            # If not found by ID, try by name
            logger.debug(f"Agent not found by ID, trying by name: {agent_id}")
            agent = await self.agent_repository.get_by_name(agent_id)
            
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
            
            agents = await self.agent_repository.get_all(skip=skip, limit=limit)
            
            logger.debug(f"Found {len(agents)} agents")
            metrics.increment_counter("agent_service.get_all", 1, {"count": str(len(agents))})
            
            return agents
            
        except Exception as e:
            logger.error(f"Error getting all agents: {e}")
            metrics.increment_counter("agent_service.get_all", 1, {"status": "error"})
            raise
