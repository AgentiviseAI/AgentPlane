"""
Dependency injection container for the application
"""
from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import ConversationRepository
from app.services import WorkflowService, ConversationService, CacheService, LLMService, RestAPIService
from app.services.cache_service import InMemoryCacheService
from app.middleware.controltower_client import controltower_client


# Global cache service (singleton)
cache_service = InMemoryCacheService()


class DIContainer:
    """Dependency injection container"""
    
    def __init__(self, db_session: AsyncSession, cache_service: CacheService):
        self.db_session = db_session
        self.cache_service = cache_service
        
        # Initialize repositories (only what AgentPlane manages)
        self._conversation_repository = ConversationRepository(db_session)
        
        # Initialize services
        self._conversation_service = ConversationService(self._conversation_repository)
        self._llm_service = LLMService(controltower_client)
        self._rest_api_service = RestAPIService(controltower_client)
        self._workflow_service = WorkflowService(
            self._conversation_service,
            cache_service,
            controltower_client,
            self._llm_service,
            self._rest_api_service
        )
    
    @property
    def conversation_repository(self) -> ConversationRepository:
        return self._conversation_repository
    
    @property
    def workflow_service(self) -> WorkflowService:
        return self._workflow_service
    
    @property
    def conversation_service(self) -> ConversationService:
        return self._conversation_service
    
    @property
    def llm_service(self) -> LLMService:
        return self._llm_service


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
