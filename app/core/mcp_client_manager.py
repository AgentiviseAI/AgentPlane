"""
MCP Client Manager for handling Model Context Protocol connections
"""
import asyncio
from typing import Dict, Any, Optional, List

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client 
from mcp.client.streamable_http import streamablehttp_client
import mcp.types as types

from app.core.logging import logger
from app.models.mcp_tool import MCPTool


class MCPClientManager:
    """Manages MCP client connections for enabled tools"""
    
    def __init__(self):
        self.active_clients: Dict[str, Dict[str, Any]] = {}
        self.initialized_tools: List[MCPTool] = []
    
    async def initialize_mcp_tool(self, tool: MCPTool) -> Optional[Dict[str, Any]]:
        """Initialize a single MCP tool and establish connection"""
        try:
            logger.info(f"[MCP] Initializing tool: {tool.name}")
            logger.info(f"[MCP]   Endpoint: {tool.endpoint_url}")
            logger.info(f"[MCP]   Transport: {tool.transport}")
            
            transport_type = tool.transport.lower().replace(" ", "_")
            
            if transport_type in ["streamable_http", "streamable-http"]:
                return await self._initialize_streamable_http_client(tool)
            elif transport_type in ["stdio", "standard_io"]:
                return await self._initialize_stdio_client(tool)
            elif transport_type in ["sse", "server_sent_events"]:
                return await self._initialize_sse_client(tool)
            else:
                logger.warning(f"[MCP] Unsupported transport type: {tool.transport} for tool: {tool.name}")
                return None
                
        except Exception as e:
            logger.error(f"[MCP] Failed to initialize tool {tool.name}: {e}")
            return None
    
    async def _initialize_streamable_http_client(self, tool: MCPTool) -> Dict[str, Any]:
        """Initialize Streamable HTTP transport client"""
        try:
            logger.info(f"[MCP] Connecting to {tool.name} via Streamable HTTP...")
            
            # Test connection and get server info
            async with streamablehttp_client(tool.endpoint_url) as (read_stream, write_stream, _):
                async with ClientSession(read_stream, write_stream) as session:
                    # Initialize connection
                    result = await session.initialize()
                    logger.info(f"[MCP] ✅ Connected to {tool.name}")
                    logger.info(f"[MCP]   Server: {result.serverInfo.name} v{result.serverInfo.version}")
                    
                    # Get available capabilities
                    tools = await session.list_tools()
                    resources = await session.list_resources()
                    prompts = await session.list_prompts()
                    
                    client_info = {
                        "tool": tool,
                        "transport": "streamable_http",
                        "status": "connected",
                        "server_info": result.serverInfo,
                        "capabilities": {
                            "tools": len(tools.tools),
                            "resources": len(resources.resources),
                            "prompts": len(prompts.prompts)
                        },
                        "tools_available": [t.name for t in tools.tools[:5]],  # Show first 5
                        "resources_available": [r.uri for r in resources.resources[:5]]
                    }
                    
                    logger.info(f"[MCP]   Capabilities: {client_info['capabilities']}")
                    if client_info['tools_available']:
                        logger.info(f"[MCP]   Sample Tools: {', '.join(client_info['tools_available'])}")
                    
                    return client_info
                    
        except Exception as e:
            logger.error(f"[MCP] Failed Streamable HTTP connection to {tool.name}: {e}")
            return {
                "tool": tool,
                "transport": "streamable_http", 
                "status": "failed",
                "error": str(e)
            }
    
    async def _initialize_stdio_client(self, tool: MCPTool) -> Dict[str, Any]:
        """Initialize STDIO transport client"""
        try:
            logger.info(f"[MCP] Connecting to {tool.name} via STDIO...")
            
            # Parse endpoint_url for command and args
            # Expected format: "command:arg1,arg2,arg3" or just "command"
            if ":" in tool.endpoint_url:
                command_part, args_part = tool.endpoint_url.split(":", 1)
                args = args_part.split(",") if args_part else []
            else:
                command_part = tool.endpoint_url
                args = []
            
            server_params = StdioServerParameters(
                command=command_part,
                args=args,
                env={}
            )
            
            # Test connection
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    result = await session.initialize()
                    logger.info(f"[MCP] ✅ Connected to {tool.name}")
                    logger.info(f"[MCP]   Server: {result.serverInfo.name} v{result.serverInfo.version}")
                    
                    # Get capabilities
                    tools = await session.list_tools()
                    resources = await session.list_resources()
                    prompts = await session.list_prompts()
                    
                    return {
                        "tool": tool,
                        "transport": "stdio",
                        "status": "connected",
                        "server_info": result.serverInfo,
                        "capabilities": {
                            "tools": len(tools.tools),
                            "resources": len(resources.resources),
                            "prompts": len(prompts.prompts)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"[MCP] Failed STDIO connection to {tool.name}: {e}")
            return {
                "tool": tool,
                "transport": "stdio",
                "status": "failed", 
                "error": str(e)
            }
    
    async def _initialize_sse_client(self, tool: MCPTool) -> Dict[str, Any]:
        """Initialize Server-Sent Events transport client"""
        try:
            logger.info(f"[MCP] Connecting to {tool.name} via SSE...")
            
            # Test connection
            async with sse_client(tool.endpoint_url) as (read, write):
                async with ClientSession(read, write) as session:
                    result = await session.initialize()
                    logger.info(f"[MCP] ✅ Connected to {tool.name}")
                    logger.info(f"[MCP]   Server: {result.serverInfo.name} v{result.serverInfo.version}")
                    
                    # Get capabilities
                    tools = await session.list_tools()
                    resources = await session.list_resources()
                    prompts = await session.list_prompts()
                    
                    return {
                        "tool": tool,
                        "transport": "sse",
                        "status": "connected",
                        "server_info": result.serverInfo,
                        "capabilities": {
                            "tools": len(tools.tools),
                            "resources": len(resources.resources),
                            "prompts": len(prompts.prompts)
                        }
                    }
                    
        except Exception as e:
            logger.error(f"[MCP] Failed SSE connection to {tool.name}: {e}")
            return {
                "tool": tool,
                "transport": "sse",
                "status": "failed",
                "error": str(e)
            }
    
    async def initialize_all_tools(self, enabled_tools: List[MCPTool]) -> Dict[str, Dict[str, Any]]:
        """Initialize all enabled MCP tools concurrently"""
        if not enabled_tools:
            logger.info("[MCP] No enabled tools found to initialize")
            return {}
        
        logger.info(f"[MCP] Initializing {len(enabled_tools)} MCP tool(s)...")
        logger.info("=" * 80)
        
        # Initialize tools concurrently with timeout
        tasks = []
        for tool in enabled_tools:
            task = asyncio.create_task(self.initialize_mcp_tool(tool))
            tasks.append((tool.name, task))
        
        # Wait for all initializations with timeout
        results = {}
        for tool_name, task in tasks:
            try:
                # 10 second timeout per tool
                result = await asyncio.wait_for(task, timeout=10.0)
                if result:
                    results[tool_name] = result
                    self.active_clients[tool_name] = result
            except asyncio.TimeoutError:
                logger.error(f"[MCP] Timeout initializing {tool_name} (10s limit)")
                results[tool_name] = {
                    "tool": next(t for t in enabled_tools if t.name == tool_name),
                    "status": "timeout",
                    "error": "Connection timeout (10s)"
                }
            except Exception as e:
                logger.error(f"[MCP] Error initializing {tool_name}: {e}")
                results[tool_name] = {
                    "tool": next(t for t in enabled_tools if t.name == tool_name),
                    "status": "error",
                    "error": str(e)
                }
        
        # Log summary
        successful = len([r for r in results.values() if r.get("status") == "connected"])
        failed = len(results) - successful
        
        logger.info("=" * 80)
        logger.info(f"[MCP] Initialization Summary: {successful} connected, {failed} failed")
        
        for tool_name, result in results.items():
            status = result.get("status", "unknown")
            if status == "connected":
                caps = result.get("capabilities", {})
                logger.info(f"[MCP] ✅ {tool_name}: {caps.get('tools', 0)} tools, {caps.get('resources', 0)} resources, {caps.get('prompts', 0)} prompts")
            else:
                error = result.get("error", "Unknown error")
                logger.info(f"[MCP] ❌ {tool_name}: {status} - {error}")
        
        logger.info("=" * 80)
        self.initialized_tools = enabled_tools
        return results

    def get_active_client(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get an active MCP client by tool name"""
        return self.active_clients.get(tool_name)
    
    def get_all_active_clients(self) -> Dict[str, Dict[str, Any]]:
        """Get all active MCP clients"""
        return self.active_clients.copy()
    
    def is_tool_connected(self, tool_name: str) -> bool:
        """Check if a specific tool is connected"""
        client = self.active_clients.get(tool_name)
        return client is not None and client.get("status") == "connected"
    
    def get_connection_summary(self) -> Dict[str, Any]:
        """Get a summary of connection statuses"""
        total = len(self.active_clients)
        connected = len([c for c in self.active_clients.values() if c.get("status") == "connected"])
        failed = total - connected
        
        return {
            "total_tools": total,
            "connected": connected,
            "failed": failed,
            "connection_rate": connected / total if total > 0 else 0
        }
