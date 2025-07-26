"""
Dependency injection container for the application
"""
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import (
    AgentRepository,
    WorkflowRepository,
    ConversationRepository,
    LLMRepository,
    MCPToolRepository
)
from app.services import (
    AgentService,
    WorkflowService,
    ConversationService,
    CacheService,
    LLMService,
    MCPToolService
)


class DIContainer:
    """Dependency injection container"""
    
    def __init__(self, db_session: AsyncSession, cache_service: CacheService):
        self.db_session = db_session
        self.cache_service = cache_service
        
        # Initialize repositories
        self._agent_repository = AgentRepository(db_session)
        self._workflow_repository = WorkflowRepository(db_session)
        self._conversation_repository = ConversationRepository(db_session)
        self._llm_repository = LLMRepository(db_session)
        self._mcp_tool_repository = MCPToolRepository(db_session)
        
        # Initialize services
        self._agent_service = AgentService(self._agent_repository)
        self._llm_service = LLMService(self._llm_repository)
        self._mcp_tool_service = MCPToolService(self._mcp_tool_repository)
        self._conversation_service = ConversationService(self._conversation_repository)
        self._workflow_service = WorkflowService(
            self._workflow_repository,
            self._agent_repository,
            self._conversation_repository,
            cache_service
        )
    
    @property
    def agent_repository(self) -> AgentRepository:
        return self._agent_repository
    
    @property
    def workflow_repository(self) -> WorkflowRepository:
        return self._workflow_repository
    
    @property
    def conversation_repository(self) -> ConversationRepository:
        return self._conversation_repository
    
    @property
    def llm_repository(self) -> LLMRepository:
        return self._llm_repository
    
    @property
    def mcp_tool_repository(self) -> MCPToolRepository:
        return self._mcp_tool_repository
    
    @property
    def agent_service(self) -> AgentService:
        return self._agent_service
    
    @property
    def workflow_service(self) -> WorkflowService:
        return self._workflow_service
    
    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service
    
    @property
    def llm_service(self) -> LLMService:
        return self._llm_service
    
    @property
    def mcp_tool_service(self) -> MCPToolService:
        return self._mcp_tool_service


# Global container instance
_container: DIContainer = None


def get_container() -> DIContainer:
    """Get the global dependency injection container"""
    if _container is None:
        raise RuntimeError("DI Container not initialized. Call init_container() first.")
    return _container


def init_container(db_session: AsyncSession, cache_service: CacheService) -> DIContainer:
    """Initialize the global dependency injection container"""
    global _container
    _container = DIContainer(db_session, cache_service)
    return _container
