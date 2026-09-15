"""Simple in-memory cache for RAG queries to improve response times."""

import hashlib
import json
import time
from typing import Any, Optional
from functools import wraps


class QueryCache:
    """Simple LRU cache for RAG queries with TTL expiration."""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = {}
        self.access_times = {}
    
    def _make_key(self, query: str, top_k: int = 5) -> str:
        """Create a cache key from query parameters."""
        key_data = f"{query.lower().strip()}:{top_k}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, query: str, top_k: int = 5) -> Optional[Any]:
        """Get cached result if available and not expired."""
        key = self._make_key(query, top_k)
        
        if key in self.cache:
            # Check if expired
            if time.time() - self.access_times[key] > self.ttl_seconds:
                del self.cache[key]
                del self.access_times[key]
                return None
            
            # Update access time
            self.access_times[key] = time.time()
            return self.cache[key]
        
        return None
    
    def set(self, query: str, result: Any, top_k: int = 5) -> None:
        """Cache a query result."""
        key = self._make_key(query, top_k)
        
        # Remove oldest if cache is full
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
            del self.cache[oldest_key]
            del self.access_times[oldest_key]
        
        self.cache[key] = result
        self.access_times[key] = time.time()
    
    def clear(self) -> None:
        """Clear the cache."""
        self.cache.clear()
        self.access_times.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.cache)


# Global cache instance
query_cache = QueryCache(max_size=500, ttl_seconds=1800)  # 30 minutes TTL


def cache_rag_response(func):
    """Decorator to cache RAG responses."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract query from arguments
        query = None
        top_k = 5
        
        for arg in args:
            if isinstance(arg, str) and len(arg) > 5:  # Likely a query
                query = arg
                break
        
        if query is None:
            for key, value in kwargs.items():
                if key in ("question", "query", "text") and isinstance(value, str):
                    query = value
                    break
        
        if "top_k" in kwargs:
            top_k = kwargs["top_k"]
        elif len(args) > 1 and isinstance(args[1], int):
            top_k = args[1]
        
        if query:
            cached = query_cache.get(query, top_k)
            if cached is not None:
                return cached
        
        result = func(*args, **kwargs)
        
        if query and result is not None:
            query_cache.set(query, result, top_k)
        
        return result
    
    return wrapper