from app.workflow.nodes import StartNode, LLMCallNode, EndNode

# Node registry for workflow processor
NODE_REGISTRY = {
    "StartNode": StartNode,
    "LLMCallNode": LLMCallNode,
    "EndNode": EndNode,
    # Aliases for workflow node types
    "start": StartNode,
    "llm": LLMCallNode,
    "end": EndNode,
}
