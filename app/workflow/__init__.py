from app.workflow.nodes import StartNode, LLMPromptNode, EndNode, MCPToolNode


def register_node(node_type: str, node_class: type, dependencies: list = None):
    """Helper function to register a node with its dependencies"""
    NODE_REGISTRY[node_type] = {
        "class": node_class,
        "dependencies": dependencies or []
    }


# Node registry for workflow processor with dependency information
NODE_REGISTRY = {
    # Standard workflow node types - use lowercase to match API format
    "start": {
        "class": StartNode,
        "dependencies": []
    },
    "llm": {
        "class": LLMPromptNode,
        "dependencies": ["llm_service"]
    },
    "end": {
        "class": EndNode,
        "dependencies": []
    },
    "mcp_tool": {
        "class": MCPToolNode,
        "dependencies": []
    },
    
    # Example of how to add more node types with dependencies:
    # "database": {
    #     "class": DatabaseNode,
    #     "dependencies": ["database_service", "cache_service"]
    # },
    # "email": {
    #     "class": EmailNode,
    #     "dependencies": ["email_service"]
    # }
}
