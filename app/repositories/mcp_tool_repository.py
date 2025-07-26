"""
MCP Tool repository for database operations
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import MCPTool


class MCPToolRepository:
    """Repository for MCP Tool database operations"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def get_by_id(self, mcp_tool_id: str) -> Optional[MCPTool]:
        """Get MCP tool by ID"""
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.id == mcp_tool_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[MCPTool]:
        """Get MCP tool by name"""
        result = await self.db.execute(
            select(MCPTool).where(MCPTool.name == name)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, enabled_only: bool = True) -> List[MCPTool]:
        """Get all MCP tools, optionally filtering by enabled status"""
        query = select(MCPTool)
        if enabled_only:
            query = query.where(MCPTool.enabled == True)
        result = await self.db.execute(query)
        return result.scalars().all()
