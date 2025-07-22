from app.pipeline.base import PipelineNode
from typing import Dict, Any
import google.generativeai as genai
import os


class InputProcessorNode(PipelineNode):
    """Node that processes and validates input"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process input prompt and add metadata"""
        prompt = state.get("prompt", "")
        
        # Basic input validation and processing
        if not prompt.strip():
            raise ValueError("Empty prompt provided")
        
        # Add processed prompt to state
        state["processed_prompt"] = prompt.strip()
        state["input_metadata"] = {
            "character_count": len(prompt),
            "word_count": len(prompt.split()),
            "processing_timestamp": str(state.get("created_at", ""))
        }
        
        return state


class LLMCallNode(PipelineNode):
    """Node that calls the Gemini LLM"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        
        # Configure Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.model_name = self.config.get("model", "gemini-1.5-flash")
        self.temperature = self.config.get("temperature", 0.7)
        self.max_tokens = self.config.get("max_tokens", 1000)
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Call Gemini LLM and store response"""
        prompt = state.get("processed_prompt", state.get("prompt", ""))
        
        try:
            # Initialize the model
            model = genai.GenerativeModel(self.model_name)
            
            # Generate content
            response = await model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                )
            )
            
            # Store the response
            state["llm_response"] = response.text
            state["llm_metadata"] = {
                "model": self.model_name,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "usage": getattr(response, "usage_metadata", {})
            }
            
        except Exception as e:
            # Fallback response in case of LLM failure
            state["llm_response"] = f"I apologize, but I'm currently unable to process your request. Error: {str(e)}"
            state["llm_metadata"] = {
                "error": str(e),
                "model": self.model_name
            }
        
        return state


class ResponseFormatterNode(PipelineNode):
    """Node that formats the final response"""
    
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format the LLM response for final output"""
        llm_response = state.get("llm_response", "")
        
        # Basic formatting and cleanup
        formatted_response = llm_response.strip()
        
        # Store final response
        state["final_llm_response"] = formatted_response
        state["response_metadata"] = {
            "formatted_at": str(state.get("created_at", "")),
            "response_length": len(formatted_response)
        }
        
        return state
