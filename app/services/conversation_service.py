from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Conversation
from app.schemas import ConversationCreate, ConversationResponse
from app.core.logging import logger
from app.core.metrics import metrics, time_operation


class ConversationService:
    """Service for managing conversations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    @time_operation("conversation_service.save")
    async def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation to database"""
        try:
            logger.debug(f"Saving conversation for user: {conversation_data['userid']}")
            
            conversation = Conversation(
                userid=conversation_data["userid"],
                chatid=conversation_data["chatid"],
                prompt=conversation_data["prompt"],
                pipeline_state=conversation_data["pipeline_state"],
                agent_id=conversation_data["agent_id"],
                pipeline_id=conversation_data["pipeline_id"]
            )
            
            self.session.add(conversation)
            await self.session.commit()
            await self.session.refresh(conversation)
            
            logger.info(f"Conversation saved successfully: {conversation.id}")
            metrics.increment_counter("conversation_service.save", 1, {"status": "success"})
            
            return str(conversation.id)
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            metrics.increment_counter("conversation_service.save", 1, {"status": "error"})
            await self.session.rollback()
            raise
    
    @time_operation("conversation_service.get_by_id")
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        try:
            logger.debug(f"Fetching conversation by ID: {conversation_id}")
            
            result = await self.session.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conversation = result.scalar_one_or_none()
            
            if conversation:
                logger.debug(f"Found conversation: {conversation.id}")
                metrics.increment_counter("conversation_service.get_by_id", 1, {"status": "found"})
            else:
                logger.warning(f"Conversation not found: {conversation_id}")
                metrics.increment_counter("conversation_service.get_by_id", 1, {"status": "not_found"})
            
            return conversation
            
        except Exception as e:
            logger.error(f"Error getting conversation by id {conversation_id}: {e}")
            metrics.increment_counter("conversation_service.get_by_id", 1, {"status": "error"})
            raise
    
    @time_operation("conversation_service.get_by_chat_id")
    async def get_by_chat_id(self, chat_id: str, user_id: str) -> List[Conversation]:
        """Get conversations by chat ID and user ID"""
        try:
            logger.debug(f"Fetching conversations for chat: {chat_id}, user: {user_id}")
            
            result = await self.session.execute(
                select(Conversation)
                .where(Conversation.chatid == chat_id)
                .where(Conversation.userid == user_id)
                .order_by(Conversation.created_at)
            )
            conversations = result.scalars().all()
            
            logger.debug(f"Found {len(conversations)} conversations for chat: {chat_id}")
            metrics.increment_counter("conversation_service.get_by_chat_id", 1, {"count": str(len(conversations))})
            
            return list(conversations)
            
        except Exception as e:
            logger.error(f"Error getting conversations by chat_id {chat_id}: {e}")
            metrics.increment_counter("conversation_service.get_by_chat_id", 1, {"status": "error"})
            raise
    
    @time_operation("conversation_service.get_by_user")
    async def get_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get conversations by user ID with pagination"""
        try:
            logger.debug(f"Fetching conversations for user: {user_id}")
            
            result = await self.session.execute(
                select(Conversation)
                .where(Conversation.userid == user_id)
                .order_by(Conversation.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            conversations = result.scalars().all()
            
            logger.debug(f"Found {len(conversations)} conversations for user: {user_id}")
            metrics.increment_counter("conversation_service.get_by_user", 1, {"count": str(len(conversations))})
            
            return list(conversations)
            
        except Exception as e:
            logger.error(f"Error getting conversations by user {user_id}: {e}")
            metrics.increment_counter("conversation_service.get_by_user", 1, {"status": "error"})
            raise
