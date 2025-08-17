"""
Intent Extractor Node - Extracts user intent using IntentClassifier service
"""
from typing import Dict, Any, List
from app.workflow.base import WorkflowNode
from app.core.logging import logger


class IntentExtractorNode(WorkflowNode):
    """Node that extracts user intent using IntentClassifier service"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None, **kwargs):
        # Accept and ignore any additional keyword arguments for backward compatibility
        super().__init__(node_id, config)
        # Import locally to avoid circular imports
        from app.middleware.intentclassifier_client import IntentClassifierClient
        self.intentclassifier_client = IntentClassifierClient()
        logger.info(f"[DEV] IntentExtractorNode initialized - ID: {node_id}")
        
        # Log any ignored parameters for debugging
        if kwargs:
            ignored_params = list(kwargs.keys())
            logger.info(f"[DEV] IntentExtractorNode - Ignored legacy parameters: {ignored_params}")
    
    def _get_expected_intents(self) -> List[str]:
        """Extract expected intents from advanced configuration"""
        # Look for expected_intents in advanced configuration
        advanced_config = self.config.get("advanced_config", {})
        expected_intents = advanced_config.get("intents_expected", [])
        
        # If no expected intents specified, use default set
        if not expected_intents:
            default_intents = [
                "agent_creation",
                "information_request", 
                "support_request",
                "general_inquiry"
            ]
            logger.info(f"[DEV] IntentExtractorNode - No expected_intents in config, using defaults: {default_intents}")
            return default_intents
        
        logger.info(f"[DEV] IntentExtractorNode - Using configured expected_intents: {expected_intents}")
        return expected_intents
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process intent extraction using the IntentClassifier service"""
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
            # Get expected intents from configuration
            expected_intents = self._get_expected_intents()
            
            logger.info(f"[DEV] IntentExtractorNode - Classifying text: '{user_input}'")
            logger.info(f"[DEV] IntentExtractorNode - Against intents: {expected_intents}")
            
            # Call IntentClassifier service via client
            classification_result = await self.intentclassifier_client.classify_intent(user_input, expected_intents)
            
            # Process the structured response
            extracted_intent = classification_result["intent"]
            confidence = classification_result["confidence"]
            all_scores = classification_result.get("all_scores", [])
            all_labels = classification_result.get("all_labels", [])
            
            logger.info(f"[DEV] IntentExtractorNode - Intent extraction completed successfully")
            logger.info(f"[DEV] IntentExtractorNode - Result: {extracted_intent} (confidence: {confidence:.3f})")
            
            # Store the structured response in state
            state["intent_extraction_response"] = {
                "intent": extracted_intent,
                "confidence": confidence,
                "all_labels": all_labels,
                "all_scores": all_scores,
                "original_text": user_input
            }
            state["extracted_intent"] = extracted_intent
            state["intent_confidence"] = confidence
            state["original_user_input"] = user_input
            state["intent_extraction_metadata"] = {
                "service": "intent_classifier",
                "client": "intentclassifier_client",
                "expected_intents": expected_intents,
                "node_type": "intent_extractor",
                "classification_method": "zero_shot",
                "top_confidence": confidence,
                "all_confidences": dict(zip(all_labels, all_scores)) if all_labels and all_scores else {}
            }
            
            # Set success flag
            state["success"] = True
            
        except Exception as e:
            logger.error(f"[DEV] IntentExtractorNode - Error: {str(e)}")
            
            # Return error state with failure flag
            error_response = f"Failed to extract intent: {str(e)}"
            state["intent_extraction_response"] = error_response
            state["extracted_intent"] = "error"
            state["intent_confidence"] = 0.0
            state["intent_extraction_metadata"] = {
                "error": str(e),
                "service": "intent_classifier",
                "client": "intentclassifier_client",
                "node_type": "intent_extractor"
            }
            
            # Critical: Set success flag to False so workflow processor knows this node failed
            state["success"] = False
            state["error"] = str(e)
        
        return state
