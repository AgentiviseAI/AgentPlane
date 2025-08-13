"""
Authorization middleware for role-based access control in AgentPlane
"""
import logging
from fastapi import Request, HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Tuple, Optional
from uuid import UUID
from app.middleware.auth_client import AuthServiceClient
from app.services.authorization_service import authorization_service

# Security
security = HTTPBearer(auto_error=False)
auth_client = AuthServiceClient()
logger = logging.getLogger(__name__)


async def get_current_user_id(
    x_user_id: str = Header(None, alias="X-User-ID"),
    x_service: str = Header(None, alias="X-Service"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> UUID:
    """Validate JWT token or handle internal service calls and return user ID as UUID"""
    # Handle internal service calls (from SchedulerService, IncomingWebhookService, etc.)
    if x_user_id and x_service:
        logger.info(f"Internal service call from {x_service} for user {x_user_id}")
        try:
            return UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID format in X-User-ID header"
            )
    
    # Handle regular JWT token validation
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_data = await auth_client.validate_token(credentials.credentials)
        # Use 'id' field for user ID, fallback to 'sub' for JWT standard compatibility
        user_id_str = user_data.get("id") or user_data.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User ID not found in token"
            )
        try:
            return UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user ID format in token"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _get_agent_id_from_request(request: Request) -> UUID:
    """Extract agent_id from request headers (required)"""
    
    # Try to get agent_id from headers
    agent_id_str = request.headers.get('x-agent-id')
        
    if not agent_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required X-Agent-ID header"
        )
    
    try:
        return UUID(agent_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid agent ID format in X-Agent-ID header: {agent_id_str}"
        )


class AuthorizationMiddleware:
    """Middleware for handling authorization checks in AgentPlane"""
    
    @staticmethod
    def create_permission_dependency(resource: str, action: str):
        """
        Create a FastAPI dependency for checking specific permissions
        
        Args:
            resource: Resource type (e.g., 'agent', 'conversations')
            action: Action to perform (e.g., 'execute', 'read', 'create', 'update', 'delete')
        
        Returns:
            FastAPI dependency function that returns (user_id, organization_id, agent_id) where all are UUIDs
        """
        async def check_permission(
            request: Request,
            current_user_id: UUID = Depends(get_current_user_id),
            agent_id: UUID = Depends(_get_agent_id_from_request)
        ) -> Tuple[UUID, UUID, UUID]:
            try:
                # Get organization_id from x-organization-id header (consistent with ControlTower)
                organization_id_str = request.headers.get('x-organization-id')
                
                if not organization_id_str:
                    # Use default test organization for development/testing
                    organization_id_str = "bb5a9afd-336a-445e-99ce-e81b9d444b76"  # Default UUID format
                    print(f"[AUTH] No x-organization-id header found, using default organization: {organization_id_str}")
                else:
                    print(f"[AUTH] Found organization_id in header: {organization_id_str}")
                
                # Convert string to UUID
                try:
                    organization_id = UUID(organization_id_str)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid organization ID format: {organization_id_str}"
                    )
                
                print(f"[AUTH] Checking permissions for user: {current_user_id}, org: {organization_id}, agent: {agent_id}, resource: {resource}, action: {action}")
                
                # Authorize the request using authorization service
                has_permission = await authorization_service.authorize_request(
                    user_id=current_user_id,
                    organization_id=str(organization_id),  # AuthorizationService expects string
                    agent_id=agent_id,
                    resource=resource,
                    action=action
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions to {action} {resource}"
                    )
                
                print(f"[AUTH] Authorization successful for user: {current_user_id}")
                return current_user_id, organization_id, agent_id  # Return all as UUIDs
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Authorization error: {str(e)}"
                )
        
        return check_permission


# Pre-defined permission dependencies for AgentPlane operations
RequireAgentExecute = AuthorizationMiddleware.create_permission_dependency("agent", "execute")
