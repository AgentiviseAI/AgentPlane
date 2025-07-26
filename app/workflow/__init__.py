from app.workflow.nodes import StartNode, LLMCallNode, EndNode, MCPToolNode

# Node registry for workflow processor
NODE_REGISTRY = {
    # Standard workflow node types - use lowercase to match API format
    "start": StartNode,
    "llm": LLMCallNode,
    "end": EndNode,
    "mcp_tool": MCPToolNode,
}
