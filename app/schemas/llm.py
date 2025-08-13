from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class LLMResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    provider: str
    model_name: str
    enabled: bool = True
    hosting_environment: str
    
    # Configuration fields
    api_endpoint: Optional[str] = None
    parameters: Dict[str, Any] = {}
    additional_config: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    
    # GCP Vertex AI fields
    gcp_project_id: Optional[str] = None
    gcp_region: Optional[str] = None
    gcp_model_name: Optional[str] = None
    gcp_auth_method: Optional[str] = None
    gcp_service_account_key: Optional[str] = None
    
    # Custom deployment fields
    custom_api_endpoint_url: Optional[str] = None
    custom_api_compatibility: Optional[str] = None
    custom_auth_api_key: Optional[str] = None
    
    # Azure AI Foundry fields
    azure_endpoint_url: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_deployment_name: Optional[str] = None
    
    # AWS Bedrock fields
    aws_region: Optional[str] = None
    aws_model_id: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
