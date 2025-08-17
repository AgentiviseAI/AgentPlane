"""
Node package initialization
Workflow nodes are organized by category for better maintainability:
- core: Essential workflow entry/exit nodes (start, end)
- intelligence: AI/ML-powered nodes (llm_prompt, intent_extractor)
- logical: Control flow nodes (if_else, switch)
- tools: External integrations (mcp_tool, rest_api)

This file also provides direct imports from reorganized node folders
for backward compatibility while nodes are now organized by category.
"""
# Import from organized subfolders
from .core import StartNode, EndNode
from .intelligence import LLMPromptNode, IntentExtractorNode
from .logical import IfElseNode, SwitchNode
from .tools import MCPToolNode, RestApiNode

# Also provide direct imports for backward compatibility
from .core.start_node import StartNode
from .core.end_node import EndNode
from .intelligence.llm_prompt_node import LLMPromptNode
from .intelligence.intent_extractor_node import IntentExtractorNode
from .logical.if_else_node import IfElseNode
from .logical.switch_node import SwitchNode
from .tools.mcp_tool_node import MCPToolNode
from .tools.rest_api_node import RestApiNode

__all__ = [
    "StartNode", 
    "EndNode", 
    "LLMPromptNode", 
    "IntentExtractorNode", 
    "IfElseNode", 
    "SwitchNode", 
    "MCPToolNode", 
    "RestApiNode"
]
