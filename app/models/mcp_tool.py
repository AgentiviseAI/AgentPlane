"""
MCP Tool model for agent-api-server
"""
from sqlalchemy import Column, String, Boolean, Text, JSON, DateTime
from sqlalchemy.sql import func
from app.models.base import Base
import uuid


class MCPTool(Base):
    __tablename__ = "mcp_tools"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    endpoint_url = Column(String(500), nullable=False)
    transport = Column(String(100), default="Streamable HTTP")
    required_permissions = Column(JSON)
    auth_headers = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
