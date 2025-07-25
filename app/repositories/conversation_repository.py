"""
Conversation Repository implementation
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional

from app.models.conversation import Conversation


class ConversationRepository:
    """Repository for Conversation operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        result = await self.db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: str, limit: Optional[int] = None, skip: int = 0) -> List[Conversation]:
        """Get conversations by user ID"""
        query = select(Conversation).where(Conversation.userid == user_id).order_by(desc(Conversation.created_at))
        
        if skip > 0:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_chat_id(self, chat_id: str) -> List[Conversation]:
        """Get conversations by chat ID"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.chatid == chat_id)
            .order_by(desc(Conversation.created_at))
        )
        return result.scalars().all()
    
    async def get_by_agent_id(self, agent_id: str) -> List[Conversation]:
        """Get conversations by agent ID"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.agent_id == agent_id)
            .order_by(desc(Conversation.created_at))
        )
        return result.scalars().all()
    
    async def get_by_workflow_id(self, workflow_id: str) -> List[Conversation]:
        """Get conversations by workflow ID"""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.workflow_id == workflow_id)
            .order_by(desc(Conversation.created_at))
        )
        return result.scalars().all()
    
    async def create(self, conversation: Conversation) -> Conversation:
        """Create a new conversation"""
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
    
    async def update(self, conversation: Conversation) -> Conversation:
        """Update an existing conversation"""
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
    
    async def delete(self, conversation: Conversation) -> None:
        """Delete a conversation"""
        await self.db.delete(conversation)
        await self.db.commit()
    
    async def get_recent_conversations(self, limit: int = 50) -> List[Conversation]:
        """Get recent conversations across all users"""
        result = await self.db.execute(
            select(Conversation)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return result.scalars().all()
