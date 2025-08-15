"""
Intent Extractor Node - Extracts user intent using LLM with system prompts
"""
from typing import Dict, Any
from app.workflow.base import WorkflowNode
from app.core.logging import logger


class IntentExtractorNode(WorkflowNode):
    """Node that extracts user intent using an LLM with customizable system prompts"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None, llm_service=None):
        super().__init__(node_id, config)
        self.llm_service = llm_service
        self.llm_entity = None
        self.llm_initialized = False
        logger.info(f"[DEV] IntentExtractorNode initialized - ID: {node_id}")
    
    async def _fetch_llm_entity(self):
        """Fetch LLM entity from ControlTower using injected LLMService"""        
        if self.llm_initialized:
            return
            
        if not self.llm_service:
            raise ValueError("LLMService not provided. Make sure to inject LLMService in constructor.")
            
        # Get LLM ID from config (using 'link' field)
        llm_id = self.get_link()
        logger.info(f"[DEV] IntentExtractorNode - Extracted LLM ID: {llm_id}")
        
        if not llm_id:
            logger.error(f"[DEV] IntentExtractorNode - No LLM ID found. Config: {self.config}")
            raise ValueError("LLM ID not found in node configuration. Expected 'link' field.")
        
        # Get LLM through injected service
        try:
            self.llm_entity = await self.llm_service.get_by_id(llm_id)
        except Exception as e:
            logger.error(f"[DEV] IntentExtractorNode - Failed to fetch LLM: {e}")
            raise ValueError(f"Failed to fetch LLM: {e}")
            
        if not self.llm_entity:
            raise ValueError(f"LLM with ID {llm_id} not found")
            
        if not self.llm_entity.enabled:
            raise ValueError(f"LLM {self.llm_entity.name} is disabled")
            
        logger.info(f"[DEV] IntentExtractorNode - Fetched LLM: {self.llm_entity.name} ({self.llm_entity.hosting_environment})")
        self.llm_initialized = True

    def _build_system_prompt(self) -> str:
        """Build the complete system prompt combining default and custom prompts"""
        
        # Default system prompt for intent extraction
        default_system_prompt = """You are a simple, highly-specialized intent extraction model. Your only function is to analyze user requests and extract the primary intent and its related entities in a structured JSON format. You will be given a list of supported intents.

Supported Intents:
- agent_creation: The user wants to create a new agent.

Example:
User Input: "create an agent named 'my special agent'"
JSON Output:
{
  "intent": "agent_creation",
  "entities": {
    "agent_name": "my special agent"
  }
}"""

        # Get additional system prompt from node configuration
        additional_system_prompt = self.config.get("system_prompt", "")
        
        if additional_system_prompt and additional_system_prompt.strip():
            # Combine default and additional system prompts
            combined_prompt = f"{default_system_prompt}\n\nAdditional Instructions:\n{additional_system_prompt.strip()}"
            logger.info(f"[DEV] IntentExtractorNode - Using combined system prompt (default + custom)")
        else:
            combined_prompt = default_system_prompt
            logger.info(f"[DEV] IntentExtractorNode - Using default system prompt")
        
        return combined_prompt

    def _build_full_prompt(self, user_input: str) -> str:
        """Build the complete prompt with system prompt + user input"""
        
        system_prompt = self._build_system_prompt()
        
        # Construct the full prompt
        full_prompt = f"{system_prompt}\n\nUser Input:\n{user_input}\n\nPlease extract the intent from the user input above:"
        
        return full_prompt

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent extraction using the LLMService"""
        logger.info(f"[DEV] IntentExtractorNode.process() - Starting intent extraction for node: {self.node_id}")
        
        # Get user input from state
        user_input = state.get("user_input") or state.get("prompt") or state.get("message", "")
        if not user_input:
            error_msg = "No user input found in state for intent extraction"
            logger.error(f"[DEV] IntentExtractorNode - {error_msg}")
            state["intent_extraction_response"] = error_msg
            state["success"] = False
            state["error"] = error_msg
            return state
        
        try:
            # Fetch LLM entity if not already done
            await self._fetch_llm_entity()
            
            # Build the complete prompt
            full_prompt = self._build_full_prompt(user_input)
            
            # Use the LLMService invoke method for unified LLM handling
            logger.info(f"[DEV] IntentExtractorNode - Using LLMService.invoke() for intent extraction")
            logger.info(f"[DEV] IntentExtractorNode - LLM: {self.llm_entity.name} ({self.llm_entity.hosting_environment})")
            logger.info(f"[DEV] IntentExtractorNode - User input length: {len(user_input)} characters")
            logger.info(f"[DEV] IntentExtractorNode - Full prompt to LLM:\n{full_prompt}")
            
            response_text = await self.llm_service.invoke(self.llm_entity, full_prompt)
            
            logger.info(f"[DEV] IntentExtractorNode - Intent extraction completed successfully")
            logger.info(f"[DEV] IntentExtractorNode - Response length: {len(response_text)} chars")
            
            # Store the response in state
            state["intent_extraction_response"] = response_text
            state["extracted_intent"] = response_text  # Alternative key for easier access
            state["original_user_input"] = user_input
            state["intent_extraction_metadata"] = {
                "llm_id": self.llm_entity.id,
                "llm_name": self.llm_entity.name,
                "model": self.llm_entity.model_name,
                "hosting_environment": self.llm_entity.hosting_environment,
                "config": self.llm_entity.additional_config or {},
                "integration": "llm_service_unified",
                "node_type": "intent_extractor",
                "has_custom_system_prompt": bool(self.config.get("system_prompt", "").strip())
            }
            
            # Set success flag
            state["success"] = True
            
        except Exception as e:
            logger.error(f"[DEV] IntentExtractorNode - Error: {str(e)}")
            
            # Return error state with failure flag
            error_response = f"Failed to extract intent: {str(e)}"
            state["intent_extraction_response"] = error_response
            state["extracted_intent"] = error_response
            state["intent_extraction_metadata"] = {
                "error": str(e),
                "llm_id": getattr(self.llm_entity, 'id', 'unknown'),
                "hosting_environment": getattr(self.llm_entity, 'hosting_environment', 'unknown'),
                "integration": "llm_service_unified",
                "node_type": "intent_extractor"
            }
            
            # Critical: Set success flag to False so workflow processor knows this node failed
            state["success"] = False
            state["error"] = str(e)
        
        return state
