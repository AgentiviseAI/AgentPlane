from app.pipeline.nodes import StartNode, LLMCallNode, EndNode

# Node registry for pipeline processor
NODE_REGISTRY = {
    "StartNode": StartNode,
    "LLMCallNode": LLMCallNode,
    "EndNode": EndNode,
    # Aliases for pipeline node types
    "start": StartNode,
    "llm": LLMCallNode,
    "end": EndNode,
}
