"""
SWITCH Node - Evaluates a field against multiple cases and routes accordingly
"""
from typing import Dict, Any, List, Tuple
from app.workflow.base import WorkflowNode
from app.core.logging import logger
import re
import json


class SwitchNode(WorkflowNode):
    """Node that evaluates a field against multiple cases and routes execution accordingly"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        self.switch_field = config.get("switch_field", "")
        self.switch_cases = config.get("switch_cases", [])
        self.default_case = config.get("default_case", "default")
        logger.info(f"[DEV] SwitchNode initialized - ID: {node_id}")
        logger.info(f"[DEV] SwitchNode - Field: {self.switch_field}, Cases: {len(self.switch_cases)}, Default: {self.default_case}")
    
    def _evaluate_switch(self, state: Dict[str, Any]) -> Tuple[str, str]:
        """Evaluate the switch field against all cases"""
        try:
            # Get the field value from state
            field_value = state.get(self.switch_field)
            
            if field_value is None:
                logger.warning(f"[DEV] SwitchNode - Field '{self.switch_field}' not found in state")
                return self.default_case, f"Field '{self.switch_field}' not found, using default case"
            
            field_str = str(field_value).strip()
            logger.info(f"[DEV] SwitchNode - Evaluating field value: '{field_str}' against {len(self.switch_cases)} cases")
            
            # Evaluate each case
            for i, case in enumerate(self.switch_cases):
                case_value = str(case.get("value", "")).strip()
                case_operator = case.get("operator", "equals")
                case_output = case.get("output", f"case_{i}")
                
                logger.info(f"[DEV] SwitchNode - Testing case {i}: '{field_str}' {case_operator} '{case_value}' -> '{case_output}'")
                
                # Evaluate based on operator
                match = False
                if case_operator == "equals":
                    match = field_str.lower() == case_value.lower()
                elif case_operator == "not_equals":
                    match = field_str.lower() != case_value.lower()
                elif case_operator == "contains":
                    match = case_value.lower() in field_str.lower()
                elif case_operator == "not_contains":
                    match = case_value.lower() not in field_str.lower()
                elif case_operator == "starts_with":
                    match = field_str.lower().startswith(case_value.lower())
                elif case_operator == "ends_with":
                    match = field_str.lower().endswith(case_value.lower())
                elif case_operator == "regex":
                    try:
                        pattern = re.compile(case_value, re.IGNORECASE)
                        match = bool(pattern.search(field_str))
                    except re.error as e:
                        logger.error(f"[DEV] SwitchNode - Invalid regex pattern in case {i}: {e}")
                        continue
                elif case_operator == "greater_than":
                    try:
                        match = float(field_str) > float(case_value)
                    except ValueError:
                        logger.warning(f"[DEV] SwitchNode - Cannot compare non-numeric values in case {i}")
                        continue
                elif case_operator == "less_than":
                    try:
                        match = float(field_str) < float(case_value)
                    except ValueError:
                        logger.warning(f"[DEV] SwitchNode - Cannot compare non-numeric values in case {i}")
                        continue
                elif case_operator == "greater_equal":
                    try:
                        match = float(field_str) >= float(case_value)
                    except ValueError:
                        logger.warning(f"[DEV] SwitchNode - Cannot compare non-numeric values in case {i}")
                        continue
                elif case_operator == "less_equal":
                    try:
                        match = float(field_str) <= float(case_value)
                    except ValueError:
                        logger.warning(f"[DEV] SwitchNode - Cannot compare non-numeric values in case {i}")
                        continue
                elif case_operator == "is_empty":
                    match = not field_str or field_str == ""
                elif case_operator == "is_not_empty":
                    match = bool(field_str and field_str != "")
                else:
                    logger.warning(f"[DEV] SwitchNode - Unknown operator '{case_operator}' in case {i}")
                    continue
                
                if match:
                    logger.info(f"[DEV] SwitchNode - Case {i} matched! Using output: '{case_output}'")
                    return case_output, f"Matched case {i}: '{field_str}' {case_operator} '{case_value}'"
            
            # No cases matched, use default
            logger.info(f"[DEV] SwitchNode - No cases matched, using default output: '{self.default_case}'")
            return self.default_case, f"No cases matched for value '{field_str}', using default case"
            
        except Exception as e:
            logger.error(f"[DEV] SwitchNode - Error evaluating switch: {e}")
            return self.default_case, f"Error evaluating switch: {e}"
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the SWITCH logic and determine the next execution path"""
        logger.info(f"[DEV] SwitchNode.process() - Starting switch evaluation for node: {self.node_id}")
        
        try:
            # Validate configuration
            if not self.switch_field:
                error_msg = "No switch field specified in SWITCH node configuration"
                logger.error(f"[DEV] SwitchNode - {error_msg}")
                state["switch_result"] = "error"
                state["switch_reason"] = error_msg
                state["success"] = False
                state["error"] = error_msg
                state["next_output_handle"] = self.default_case
                return state
            
            if not self.switch_cases or len(self.switch_cases) == 0:
                error_msg = "No switch cases defined in SWITCH node configuration"
                logger.error(f"[DEV] SwitchNode - {error_msg}")
                state["switch_result"] = "error"
                state["switch_reason"] = error_msg
                state["success"] = False
                state["error"] = error_msg
                state["next_output_handle"] = self.default_case
                return state
            
            # Evaluate the switch
            output_handle, evaluation_message = self._evaluate_switch(state)
            
            # Update state with SWITCH results
            state["switch_result"] = output_handle
            state["switch_reason"] = evaluation_message
            state["switch_field"] = self.switch_field
            state["switch_cases_count"] = len(self.switch_cases)
            state["switch_metadata"] = {
                "node_id": self.node_id,
                "field_value": state.get(self.switch_field),
                "cases": self.switch_cases,
                "default_case": self.default_case,
                "result": output_handle,
                "evaluation_message": evaluation_message
            }
            
            # Set the next output handle for the workflow processor
            state["next_output_handle"] = output_handle
            
            # Set success flag
            state["success"] = True
            
            logger.info(f"[DEV] SwitchNode - Switch evaluation completed")
            logger.info(f"[DEV] SwitchNode - Result: {output_handle}")
            
        except Exception as e:
            logger.error(f"[DEV] SwitchNode - Error: {str(e)}")
            
            # Return error state
            error_message = f"SWITCH node failed: {str(e)}"
            state["switch_result"] = "error"
            state["switch_reason"] = error_message
            state["switch_metadata"] = {
                "node_id": self.node_id,
                "error": str(e)
            }
            state["next_output_handle"] = self.default_case
            state["success"] = False
            state["error"] = str(e)
        
        return state
