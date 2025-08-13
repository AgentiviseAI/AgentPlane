"""
ControlTower API Client
Handles API calls to the ControlTower service for agent, workflow, and other resources
"""
import aiohttp
import logging
from typing import Optional, List
from app.core.config import settings
from app.core.auth_context import get_current_user_id
from app.schemas import AIAgentResponse, WorkflowResponse, LLMResponse, MCPToolResponse, SecurityRoleResponse

logger = logging.getLogger(__name__)


class ControlTowerClient:
    """Client for making API calls to ControlTower service"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.controltower_url
        self.session = None
    
    def _get_headers(self) -> dict:
        """Get standard headers for ControlTower API requests"""
        headers = {
            "Content-Type": "application/json",
            "X-Service": "AgentPlane"  # Identify the calling service
        }
        # Get user_id from auth context
        effective_user_id = get_current_user_id()
        if effective_user_id:
            headers["X-User-ID"] = effective_user_id
        return headers
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def get_agent(self, agent_id: str) -> Optional[AIAgentResponse]:
        """Get agent details from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/agents/{agent_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return AIAgentResponse(**data)
                elif response.status == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[WorkflowResponse]:
        """Get workflow details from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/workflows/{workflow_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return WorkflowResponse(**data)
                elif response.status == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get workflow {workflow_id}: {e}")
            raise
    
    async def get_llm(self, llm_id: str) -> Optional[LLMResponse]:
        """Get LLM details from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/llms/{llm_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return LLMResponse(**data)
                elif response.status == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get LLM {llm_id}: {e}")
            raise
    
    async def get_mcp_tools(self) -> List[MCPToolResponse]:
        """Get all MCP tools from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/mcp-tools", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both direct list and wrapped response formats
                    if isinstance(data, dict) and 'items' in data:
                        tools = data['items']
                    else:
                        tools = data
                    return [MCPToolResponse(**tool) for tool in tools]
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get MCP tools: {e}")
            raise
    
    async def get_mcp_tool(self, tool_id: str) -> Optional[MCPToolResponse]:
        """Get MCP tool details from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/mcp-tools/{tool_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return MCPToolResponse(**data)
                elif response.status == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get MCP tool {tool_id}: {e}")
            raise
    
    async def get_security_roles(self) -> List[SecurityRoleResponse]:
        """Get all security roles from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/security/roles", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle both direct list and wrapped response formats
                    if isinstance(data, dict) and 'items' in data:
                        roles = data['items']
                    else:
                        roles = data
                    return [SecurityRoleResponse(**role) for role in roles]
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get security roles: {e}")
            raise
    
    async def get_security_role(self, role_id: str) -> Optional[SecurityRoleResponse]:
        """Get security role details from ControlTower"""
        try:
            session = await self._get_session()
            headers = self._get_headers()
            async with session.get(f"{self.base_url}/api/v1/security/roles/{role_id}", headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return SecurityRoleResponse(**data)
                elif response.status == 404:
                    return None
                else:
                    response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to get security role {role_id}: {e}")
            raise


# Global client instance
controltower_client = ControlTowerClient()
