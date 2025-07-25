from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AIAgentResponse(BaseModel):
    id: str
    name: str
    description: str
    workflow_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIAgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    workflow_id: str


class AIAgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    workflow_id: Optional[str] = None
