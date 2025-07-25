"""
LLM Call Node - Handles dynamic LLM calls based on hosting environment using LangChain
"""
from typing import Dict, Any
import os
from app.workflow.base import WorkflowNode
from app.core.logging import logger

# LangChain imports
from langchain_aws import ChatBedrock
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.messages import HumanMessage


class LLMCallNode(WorkflowNode):
    """Node that calls an LLM based on node configuration"""
    
    def __init__(self, node_id: str, config: Dict[str, Any] = None):
        super().__init__(node_id, config)
        self.llm_entity = None
        self.llm_initialized = False
        logger.info(f"[DEV] LLMCallNode initialized - ID: {node_id}")
    
    async def _fetch_llm_entity(self):
        """Fetch LLM entity from database using LLMService"""        
        if self.llm_initialized:
            return
            
        # Get LLM ID from config (now includes root-level fields like 'link')
        llm_id = self.config.get("link") or self.config.get("llm_id")
        logger.info(f"[DEV] LLMCallNode - Extracted LLM ID: {llm_id}")
        
        if not llm_id:
            logger.error(f"[DEV] LLMCallNode - No LLM ID found. Config: {self.config}")
            raise ValueError("LLM ID not found in node configuration. Expected 'link' or 'llm_id' field.")
        
        # Get LLM through service layer using late import to avoid circular dependencies
        try:
            import app.core.di_container as di_module
            container = di_module.get_container()
            llm_service = container.llm_service
            self.llm_entity = await llm_service.get_by_id(llm_id)
        except RuntimeError as e:
            logger.error(f"[DEV] LLMCallNode - DI Container not initialized: {e}")
            raise ValueError("Service container not available. Make sure the application is properly initialized.")
        except ImportError as e:
            logger.error(f"[DEV] LLMCallNode - Failed to import DI Container: {e}")
            raise ValueError("Service container unavailable due to import issues.")
            
        if not self.llm_entity:
            raise ValueError(f"LLM with ID {llm_id} not found")
            
        if not self.llm_entity.enabled:
            raise ValueError(f"LLM {self.llm_entity.name} is disabled")
            
        logger.info(f"[DEV] LLMCallNode - Fetched LLM: {self.llm_entity.name} ({self.llm_entity.hosting_environment})")
        self.llm_initialized = True
    
    async def _create_vertex_ai_llm(self):
        """Initialize Google Cloud Vertex AI LLM using LangChain"""
        if not self.llm_entity.gcp_project_id:
            raise ValueError("GCP project ID not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        # Set up authentication
        if self.llm_entity.gcp_auth_method == "service_account_key" and self.llm_entity.gcp_service_account_key:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS_JSON"] = self.llm_entity.gcp_service_account_key
        
        llm = ChatVertexAI(
            project=self.llm_entity.gcp_project_id,
            location=self.llm_entity.gcp_region or "us-central1",
            model=self.llm_entity.gcp_model_name or self.llm_entity.model_name,
            temperature=config.get("temperature", self.llm_entity.temperature or 0.7),
            max_tokens=config.get("max_tokens", self.llm_entity.max_tokens or 1000),
        )
        return llm
    
    async def _create_ollama_llm(self):
        """Initialize Ollama LLM using LangChain"""
        if not self.llm_entity.custom_api_endpoint_url:
            raise ValueError("Custom API endpoint URL not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        # Import the new ChatOllama from langchain-ollama
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            # Fallback to community version if langchain-ollama is not available
            from langchain_community.chat_models import ChatOllama
        
        # Extract base URL from the endpoint URL
        # If the URL ends with /api/generate, remove it to get the base URL
        base_url = self.llm_entity.custom_api_endpoint_url
        if base_url.endswith('/api/generate'):
            base_url = base_url[:-len('/api/generate')]
            logger.info(f"[DEV] LLMCallNode - Converted Ollama URL from {self.llm_entity.custom_api_endpoint_url} to {base_url}")
        elif base_url.endswith('/api/chat'):
            base_url = base_url[:-len('/api/chat')]
            logger.info(f"[DEV] LLMCallNode - Converted Ollama URL from {self.llm_entity.custom_api_endpoint_url} to {base_url}")
        
        # Ensure model name matches what's available in Ollama
        model_name = self.llm_entity.model_name
        # Handle common model name variations
        if model_name == "gemma-2-2b-instruct":
            model_name = "gemma2:2b"
            logger.info(f"[DEV] LLMCallNode - Converted model name from {self.llm_entity.model_name} to {model_name}")
        
        llm = ChatOllama(
            base_url=base_url,
            model=model_name,
            temperature=config.get("temperature", self.llm_entity.temperature or 0.7),
            num_predict=config.get("max_tokens", self.llm_entity.max_tokens or 1000),
        )
        return llm
    
    async def _create_openai_compatible_llm(self):
        """Initialize OpenAI-compatible LLM using LangChain"""
        if not self.llm_entity.custom_api_endpoint_url:
            raise ValueError("Custom API endpoint URL not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        # Get API key from custom auth configuration
        api_key = self.llm_entity.custom_auth_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key not configured for OpenAI-compatible LLM")
        
        llm = ChatOpenAI(
            base_url=self.llm_entity.custom_api_endpoint_url,
            api_key=api_key,
            model=self.llm_entity.model_name,
            temperature=config.get("temperature", self.llm_entity.temperature or 0.7),
            max_tokens=config.get("max_tokens", self.llm_entity.max_tokens or 1000),
        )
        return llm
    
    async def _create_azure_ai_foundry_llm(self):
        """Initialize Azure AI Foundry LLM using Azure OpenAI integration"""
        if not self.llm_entity.azure_endpoint_url:
            raise ValueError("Azure endpoint URL not configured for this LLM")
        
        if not self.llm_entity.azure_api_key:
            raise ValueError("Azure API key not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        # For Azure AI Foundry, we can use AzureChatOpenAI from langchain-openai
        from langchain_openai import AzureChatOpenAI
        
        llm = AzureChatOpenAI(
            azure_endpoint=self.llm_entity.azure_endpoint_url,
            api_key=self.llm_entity.azure_api_key,
            azure_deployment=self.llm_entity.azure_deployment_name or self.llm_entity.model_name,
            api_version="2024-02-01",  # Use latest API version
            temperature=config.get("temperature", self.llm_entity.temperature or 0.7),
            max_tokens=config.get("max_tokens", self.llm_entity.max_tokens or 1000),
        )
        return llm
    
    async def _create_bedrock_llm(self):
        """Initialize AWS Bedrock LLM using LangChain"""
        if not self.llm_entity.aws_region:
            raise ValueError("AWS region not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        # Set up AWS credentials if provided
        credentials = {}
        if self.llm_entity.aws_access_key_id:
            credentials["aws_access_key_id"] = self.llm_entity.aws_access_key_id
        if self.llm_entity.aws_secret_access_key:
            credentials["aws_secret_access_key"] = self.llm_entity.aws_secret_access_key
        
        llm = ChatBedrock(
            model_id=self.llm_entity.aws_model_id or self.llm_entity.model_name,
            region_name=self.llm_entity.aws_region,
            model_kwargs={
                "temperature": config.get("temperature", self.llm_entity.temperature or 0.7),
                "max_tokens": config.get("max_tokens", self.llm_entity.max_tokens or 1000),
            },
            **credentials
        )
        return llm
    
    async def _create_huggingface_tgi_llm(self):
        """Initialize Hugging Face TGI LLM using LangChain"""
        if not self.llm_entity.custom_api_endpoint_url:
            raise ValueError("Custom API endpoint URL not configured for this LLM")
        
        # Use additional_config or fallback to basic config
        config = self.llm_entity.additional_config or {}
        
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        
        # Use ChatHuggingFace for chat completions or HuggingFaceEndpoint for text generation
        llm = HuggingFaceEndpoint(
            endpoint_url=self.llm_entity.custom_api_endpoint_url,
            task="text-generation",
            model_kwargs={
                "temperature": config.get("temperature", self.llm_entity.temperature or 0.7),
                "max_new_tokens": config.get("max_tokens", self.llm_entity.max_tokens or 1000),
                "do_sample": True,
            }
        )
        return llm

    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process the LLM call using the configured LLM entity with LangChain integrations."""
        logger.info(f"[DEV] LLMCallNode.process() - Starting for node: {self.node_id}")
        
        prompt = state.get("processed_prompt", state.get("prompt", ""))
        if not prompt:
            error_msg = "No prompt found in state"
            logger.error(f"[DEV] LLMCallNode - {error_msg}")
            state["llm_response"] = error_msg
            return state
        
        try:
            # Fetch LLM entity if not already done
            await self._fetch_llm_entity()
            
            hosting_env = self.llm_entity.hosting_environment.lower()
            logger.info(f"[DEV] LLMCallNode - Using hosting environment: {hosting_env}")
            
            # Create LangChain LLM based on hosting environment
            llm = None
            if hosting_env in ["gcp_vertex_ai", "google_vertex_ai"]:
                logger.info(f"[DEV] LLMCallNode - Creating Vertex AI LLM with project: {getattr(self.llm_entity, 'gcp_project_id', 'N/A')}, model: {self.llm_entity.model_name}")
                llm = await self._create_vertex_ai_llm()
            elif hosting_env == "custom_deployment":
                # Route based on custom_api_compatibility field
                api_compatibility = getattr(self.llm_entity, 'custom_api_compatibility', '').lower()
                logger.info(f"[DEV] LLMCallNode - Custom deployment with API compatibility: {api_compatibility}")
                
                if api_compatibility == "ollama_compatible":
                    logger.info(f"[DEV] LLMCallNode - Creating Ollama LLM with endpoint: {self.llm_entity.custom_api_endpoint_url}, model: {self.llm_entity.model_name}")
                    llm = await self._create_ollama_llm()
                elif api_compatibility == "hf_tgi_compatible":
                    logger.info(f"[DEV] LLMCallNode - Creating HuggingFace TGI LLM with endpoint: {self.llm_entity.custom_api_endpoint_url}, model: {self.llm_entity.model_name}")
                    llm = await self._create_huggingface_tgi_llm()
                elif api_compatibility == "openai_compatible":
                    logger.info(f"[DEV] LLMCallNode - Creating OpenAI-compatible LLM with endpoint: {self.llm_entity.custom_api_endpoint_url}, model: {self.llm_entity.model_name}")
                    llm = await self._create_openai_compatible_llm()
                else:
                    # Default to Ollama-compatible for backward compatibility
                    logger.info(f"[DEV] LLMCallNode - Unknown API compatibility '{api_compatibility}', defaulting to Ollama-compatible LLM with endpoint: {self.llm_entity.custom_api_endpoint_url}, model: {self.llm_entity.model_name}")
                    llm = await self._create_ollama_llm()
            elif hosting_env == "azure_ai_foundry":
                logger.info(f"[DEV] LLMCallNode - Creating Azure AI Foundry LLM with endpoint: {getattr(self.llm_entity, 'azure_endpoint_url', 'N/A')}, deployment: {getattr(self.llm_entity, 'azure_deployment_name', self.llm_entity.model_name)}")
                llm = await self._create_azure_ai_foundry_llm()
            elif hosting_env == "aws_bedrock":
                logger.info(f"[DEV] LLMCallNode - Creating AWS Bedrock LLM with region: {getattr(self.llm_entity, 'aws_region', 'N/A')}, model: {getattr(self.llm_entity, 'aws_model_id', self.llm_entity.model_name)}")
                llm = await self._create_bedrock_llm()
            elif hosting_env == "aws_sagemaker":
                logger.info(f"[DEV] LLMCallNode - Creating HuggingFace TGI LLM with endpoint: {getattr(self.llm_entity, 'custom_api_endpoint_url', 'N/A')}, model: {self.llm_entity.model_name}")
                llm = await self._create_huggingface_tgi_llm()
            else:
                raise ValueError(f"Unsupported hosting environment: {hosting_env}")
            
            if not llm:
                raise ValueError(f"Failed to create LLM for hosting environment: {hosting_env}")
            
            logger.info(f"[DEV] LLMCallNode - Successfully created LLM instance for {hosting_env}")
            
            # Create messages using LangChain format
            messages = [HumanMessage(content=prompt)]
            
            # Call the LLM using LangChain
            logger.info(f"[DEV] LLMCallNode - Calling LLM with LangChain integration for {hosting_env}")
            logger.info(f"[DEV] LLMCallNode - Prompt length: {len(prompt)} characters")
            response = await llm.ainvoke(messages)
            
            # Extract content from LangChain response
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            logger.info(f"[DEV] LLMCallNode - LLM call completed successfully")
            logger.info(f"[DEV] LLMCallNode - Response length: {len(response_text)} chars")
            
            # Store the response
            state["llm_response"] = response_text
            state["llm_metadata"] = {
                "llm_id": self.llm_entity.id,
                "llm_name": self.llm_entity.name,
                "model": self.llm_entity.model_name,
                "hosting_environment": self.llm_entity.hosting_environment,
                "config": self.llm_entity.additional_config or {},
                "integration": "langchain"
            }
            
        except Exception as e:
            logger.error(f"[DEV] LLMCallNode - Error: {str(e)}")
            
            # Fallback response in case of LLM failure
            error_response = f"I apologize, but I'm currently unable to process your request. Error: {str(e)}"
            state["llm_response"] = error_response
            state["llm_metadata"] = {
                "error": str(e),
                "llm_id": getattr(self.llm_entity, 'id', 'unknown'),
                "hosting_environment": getattr(self.llm_entity, 'hosting_environment', 'unknown'),
                "integration": "langchain"
            }
        
        return state
