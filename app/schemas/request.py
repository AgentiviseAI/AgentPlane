from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProcessPromptRequest(BaseModel):
    agentid: str
    prompt: str
    chatid: str = ""
    userid: str


class ProcessPromptResponse(BaseModel):
    agentid: str
    response: str
    chatid: str
    userid: str
