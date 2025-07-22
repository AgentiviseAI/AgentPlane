from app.pipeline.nodes import InputProcessorNode, LLMCallNode, ResponseFormatterNode

# Node registry for pipeline processor
NODE_REGISTRY = {
    "InputProcessorNode": InputProcessorNode,
    "LLMCallNode": LLMCallNode,
    "ResponseFormatterNode": ResponseFormatterNode,
    # Add aliases for existing pipeline node types
    "start": InputProcessorNode,
    "llm": LLMCallNode,
    "end": ResponseFormatterNode,
    "prompt_rewriter": InputProcessorNode,  # Map to input processor for now
}
