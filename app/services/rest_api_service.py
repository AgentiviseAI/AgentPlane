"""
REST API Service for AgentPlane - Communicates with ControlTower to fetch REST API configurations
"""
from typing import Optional, List
from app.middleware.controltower_client import ControlTowerClient
from app.schemas.rest_api import RestAPIResponse, RestAPIListResponse
from app.core.logging import logger


class RestAPIService:
    """Service to fetch REST API configurations from ControlTower"""
    
    def __init__(self, controltower_client: ControlTowerClient):
        self.controltower_client = controltower_client
    
    async def get_by_id(self, rest_api_id: str) -> Optional[RestAPIResponse]:
        """Fetch REST API configuration by ID from ControlTower"""
        try:
            logger.info(f"[DEV] RestAPIService - Fetching REST API {rest_api_id}")
            rest_api = await self.controltower_client.get_rest_api(rest_api_id)
            
            if rest_api:
                logger.info(f"[DEV] RestAPIService - Successfully fetched REST API: {rest_api.name}")
            else:
                logger.warning(f"[DEV] RestAPIService - REST API {rest_api_id} not found")
                
            return rest_api
            
        except Exception as e:
            logger.error(f"[DEV] RestAPIService - Failed to fetch REST API {rest_api_id}: {e}")
            raise

    async def list_apis(self, organization_id: Optional[str] = None, enabled_only: bool = True) -> RestAPIListResponse:
        """List REST APIs from ControlTower"""
        try:
            logger.info(f"[DEV] RestAPIService - Listing REST APIs (enabled_only: {enabled_only})")
            rest_apis = await self.controltower_client.list_rest_apis(enabled_only=enabled_only, organization_id=organization_id)
            
            logger.info(f"[DEV] RestAPIService - Successfully listed {len(rest_apis.items)} REST APIs")
            return rest_apis
            
        except Exception as e:
            logger.error(f"[DEV] RestAPIService - Failed to list REST APIs: {e}")
            raise
