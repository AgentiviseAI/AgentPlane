from fastapi import APIRouter, HTTPException, Depends
from typing import Tuple
from uuid import UUID
from app.core import logger, metrics
from app.schemas import ExecuteRequest, ExecuteResponse
from app.middleware import RequireAgentExecute
from app.api.dependencies import get_workflow_service
from app.services import WorkflowService

router = APIRouter()


@router.post("/execute", response_model=ExecuteResponse)
async def execute(
    request: ExecuteRequest,
    auth_context: Tuple[UUID, UUID, UUID] = Depends(RequireAgentExecute),
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Execute agent workflow with user prompt"""
    user_id, organization_id, agent_id = auth_context
    
    try:
        logger.info(f"Executing agent workflow for agent: {agent_id}), user: {user_id}, org: {organization_id}")
        metrics.increment_counter("api.execute.requests", 1)
        
        response = await workflow_service.execute(request, user_id, organization_id, agent_id)
        
        metrics.increment_counter("api.execute.success", 1)
        logger.info(f"Agent workflow executed successfully for agent: {agent_id}")
        
        return response
    except ValueError as e:
        logger.warning(f"Bad request for agent {agent_id}: {e}")
        metrics.increment_counter("api.execute.errors", 1, {"type": "not_found"})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error executing agent workflow for agent {agent_id}: {e}")
        metrics.increment_counter("api.execute.errors", 1, {"type": "internal"})
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.core.config import settings
    return {
        "status": "healthy", 
        "service": "Agent API Server",
        "version": settings.api_version,
        "environment": settings.environment
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Agent API Server is running"}
