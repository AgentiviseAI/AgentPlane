"""
End Node - Marks the end of workflow execution
"""
from typing import Dict, Any
from app.workflow.base import WorkflowNode
from app.core.logging import logger


class EndNode(WorkflowNode):
    """Node that marks the end of workflow execution"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        logger.info(f"[DEV] EndNode initialized - ID: {node_id}")
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Mark the end of workflow execution and ensure client gets a response"""
        logger.info(f"[DEV] EndNode.process() - Workflow execution completed for node: {self.node_id}")
        
        # Check if we have a valid LLM response
        llm_response = state.get("llm_response", "")
        llm_metadata = state.get("llm_metadata", {})
        
        # If no response or there was an error, provide fallback
        if not llm_response or llm_metadata.get("error"):
            error_details = llm_metadata.get("error", "Unknown workflow error")
            fallback_message = (
                "I apologize, but I'm currently unable to process your request. "
                "Please try again later or contact support if the issue persists."
            )
            
            logger.warning(f"[DEV] EndNode - Workflow failed, using fallback. Error: {error_details}")
            
            # Ensure client gets a response
            state["llm_response"] = fallback_message
            state["final_response"] = fallback_message
            state["final_llm_response"] = fallback_message  # This is what the API expects
            state["workflow_status"] = "failed"
            state["error_details"] = error_details
        else:
            # Workflow succeeded
            state["final_response"] = llm_response
            state["final_llm_response"] = llm_response  # This is what the API expects
            state["workflow_status"] = "success"
            logger.info(f"[DEV] EndNode - Workflow succeeded with response length: {len(llm_response)} chars")
        
        return state
