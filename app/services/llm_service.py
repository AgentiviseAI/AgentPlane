from typing import Optional, List
from app.models import LLM
from app.repositories import LLMRepository
from app.core.logging import logger
from app.core.metrics import metrics, time_operation


class LLMService:
    """Service for managing LLMs (read-only)"""
    
    def __init__(self, llm_repository: LLMRepository):
        self.llm_repository = llm_repository
    
    @time_operation("llm_service.get_by_id")
    async def get_by_id(self, llm_id: str) -> Optional[LLM]:
        """Get LLM by ID"""
        try:
            logger.debug(f"Fetching LLM by ID: {llm_id}")
            
            llm = await self.llm_repository.get_by_id(llm_id)
            
            if llm:
                logger.debug(f"Found LLM: {llm.name}")
                metrics.increment_counter("llm_service.get_by_id", 1, {"status": "found"})
            else:
                logger.warning(f"LLM not found: {llm_id}")
                metrics.increment_counter("llm_service.get_by_id", 1, {"status": "not_found"})
            
            return llm
            
        except Exception as e:
            logger.error(f"Error getting LLM by id {llm_id}: {e}")
            metrics.increment_counter("llm_service.get_by_id", 1, {"status": "error"})
            raise
    
    @time_operation("llm_service.get_enabled")
    async def get_enabled(self) -> List[LLM]:
        """Get all enabled LLMs"""
        try:
            logger.debug("Fetching enabled LLMs")
            
            llms = await self.llm_repository.get_enabled_llms()
            
            logger.debug(f"Found {len(llms)} enabled LLMs")
            metrics.increment_counter("llm_service.get_enabled", 1, {"count": str(len(llms))})
            
            return llms
            
        except Exception as e:
            logger.error(f"Error getting enabled LLMs: {e}")
            metrics.increment_counter("llm_service.get_enabled", 1, {"status": "error"})
            raise
    
    @time_operation("llm_service.get_by_hosting_environment")
    async def get_by_hosting_environment(self, hosting_environment: str) -> List[LLM]:
        """Get LLMs by hosting environment"""
        try:
            logger.debug(f"Fetching LLMs for hosting environment: {hosting_environment}")
            
            llms = await self.llm_repository.get_by_hosting_environment(hosting_environment)
            
            logger.debug(f"Found {len(llms)} LLMs for hosting environment: {hosting_environment}")
            metrics.increment_counter("llm_service.get_by_hosting_environment", 1, {"count": str(len(llms))})
            
            return llms
            
        except Exception as e:
            logger.error(f"Error getting LLMs by hosting environment {hosting_environment}: {e}")
            metrics.increment_counter("llm_service.get_by_hosting_environment", 1, {"status": "error"})
            raise
