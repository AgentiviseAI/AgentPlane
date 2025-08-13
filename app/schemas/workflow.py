from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
