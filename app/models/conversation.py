from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    userid = Column(String(255), nullable=False)
    chatid = Column(String(36), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    workflow_state = Column(JSON, nullable=False)
    agent_id = Column(String(36), ForeignKey("ai_agents.id"), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    agent = relationship("AIAgent", back_populates="conversations")
    workflow = relationship("Workflow", back_populates="conversations")
