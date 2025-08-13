from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class RoleType(str, Enum):
    SYSTEM = "system"
    ORGANIZATION = "organization"


class SecurityRoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    permissions: List[str] = []
    type: Optional[RoleType] = RoleType.ORGANIZATION
    organization_id: Optional[UUID] = None  # Nullable for system roles
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
