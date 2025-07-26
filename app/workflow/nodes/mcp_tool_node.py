"""
MCP Tool Node - Handles Model Context Protocol tool execution
"""
from app.workflow.base import WorkflowNode
from app.core.logging import logger


class MCPToolNode(WorkflowNode):
    """MCP Tool execution node"""
    
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.tool_id = config.get('link')  # Tool ID from configuration
        self.tool_config = config.get('config', {})
        self.mcp_tool_entity = None
        self.mcp_tool_initialized = False
        logger.info(f"[DEV] MCPToolNode initialized - ID: {node_id}, Tool: {self.tool_id}")
    
    async def _fetch_mcp_tool_entity(self):
        """Fetch MCP tool entity from database using MCPToolService"""        
        if self.mcp_tool_initialized:
            return
            
        # Get MCP tool ID from config (now includes root-level fields like 'link')
        mcp_tool_id = self.tool_id
        logger.info(f"[DEV] MCPToolNode - Extracted MCP Tool ID: {mcp_tool_id}")
        
        if not mcp_tool_id or mcp_tool_id == "None":
            logger.error(f"[DEV] MCPToolNode - No MCP Tool ID found or ID is None. Config: {self.config}")
            raise ValueError("MCP Tool ID not found in node configuration. Please select an MCP tool for this node. Expected valid 'link' field.")
        
        # Get MCP tool through service layer using late import to avoid circular dependencies
        try:
            import app.core.di_container as di_module
            container = di_module.get_container()
            mcp_tool_service = container.mcp_tool_service
            self.mcp_tool_entity = await mcp_tool_service.get_by_id(mcp_tool_id)
        except RuntimeError as e:
            logger.error(f"[DEV] MCPToolNode - DI Container not initialized: {e}")
            raise ValueError("Service container not available. Make sure the application is properly initialized.")
        except ImportError as e:
            logger.error(f"[DEV] MCPToolNode - Failed to import DI Container: {e}")
            raise ValueError("Service container unavailable due to import issues.")
            
        if not self.mcp_tool_entity:
            raise ValueError(f"MCP tool with ID {mcp_tool_id} not found in database")
            
        if not self.mcp_tool_entity.enabled:
            raise ValueError(f"MCP tool {self.mcp_tool_entity.name} is disabled")
            
        logger.info(f"[DEV] MCPToolNode - Fetched MCP Tool: {self.mcp_tool_entity.name} ({self.mcp_tool_entity.endpoint_url})")
        self.mcp_tool_initialized = True
    
    async def process(self, context: dict) -> dict:
        """Process the MCP tool execution"""
        logger.info(f"[DEV] MCPToolNode.process() - Starting MCP tool execution for node: {self.node_id}")
        logger.info(f"[DEV] MCPToolNode - Tool ID: {self.tool_id}")
        logger.info(f"[DEV] MCPToolNode - Tool Config: {self.tool_config}")
        logger.info(f"[DEV] MCPToolNode - Input Context Keys: {list(context.keys())}")
        
        try:
            # Fetch MCP tool entity if not already done
            await self._fetch_mcp_tool_entity()
            
            logger.info(f"[DEV] MCPToolNode - Using MCP tool: {self.mcp_tool_entity.name}")
            logger.info(f"[DEV] MCPToolNode - Endpoint URL: {self.mcp_tool_entity.endpoint_url}")
            logger.info(f"[DEV] MCPToolNode - Transport: {self.mcp_tool_entity.transport}")
            
            # TODO: Implement actual MCP tool execution
            # For now, just log and pass through the context
            logger.info(f"[DEV] MCPToolNode - Simulating MCP tool '{self.mcp_tool_entity.name}' execution")
            
            # Simulate some tool output using the real entity data
            tool_result = {
                "tool_output": f"Simulated output from MCP tool {self.mcp_tool_entity.name}",
                "tool_status": "success",
                "tool_metadata": {
                    "tool_id": self.mcp_tool_entity.id,
                    "tool_name": self.mcp_tool_entity.name,
                    "endpoint_url": self.mcp_tool_entity.endpoint_url,
                    "transport": self.mcp_tool_entity.transport,
                    "execution_time": "0.1s",
                    "config_used": self.tool_config
                }
            }
            
            # Add tool result to context
            updated_context = {
                **context,
                "mcp_tool_result": tool_result,
                "last_tool_output": tool_result["tool_output"]
            }
            
            logger.info(f"[DEV] MCPToolNode - Tool execution completed successfully")
            logger.info(f"[DEV] MCPToolNode - Output Context Keys: {list(updated_context.keys())}")
            
            return updated_context
            
        except Exception as e:
            logger.error(f"[DEV] MCPToolNode - Error during tool execution: {str(e)}")
            
            # Return context with error information
            error_context = {
                **context,
                "mcp_tool_result": {
                    "tool_output": f"Error executing MCP tool {self.tool_id}: {str(e)}",
                    "tool_status": "error",
                    "error_details": str(e)
                }
            }
            
            return error_context
