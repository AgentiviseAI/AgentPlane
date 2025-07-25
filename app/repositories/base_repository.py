"""
Base Repository implementation with common functionality
"""
from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar, Generic, Optional, List, Type

# Type variable for model types
ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ModelType]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    async def create(self, entity: ModelType) -> ModelType:
        """Create a new entity"""
        pass
    
    @abstractmethod
    async def update(self, entity: ModelType) -> ModelType:
        """Update an existing entity"""
        pass
    
    @abstractmethod
    async def delete(self, entity: ModelType) -> None:
        """Delete an entity"""
        pass
    
    async def commit(self) -> None:
        """Commit the current transaction"""
        await self.db.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction"""
        await self.db.rollback()
    
    async def refresh(self, entity: ModelType) -> None:
        """Refresh an entity from the database"""
        await self.db.refresh(entity)
