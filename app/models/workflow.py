from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base
import uuid


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    nodes = Column(JSON)
    edges = Column(JSON)
    status = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    agents = relationship("AIAgent", back_populates="workflow")
    conversations = relationship("Conversation", back_populates="workflow")
