from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core import get_db, logger, metrics
from app.core.di_container import get_container, init_container
from app.schemas import ProcessPromptRequest, ProcessPromptResponse
from app.services import WorkflowService
from app.services.cache_service import InMemoryCacheService

router = APIRouter()

# Global cache service (singleton)
cache_service = InMemoryCacheService()


async def get_workflow_service(db: AsyncSession = Depends(get_db)) -> WorkflowService:
    """Dependency to get workflow service"""
    # Initialize DI container if not already done
    try:
        container = get_container()
    except RuntimeError:
        container = init_container(db, cache_service)
    
    return container.workflow_service


@router.post("/process_prompt", response_model=ProcessPromptResponse)
async def process_prompt(
    request: ProcessPromptRequest,
    workflow_service: WorkflowService = Depends(get_workflow_service)
):
    """Process a user prompt through the agent workflow"""
    try:
        logger.info(f"Processing prompt request for agent: {request.agentid}")
        metrics.increment_counter("api.process_prompt.requests", 1)
        
        response = await workflow_service.process_prompt(request)
        
        metrics.increment_counter("api.process_prompt.success", 1)
        logger.info(f"Prompt processed successfully for agent: {request.agentid}")
        
        return response
    except ValueError as e:
        logger.warning(f"Bad request for agent {request.agentid}: {e}")
        metrics.increment_counter("api.process_prompt.errors", 1, {"type": "not_found"})
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Internal error processing prompt for agent {request.agentid}: {e}")
        metrics.increment_counter("api.process_prompt.errors", 1, {"type": "internal"})
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


@router.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        "metrics": metrics.get_metrics(),
        "cache_stats": cache_service.get_stats()
    }


@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Agent API Server is running"}
