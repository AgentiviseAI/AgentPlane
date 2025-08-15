"""
REST API Schema - Response models for REST API entities
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class RestAPIResponse(BaseModel):
    """Response model for REST API entity from ControlTower"""
    id: str = Field(..., description="Unique identifier for the REST API")
    name: str = Field(..., description="Name of the REST API")
    description: Optional[str] = Field(None, description="Description of the REST API")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE, etc.)")
    base_url: str = Field(..., description="Base URL for the API")
    resource_path: Optional[str] = Field(None, description="Resource path (endpoint path)")
    endpoint_url: Optional[str] = Field(None, description="Complete endpoint URL (computed)")
    enabled: bool = Field(True, description="Whether the API is enabled")
    status: str = Field("active", description="Status of the API")
    
    # Headers and authentication
    headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Default headers")
    auth_headers: Optional[Dict[str, str]] = Field(default_factory=dict, description="Authentication headers")
    
    # Parameters
    query_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Default query parameters")
    path_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Path parameters")
    
    # Metadata
    tags: Optional[List[str]] = Field(default_factory=list, description="Tags for categorization")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    @property
    def endpoint_url(self) -> str:
        """Get the complete endpoint URL"""
        base = self.base_url.rstrip('/') if self.base_url else ''
        resource = self.resource_path
        if resource:
            return f"{base}/{resource.lstrip('/')}"
        return base
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class RestAPIListResponse(BaseModel):
    """Response model for listing REST APIs"""
    items: List[RestAPIResponse] = Field(default_factory=list, description="List of REST APIs")
    total: int = Field(0, description="Total count of items")
    page: int = Field(1, description="Current page number")
    size: int = Field(10, description="Page size")
    
    class Config:
        from_attributes = True
