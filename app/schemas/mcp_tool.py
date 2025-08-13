from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class MCPToolResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    command: str
    parameters: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
