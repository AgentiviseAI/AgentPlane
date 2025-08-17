"""
IF-ELSE Node - Evaluates a condition and routes to success or failure path
"""
from typing import Dict, Any, Tuple
from app.workflow.base import WorkflowNode
from app.core.logging import logger
import re
import json


class IfElseNode(WorkflowNode):
    """Node that evaluates a condition and routes execution to success or failure path"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        self.condition_field = config.get("condition_field", "")
        self.condition_operator = config.get("condition_operator", "equals")
        self.condition_value = config.get("condition_value", "")
        logger.info(f"[DEV] IfElseNode initialized - ID: {node_id}")
        logger.info(f"[DEV] IfElseNode - Field: {self.condition_field}, Operator: {self.condition_operator}, Value: {self.condition_value}")
    
    def _evaluate_condition(self, state: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate the condition against the workflow state"""
        try:
            # Get the field value from state
            field_value = state.get(self.condition_field)
            
            if field_value is None:
                logger.warning(f"[DEV] IfElseNode - Field '{self.condition_field}' not found in state")
                return False, f"Field '{self.condition_field}' not found in workflow state"
            
            logger.info(f"[DEV] IfElseNode - Evaluating: {field_value} {self.condition_operator} {self.condition_value}")
            
            # Convert values to strings for comparison
            field_str = str(field_value).strip()
            condition_str = str(self.condition_value).strip()
            
            # Evaluate based on operator
            if self.condition_operator == "equals":
                result = field_str.lower() == condition_str.lower()
            elif self.condition_operator == "not_equals":
                result = field_str.lower() != condition_str.lower()
            elif self.condition_operator == "contains":
                result = condition_str.lower() in field_str.lower()
            elif self.condition_operator == "not_contains":
                result = condition_str.lower() not in field_str.lower()
            elif self.condition_operator == "starts_with":
                result = field_str.lower().startswith(condition_str.lower())
            elif self.condition_operator == "ends_with":
                result = field_str.lower().endswith(condition_str.lower())
            elif self.condition_operator == "regex":
                try:
                    pattern = re.compile(condition_str, re.IGNORECASE)
                    result = bool(pattern.search(field_str))
                except re.error as e:
                    logger.error(f"[DEV] IfElseNode - Invalid regex pattern: {e}")
                    return False, f"Invalid regex pattern: {e}"
            elif self.condition_operator == "greater_than":
                try:
                    result = float(field_str) > float(condition_str)
                except ValueError:
                    return False, f"Cannot compare non-numeric values with greater_than operator"
            elif self.condition_operator == "less_than":
                try:
                    result = float(field_str) < float(condition_str)
                except ValueError:
                    return False, f"Cannot compare non-numeric values with less_than operator"
            elif self.condition_operator == "greater_equal":
                try:
                    result = float(field_str) >= float(condition_str)
                except ValueError:
                    return False, f"Cannot compare non-numeric values with greater_equal operator"
            elif self.condition_operator == "less_equal":
                try:
                    result = float(field_str) <= float(condition_str)
                except ValueError:
                    return False, f"Cannot compare non-numeric values with less_equal operator"
            elif self.condition_operator == "is_empty":
                result = not field_str or field_str == ""
            elif self.condition_operator == "is_not_empty":
                result = bool(field_str and field_str != "")
            else:
                logger.error(f"[DEV] IfElseNode - Unknown operator: {self.condition_operator}")
                return False, f"Unknown operator: {self.condition_operator}"
            
            logger.info(f"[DEV] IfElseNode - Condition result: {result}")
            return result, f"Condition '{field_str} {self.condition_operator} {condition_str}' evaluated to {result}"
            
        except Exception as e:
            logger.error(f"[DEV] IfElseNode - Error evaluating condition: {e}")
            return False, f"Error evaluating condition: {e}"
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the IF-ELSE logic and determine the next execution path"""
        logger.info(f"[DEV] IfElseNode.process() - Starting condition evaluation for node: {self.node_id}")
        
        try:
            # Validate configuration
            if not self.condition_field:
                error_msg = "No condition field specified in IF-ELSE node configuration"
                logger.error(f"[DEV] IfElseNode - {error_msg}")
                state["if_else_result"] = "error"
                state["if_else_reason"] = error_msg
                state["success"] = False
                state["error"] = error_msg
                state["next_output_handle"] = "false"  # Default to false path on error
                return state
            
            # Evaluate the condition
            condition_result, evaluation_message = self._evaluate_condition(state)
            
            # Determine which output path to take
            output_handle = "true" if condition_result else "false"
            
            # Update state with IF-ELSE results
            state["if_else_result"] = "true" if condition_result else "false"
            state["if_else_reason"] = evaluation_message
            state["if_else_field"] = self.condition_field
            state["if_else_operator"] = self.condition_operator
            state["if_else_value"] = self.condition_value
            state["if_else_metadata"] = {
                "node_id": self.node_id,
                "field_value": state.get(self.condition_field),
                "expected_value": self.condition_value,
                "operator": self.condition_operator,
                "result": condition_result,
                "evaluation_message": evaluation_message
            }
            
            # Set the next output handle for the workflow processor
            # Use full handle format to match sourceHandle in edges
            full_output_handle = f"{self.node_id}-{output_handle}"
            state["next_output_handle"] = full_output_handle
            
            # Set success flag
            state["success"] = True
            
            logger.info(f"[DEV] IfElseNode - Condition evaluation completed")
            logger.info(f"[DEV] IfElseNode - Result: {condition_result}, Next path: {output_handle}")
            
        except Exception as e:
            logger.error(f"[DEV] IfElseNode - Error: {str(e)}")
            
            # Return error state
            error_message = f"IF-ELSE node failed: {str(e)}"
            state["if_else_result"] = "error"
            state["if_else_reason"] = error_message
            state["if_else_metadata"] = {
                "node_id": self.node_id,
                "error": str(e)
            }
            state["next_output_handle"] = "false"  # Default to false path on error
            state["success"] = False
            state["error"] = str(e)
        
        return state
