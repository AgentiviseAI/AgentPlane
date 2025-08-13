"""
MCP Tool model for AgentPlane
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class MCPTool(BaseModel):
    """MCP Tool model for client manager compatibility"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    endpoint_url: str
    transport: str = "streamable_http"
    is_enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'MCPTool':
        """Create MCPTool from API response data"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            endpoint_url=data.get('endpoint_url', ''),
            transport=data.get('transport', 'streamable_http'),
            is_enabled=data.get('is_enabled', True),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at')
        )
