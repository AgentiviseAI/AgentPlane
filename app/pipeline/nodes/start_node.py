"""
Start Node - Marks the beginning of pipeline execution
"""
from typing import Dict, Any
from app.pipeline.base import PipelineNode
from app.core.logging import logger


class StartNode(PipelineNode):
    """Node that marks the start of pipeline execution"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        logger.info(f"[DEV] StartNode initialized - ID: {node_id}")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mark the start of pipeline execution"""
        logger.info(f"[DEV] StartNode.process() - Pipeline execution started for node: {self.node_id}")
        
        # Just pass through the state without modification
        return state
