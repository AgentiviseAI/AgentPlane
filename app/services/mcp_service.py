"""
MCP Service for managing MCP tools via ControlTower API
"""
import logging
from typing import List, Optional
from app.middleware.controltower_client import ControlTowerClient
from app.models.mcp_tool import MCPTool

logger = logging.getLogger(__name__)


class MCPService:
    """Service for managing MCP tools through ControlTower API"""
    
    def __init__(self, client: Optional[ControlTowerClient] = None):
        self.client = client or ControlTowerClient()
    
    async def get_enabled_mcp_tools(self, user_id: Optional[str] = None) -> List[MCPTool]:
        """Get all enabled MCP tools from ControlTower"""
        try:
            # Get all MCP tools from ControlTower
            mcp_tools_response = await self.client.get_mcp_tools(user_id)
            
            # Convert to MCPTool objects and filter enabled ones
            enabled_tools = []
            for tool_response in mcp_tools_response:
                tool_dict = tool_response.dict()
                # Map the API response fields to MCPTool fields
                mcp_tool_data = {
                    'id': tool_dict.get('id'),
                    'name': tool_dict.get('name', ''),
                    'description': tool_dict.get('description'),
                    'endpoint_url': tool_dict.get('command', ''),  # Map 'command' to 'endpoint_url'
                    'transport': 'streamable_http',  # Default transport
                    'is_enabled': True,  # Assume enabled if returned by API
                    'created_at': tool_dict.get('created_at'),
                    'updated_at': tool_dict.get('updated_at')
                }
                
                # Check if the tool has required fields
                if mcp_tool_data['name'] and mcp_tool_data['endpoint_url']:
                    enabled_tools.append(MCPTool(**mcp_tool_data))
                else:
                    logger.warning(f"Skipping MCP tool with missing required fields: {tool_dict}")
            
            return enabled_tools
            
        except Exception as e:
            logger.error(f"Failed to get enabled MCP tools: {e}")
            raise
    
    async def close(self):
        """Close the service's HTTP client"""
        if self.client:
            await self.client.close()
