from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime


class ConversationCreate(BaseModel):
    userid: str
    chatid: str
    prompt: str
    workflow_state: Dict[str, Any]
    agent_id: str
    workflow_id: str


class ConversationResponse(BaseModel):
    id: str
    userid: str
    chatid: str
    prompt: str
    workflow_state: Dict[str, Any]
    agent_id: str
    workflow_id: str
    created_at: datetime

    class Config:
        from_attributes = True
