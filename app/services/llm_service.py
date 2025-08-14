"""
LLM Service - Handles LLM entity operations via ControlTower
"""
from typing import Optional, List
from app.middleware.controltower_client import ControlTowerClient
from app.schemas.llm import LLMResponse


class LLMService:
    """Service for managing LLM entities via ControlTower"""
    
    def __init__(self, controltower_client: ControlTowerClient):
        self.controltower_client = controltower_client
    
    async def get_by_id(self, llm_id: str) -> Optional[LLMResponse]:
        """Get LLM by ID from ControlTower"""
        return await self.controltower_client.get_llm(llm_id)
    
    async def list_llms(self) -> List[LLMResponse]:
        """List available LLMs from ControlTower"""
        # This would be implemented when ControlTower exposes a list LLMs endpoint
        # For now, return empty list
        return []
