from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ExecuteRequest(BaseModel):
    prompt: str
    runid: str = ""
    includeHistory: bool = False


class ExecuteResponse(BaseModel):
    response: str
    runid: str


