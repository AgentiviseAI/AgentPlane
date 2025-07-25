"""
Example API endpoints demonstrating the new repository pattern
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core import get_db, logger
from app.core.di_container import get_container, init_container
from app.schemas import AIAgentResponse
from app.services import AgentService
from app.services.cache_service import InMemoryCacheService

router = APIRouter(prefix="/agents", tags=["agents"])

# Global cache service (singleton)
cache_service = InMemoryCacheService()


async def get_agent_service(db: AsyncSession = Depends(get_db)) -> AgentService:
    """Dependency to get agent service with proper DI"""
    try:
        container = get_container()
    except RuntimeError:
        container = init_container(db, cache_service)
    
    return container.agent_service


@router.get("/", response_model=List[AIAgentResponse])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get all agents with pagination - demonstrates repository pattern"""
    try:
        logger.info(f"Fetching agents with skip={skip}, limit={limit}")
        
        agents = await agent_service.get_all(skip=skip, limit=limit)
        
        # Convert to response models
        return [
            AIAgentResponse(
                id=str(agent.id),
                name=agent.name,
                description=agent.description,
                workflow_id=str(agent.workflow_id) if agent.workflow_id else None,
                enabled=agent.enabled,
                created_at=agent.created_at
            )
            for agent in agents
        ]
        
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}", response_model=AIAgentResponse)
async def get_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get a specific agent - demonstrates repository pattern"""
    try:
        logger.info(f"Fetching agent: {agent_id}")
        
        agent = await agent_service.get_by_id(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return AIAgentResponse(
            id=str(agent.id),
            name=agent.name,
            description=agent.description,
            workflow_id=str(agent.workflow_id) if agent.workflow_id else None,
            enabled=agent.enabled,
            created_at=agent.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
