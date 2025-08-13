from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSON
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
    # Store as strings without foreign key constraints since these reference ControlTower data
    agent_id = Column(String(36), nullable=False, index=True)
    workflow_id = Column(String(36), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now())
