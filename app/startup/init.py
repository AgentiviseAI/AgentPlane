"""
Startup utilities for agent-api-server
"""
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from app.core.logging import logger
from app.middleware.mcp_client_manager import MCPClientManager
from app.services.mcp_service import MCPService


# Global MCP client manager instance
mcp_manager = MCPClientManager()


async def initialize_mcp_tools_at_startup():
    """Initialize MCP tools and establish client connections during application startup"""
    try:
        logger.info("[STARTUP] Fetching enabled MCP tools from ControlTower...")
        
        # Use MCPService to get enabled tools via ControlTower API
        mcp_service = MCPService()
        try:
            enabled_tools = await mcp_service.get_enabled_mcp_tools()
            
            if not enabled_tools:
                logger.info("[STARTUP] No enabled MCP tools found")
                return
            
            logger.info(f"[STARTUP] Found {len(enabled_tools)} enabled MCP tool(s)")
            
            # Display tool information
            logger.info("=" * 80)
            for tool in enabled_tools:
                logger.info(f"[MCP] Tool Name: {tool.name}")
                logger.info(f"[MCP]   Endpoint: {tool.endpoint_url}")
                logger.info(f"[MCP]   Transport: {tool.transport}")
                if tool.description:
                    logger.info(f"[MCP]   Description: {tool.description}")
                logger.info("-" * 40)
            logger.info("=" * 80)
            
            # Initialize MCP clients for each tool
            logger.info("[STARTUP] Initializing MCP client connections...")
            initialization_results = await mcp_manager.initialize_all_tools(enabled_tools)
            
            # Log final startup status
            successful_connections = len([r for r in initialization_results.values() if r.get("status") == "connected"])
            logger.info(f"[STARTUP] MCP initialization completed: {successful_connections}/{len(enabled_tools)} tools connected successfully")
            
        except Exception as e:
            logger.error(f"[STARTUP] Error fetching MCP tools from ControlTower: {e}")
        finally:
            # Clean up the service's HTTP client
            await mcp_service.close()
                
    except Exception as e:
        logger.error(f"[STARTUP] Failed to initialize MCP tools: {e}")


def get_mcp_manager() -> MCPClientManager:
    """Get the global MCP client manager instance"""
    return mcp_manager
