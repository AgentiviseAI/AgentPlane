from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class LLMResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    # Map custom_llm_provider to provider for backward compatibility
    provider: str = Field(alias='custom_llm_provider')
    model_name: str
    enabled: bool = True
    hosting_environment: str
    
    # Status and organization
    status: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Configuration fields
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[str] = None
    
    # Azure fields
    azure_endpoint_url: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    
    # AWS fields
    aws_region: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_model_id: Optional[str] = None
    aws_sagemaker_endpoint_name: Optional[str] = None
    aws_content_handler_class: Optional[str] = None
    
    # GCP fields
    gcp_project_id: Optional[str] = None
    gcp_region: Optional[str] = None
    gcp_auth_method: Optional[str] = None
    gcp_service_account_key: Optional[str] = None
    gcp_model_type: Optional[str] = None
    gcp_model_name: Optional[str] = None
    gcp_endpoint_id: Optional[str] = None
    gcp_model_id: Optional[str] = None
    
    # Custom deployment fields
    custom_deployment_location: Optional[str] = None
    custom_llm_provider: Optional[str] = None
    custom_api_endpoint_url: Optional[str] = None
    custom_api_compatibility: Optional[str] = None
    custom_auth_method: Optional[str] = None
    custom_auth_header_name: Optional[str] = None
    custom_auth_key_prefix: Optional[str] = None
    custom_auth_api_key: Optional[str] = None
    
    # Stats and additional config
    usage_stats: Optional[Dict[str, Any]] = {}
    additional_config: Optional[Dict[str, Any]] = {}
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True  # Allow both field name and alias
