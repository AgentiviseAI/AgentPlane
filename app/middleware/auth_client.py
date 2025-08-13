"""
Auth Service Client
Simple client to communicate with AuthService for token validation
"""
import httpx
import logging
from typing import Optional, Dict, Any
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthServiceClient:
    """Client for communicating with AuthService"""
    
    def __init__(self):
        self.auth_service_url = settings.auth_service_url
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate token with AuthService and return user info
        """
           
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": f"Bearer {token}"}
                response = await client.get(
                    f"{self.auth_service_url}/auth/userid",
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid token")
                
                response.raise_for_status()
                data = response.json()
                
                if not data.get("valid"):
                    raise HTTPException(status_code=401, detail="Token validation failed")
                
                return data.get("user", {})
                
        except httpx.RequestError as e:
            logger.error(f"Failed to validate token with AuthService: {e}")
            raise HTTPException(status_code=503, detail="Authentication service unavailable")
        except httpx.HTTPStatusError as e:
            logger.error(f"AuthService returned error: {e.response.status_code}")
            raise HTTPException(status_code=401, detail="Token validation failed")


# Global instance
auth_client = AuthServiceClient()
