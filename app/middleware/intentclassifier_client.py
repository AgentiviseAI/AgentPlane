"""
IntentClassifier API Client
Handles API calls to the IntentClassifier service for intent classification
"""
import httpx
import logging
from typing import Dict, Any, List
from app.core.config import settings
from app.core.auth_context import get_current_user_id, get_current_organization_id

logger = logging.getLogger(__name__)


class IntentClassifierClient:
    """Client for making API calls to IntentClassifier service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.intentclassifier_url
    
    def _get_headers(self) -> dict:
        """Get standard headers for IntentClassifier API requests for service-to-service calls"""
        headers = {
            "Content-Type": "application/json",
            "X-Service": "AgentPlane"  # Identify the calling service
        }
        # Get user_id and organization_id from auth context
        effective_user_id = get_current_user_id()
        if effective_user_id:
            headers["X-User-ID"] = effective_user_id
        
        effective_organization_id = get_current_organization_id()
        if effective_organization_id:
            headers["X-Organization-ID"] = effective_organization_id
            
        return headers
    
    async def classify_intent(self, text: str, labels: List[str]) -> Dict[str, Any]:
        """
        Classify intent using the IntentClassifier service
        
        Args:
            text: Text to classify
            labels: List of candidate labels/intents
            
        Returns:
            Classification result with predicted intent and confidence scores
        """
        request_payload = {
            "text": text,
            "labels": labels
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/classify",
                    json=request_payload,
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"IntentClassifier: Classification successful - {result.get('intent')} (confidence: {result.get('confidence', 0):.3f})")
                    return result
                else:
                    error_text = response.text
                    logger.error(f"IntentClassifier API error {response.status_code}: {error_text}")
                    raise Exception(f"IntentClassifier API error {response.status_code}: {error_text}")
                        
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to IntentClassifier service: {e}")
            raise Exception(f"Failed to connect to IntentClassifier service: {str(e)}")
        except httpx.HTTPStatusError as e:
            logger.error(f"IntentClassifier service returned error: {e.response.status_code}")
            raise Exception(f"IntentClassifier service error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error calling IntentClassifier: {e}")
            raise Exception(f"Error calling IntentClassifier: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of the IntentClassifier service
        
        Returns:
            Service health status
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/classify/health",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"IntentClassifier health check: {result.get('status', 'unknown')}")
                    return result
                else:
                    logger.warning(f"IntentClassifier health check failed: {response.status_code}")
                    return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
                        
        except Exception as e:
            logger.error(f"IntentClassifier health check error: {e}")
            return {"status": "unavailable", "error": str(e)}


# Global client instance
intentclassifier_client = IntentClassifierClient()
