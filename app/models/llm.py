"""
LLM Model for agent-api-server
"""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Float, Integer
from app.models.base import Base
import uuid
from datetime import datetime


class LLM(Base):
    __tablename__ = "llms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Hosting Environment
    hosting_environment = Column(String(100), nullable=False)  # azure_ai_foundry, aws_bedrock, aws_sagemaker, gcp_vertex_ai, custom_deployment
    
    # Azure AI Foundry fields
    azure_endpoint_url = Column(String(500))
    azure_api_key = Column(Text)  # Encrypted
    azure_deployment_name = Column(String(255))
    
    # AWS fields (Bedrock & SageMaker)
    aws_region = Column(String(50))
    aws_access_key_id = Column(Text)  # Encrypted
    aws_secret_access_key = Column(Text)  # Encrypted
    aws_model_id = Column(String(255))  # For Bedrock
    aws_sagemaker_endpoint_name = Column(String(255))  # For SageMaker
    aws_content_handler_class = Column(String(255))  # For SageMaker
    
    # Google Cloud Vertex AI fields
    gcp_project_id = Column(String(255))
    gcp_region = Column(String(50))
    gcp_auth_method = Column(String(50))  # adc, service_account_key
    gcp_service_account_key = Column(Text)  # Encrypted JSON
    gcp_model_type = Column(String(50))  # foundation, custom_endpoint
    gcp_model_name = Column(String(255))  # For foundation models
    gcp_endpoint_id = Column(String(255))  # For custom endpoints
    gcp_model_id = Column(String(255))  # For custom endpoints
    
    # Custom Deployment fields
    custom_deployment_location = Column(String(100))  # on_premise, azure_compute, aws_compute, gcp_compute, other_cloud
    custom_llm_provider = Column(String(255))
    custom_api_endpoint_url = Column(String(500))
    custom_api_compatibility = Column(String(50))  # openai_compatible, huggingface_tgi, ollama, custom
    custom_auth_method = Column(String(50))  # none, api_key_header, bearer_token, other
    custom_auth_header_name = Column(String(100))
    custom_auth_key_prefix = Column(String(50))
    custom_auth_api_key = Column(Text)  # Encrypted
    
    # General LLM Configuration
    model_name = Column(String(255))  # Internal tracking name
    temperature = Column(Float)
    max_tokens = Column(Integer)
    top_p = Column(Float)
    stop_sequences = Column(Text)  # Comma-separated
    
    # System fields
    enabled = Column(Boolean, default=True)
    status = Column(String(50), default="active")
    usage_stats = Column(JSON)
    additional_config = Column(JSON)  # For any extra configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
