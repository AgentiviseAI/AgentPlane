"""
LLM Service - Handles LLM entity operations via ControlTower
"""
from typing import Optional, List, Dict, Any
import asyncio
import logging
from langchain_core.messages import HumanMessage, SystemMessage
from app.middleware.controltower_client import ControlTowerClient
from app.schemas.llm import LLMResponse

logger = logging.getLogger(__name__)


class LLMService:
    """Service for managing LLM entities via ControlTower"""
    
    def __init__(self, controltower_client: ControlTowerClient):
        self.controltower_client = controltower_client
    
    async def get_by_id(self, llm_id: str) -> Optional[LLMResponse]:
        """Get LLM by ID from ControlTower"""
        return await self.controltower_client.get_llm(llm_id)
    
    async def list_llms(self) -> List[LLMResponse]:
        """List available LLMs from ControlTower"""
        # This would be implemented when ControlTower exposes a list LLMs endpoint
        # For now, return empty list
        return []
    
    async def invoke(self, llm_entity: LLMResponse, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Invoke LLM with a prompt and return the response
        
        Args:
            llm_entity: The LLM configuration
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt to set context/instructions
            **kwargs: Additional parameters like format, temperature, etc.
        """
        try:
            logger.info(f"[DEV] LLMService - Invoking LLM {llm_entity.name} with prompt length: {len(prompt)}")
            if system_prompt:
                logger.info(f"[DEV] LLMService - System prompt length: {len(system_prompt)}")
            if kwargs:
                logger.info(f"[DEV] LLMService - Additional parameters: {kwargs}")
            
            # Create LangChain LLM instance based on hosting environment
            llm = await self._create_llm_instance(llm_entity, **kwargs)
            if not llm:
                raise ValueError(f"Failed to create LLM instance for {llm_entity.hosting_environment}")
            
            # Create messages using LangChain format
            messages = []
            if system_prompt:
                messages.append(SystemMessage(content=system_prompt))
            messages.append(HumanMessage(content=prompt))
            
            # Call the LLM using LangChain
            response = await llm.ainvoke(messages)
            
            # Extract content from LangChain response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            logger.info(f"[DEV] LLMService - LLM call completed successfully, response length: {len(response_text)}")
            return response_text
            
        except Exception as e:
            logger.error(f"[DEV] LLMService - Error invoking LLM: {str(e)}")
            raise e
    
    async def _create_llm_instance(self, llm_entity: LLMResponse, **kwargs):
        """Create LangChain LLM instance based on hosting environment
        
        Args:
            llm_entity: The LLM configuration
            **kwargs: Additional parameters like format, temperature, etc.
        """
        hosting_env = llm_entity.hosting_environment
        
        try:
            if hosting_env == "custom_deployment":
                api_compatibility = getattr(llm_entity, 'custom_api_compatibility', None)
                if api_compatibility == "ollama_compatible":
                    return await self._create_ollama_llm(llm_entity, **kwargs)
                elif api_compatibility == "hf_tgi_compatible":
                    return await self._create_huggingface_tgi_llm(llm_entity, **kwargs)
                elif api_compatibility == "openai_compatible":
                    return await self._create_openai_compatible_llm(llm_entity, **kwargs)
                else:
                    # Default to Ollama-compatible for backward compatibility
                    return await self._create_ollama_llm(llm_entity, **kwargs)
            elif hosting_env == "azure_ai_foundry":
                return await self._create_azure_ai_foundry_llm(llm_entity, **kwargs)
            elif hosting_env == "aws_bedrock":
                return await self._create_bedrock_llm(llm_entity, **kwargs)
            elif hosting_env == "aws_sagemaker":
                return await self._create_huggingface_tgi_llm(llm_entity, **kwargs)
            else:
                raise ValueError(f"Unsupported hosting environment: {hosting_env}")
                
        except Exception as e:
            logger.error(f"[DEV] LLMService - Error creating LLM instance: {str(e)}")
            raise e
    
    async def _create_ollama_llm(self, llm_entity: LLMResponse, **kwargs):
        """Create Ollama-compatible LLM instance
        
        Args:
            llm_entity: The LLM configuration
            **kwargs: Additional parameters like format, temperature, etc.
        """
        from langchain_ollama import OllamaLLM
        
        # Extract Ollama-specific parameters
        ollama_params = {
            'model': llm_entity.model_name,
            'base_url': llm_entity.custom_api_endpoint_url,
            'temperature': kwargs.get('temperature', getattr(llm_entity, 'temperature', 0.7))
        }
        
        # Add format parameter if specified (for JSON output)
        if 'format' in kwargs:
            ollama_params['format'] = kwargs['format']
            
        return OllamaLLM(**ollama_params)
    
    async def _create_openai_compatible_llm(self, llm_entity: LLMResponse, **kwargs):
        """Create OpenAI-compatible LLM instance"""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=llm_entity.model_name,
            base_url=llm_entity.custom_api_endpoint_url,
            api_key=llm_entity.custom_auth_api_key or "dummy-key",
            temperature=kwargs.get('temperature', getattr(llm_entity, 'temperature', 0.7)),
            max_tokens=getattr(llm_entity, 'max_tokens', None)
        )
    
    async def _create_huggingface_tgi_llm(self, llm_entity: LLMResponse, **kwargs):
        """Create HuggingFace TGI-compatible LLM instance"""
        from langchain_community.llms import HuggingFaceTextGenInference
        
        return HuggingFaceTextGenInference(
            inference_server_url=llm_entity.custom_api_endpoint_url,
            temperature=kwargs.get('temperature', getattr(llm_entity, 'temperature', 0.7)),
            max_new_tokens=getattr(llm_entity, 'max_tokens', 512)
        )
    
    async def _create_azure_ai_foundry_llm(self, llm_entity: LLMResponse, **kwargs):
        """Create Azure AI Foundry LLM instance"""
        from langchain_openai import AzureChatOpenAI
        
        return AzureChatOpenAI(
            azure_endpoint=llm_entity.azure_endpoint_url,
            api_key=llm_entity.azure_api_key,
            azure_deployment=llm_entity.azure_deployment_name,
            api_version="2024-02-15-preview",
            temperature=kwargs.get('temperature', getattr(llm_entity, 'temperature', 0.7)),
            max_tokens=getattr(llm_entity, 'max_tokens', None)
        )
    
    async def _create_bedrock_llm(self, llm_entity: LLMResponse, **kwargs):
        """Create AWS Bedrock LLM instance"""
        from langchain_aws import ChatBedrock
        
        return ChatBedrock(
            model_id=llm_entity.aws_model_id,
            region_name=llm_entity.aws_region,
            credentials_profile_name=None,
            model_kwargs={
                "temperature": kwargs.get('temperature', getattr(llm_entity, 'temperature', 0.7)),
                "max_tokens": getattr(llm_entity, 'max_tokens', None)
            }
        )
