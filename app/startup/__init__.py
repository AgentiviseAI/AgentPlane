"""
Startup package for AgentPlane
"""
from .init import (
    initialize_mcp_tools_at_startup,
    get_mcp_manager,
    mcp_manager
)

__all__ = [
    "initialize_mcp_tools_at_startup",
    "get_mcp_manager", 
    "mcp_manager"
]
