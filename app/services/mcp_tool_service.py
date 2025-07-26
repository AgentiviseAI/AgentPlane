"""
MCP Tool service for business logic
"""
from typing import List, Optional
from app.repositories.mcp_tool_repository import MCPToolRepository
from app.models import MCPTool


class MCPToolService:
    """Service for MCP Tool business logic"""
    
    def __init__(self, repository: MCPToolRepository):
        self.repository = repository
    
    async def get_by_id(self, mcp_tool_id: str) -> Optional[MCPTool]:
        """Get MCP tool by ID"""
        return await self.repository.get_by_id(mcp_tool_id)
    
    async def get_by_name(self, name: str) -> Optional[MCPTool]:
        """Get MCP tool by name"""
        return await self.repository.get_by_name(name)
    
    async def get_all_enabled(self) -> List[MCPTool]:
        """Get all enabled MCP tools"""
        return await self.repository.get_all(enabled_only=True)
