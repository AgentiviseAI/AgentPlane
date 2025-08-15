"""
LLM Prompt Node - Handles dynamic LLM calls based on hosting environment using LLMService
"""
from typing import Dict, Any
from app.workflow.base import WorkflowNode
from app.core.logging import logger

# LangChain imports
from langchain_core.messages import HumanMessage


class LLMPromptNode(WorkflowNode):
    """Node that calls an LLM based on node configuration"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None, llm_service=None):
        super().__init__(node_id, config)
        self.llm_service = llm_service
        self.llm_entity = None
        self.llm_initialized = False
        logger.info(f"[DEV] LLMPromptNode initialized - ID: {node_id}")
    
    async def _fetch_llm_entity(self):
        """Fetch LLM entity from ControlTower using injected LLMService"""        
        if self.llm_initialized:
            return
            
        if not self.llm_service:
            raise ValueError("LLMService not provided. Make sure to inject LLMService in constructor.")
            
        # Get LLM ID from config (now includes root-level fields like 'link')
        llm_id = self.config.get("link") or self.config.get("llm_id")
        logger.info(f"[DEV] LLMPromptNode - Extracted LLM ID: {llm_id}")
        
        if not llm_id:
            logger.error(f"[DEV] LLMPromptNode - No LLM ID found. Config: {self.config}")
            raise ValueError("LLM ID not found in node configuration. Expected 'link' or 'llm_id' field.")
        
        # Get LLM through injected service
        try:
            self.llm_entity = await self.llm_service.get_by_id(llm_id)
        except Exception as e:
            logger.error(f"[DEV] LLMPromptNode - Failed to fetch LLM: {e}")
            raise ValueError(f"Failed to fetch LLM: {e}")
            
        if not self.llm_entity:
            raise ValueError(f"LLM with ID {llm_id} not found")
            
        if not self.llm_entity.enabled:
            raise ValueError(f"LLM {self.llm_entity.name} is disabled")
            
        logger.info(f"[DEV] LLMPromptNode - Fetched LLM: {self.llm_entity.name} ({self.llm_entity.hosting_environment})")
        self.llm_initialized = True

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the LLM call using the LLMService for unified LLM handling."""
        logger.info(f"[DEV] LLMPromptNode.process() - Starting for node: {self.node_id}")
        
        prompt = state.get("processed_prompt", state.get("prompt", ""))
        if not prompt:
            error_msg = "No prompt found in state"
            logger.error(f"[DEV] LLMPromptNode - {error_msg}")
            state["llm_response"] = error_msg
            return state
        
        try:
            # Fetch LLM entity if not already done
            await self._fetch_llm_entity()
            
            # Use the LLMService invoke method for unified LLM handling
            logger.info(f"[DEV] LLMPromptNode - Using LLMService.invoke() for unified LLM processing")
            logger.info(f"[DEV] LLMPromptNode - LLM: {self.llm_entity.name} ({self.llm_entity.hosting_environment})")
            logger.info(f"[DEV] LLMPromptNode - Prompt length: {len(prompt)} characters")
            
            response_text = await self.llm_service.invoke(self.llm_entity, prompt)
            
            logger.info(f"[DEV] LLMPromptNode - LLM call completed successfully")
            logger.info(f"[DEV] LLMPromptNode - Response length: {len(response_text)} chars")
            
            # Store the response
            state["llm_response"] = response_text
            state["llm_metadata"] = {
                "llm_id": self.llm_entity.id,
                "llm_name": self.llm_entity.name,
                "model": self.llm_entity.model_name,
                "hosting_environment": self.llm_entity.hosting_environment,
                "config": self.llm_entity.additional_config or {},
                "integration": "llm_service_unified"
            }
            
            # Set success flag
            state["success"] = True
            
        except Exception as e:
            logger.error(f"[DEV] LLMPromptNode - Error: {str(e)}")
            
            # Return error state with failure flag
            error_response = f"I apologize, but I'm currently unable to process your request. Error: {str(e)}"
            state["llm_response"] = error_response
            state["llm_metadata"] = {
                "error": str(e),
                "llm_id": getattr(self.llm_entity, 'id', 'unknown'),
                "hosting_environment": getattr(self.llm_entity, 'hosting_environment', 'unknown'),
                "integration": "llm_service_unified"
            }
            
            # Critical: Set success flag to False so workflow processor knows this node failed
            state["success"] = False
        
        return state
