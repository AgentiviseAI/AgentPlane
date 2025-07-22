from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from app.core.logging import logger
from app.core.metrics import metrics, time_operation


class CacheService(ABC):
    """Abstract cache service interface"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        pass


class InMemoryCacheService(CacheService):
    """In-memory cache implementation"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._ttl: Dict[str, float] = {}
        logger.info("Initialized InMemoryCacheService")
    
    @time_operation("cache_service.get")
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        import time
        
        logger.debug(f"Cache get: {key}")
        
        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            metrics.increment_counter("cache_service.get", 1, {"status": "miss"})
            return None
        
        # Check TTL
        if key in self._ttl and time.time() > self._ttl[key]:
            logger.debug(f"Cache expired: {key}")
            await self.delete(key)
            metrics.increment_counter("cache_service.get", 1, {"status": "expired"})
            return None
        
        logger.debug(f"Cache hit: {key}")
        metrics.increment_counter("cache_service.get", 1, {"status": "hit"})
        return self._cache.get(key)
    
    @time_operation("cache_service.set")
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache"""
        import time
        
        logger.debug(f"Cache set: {key} (TTL: {ttl})")
        
        self._cache[key] = value
        if ttl:
            self._ttl[key] = time.time() + ttl
        
        metrics.increment_counter("cache_service.set", 1)
        metrics.set_gauge("cache_service.size", len(self._cache))
    
    @time_operation("cache_service.delete")
    async def delete(self, key: str) -> None:
        """Delete value from cache"""
        logger.debug(f"Cache delete: {key}")
        
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
        
        metrics.increment_counter("cache_service.delete", 1)
        metrics.set_gauge("cache_service.size", len(self._cache))
    
    def clear(self) -> None:
        """Clear all cache entries"""
        logger.info("Clearing cache")
        self._cache.clear()
        self._ttl.clear()
        metrics.increment_counter("cache_service.clear", 1)
        metrics.set_gauge("cache_service.size", 0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self._cache),
            "ttl_entries": len(self._ttl)
        }
