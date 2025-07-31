"""
Redis caching service for improved performance and reduced database load.
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import redis
from redis.exceptions import ConnectionError, RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Comprehensive Redis caching service with multiple strategies."""

    def __init__(self, redis_url: str = None):
        """Initialize Redis connection with fallback handling.
        
        Sets up the Redis caching service with connection management, TTL configuration
        for different data types, and automatic fallback when Redis is unavailable.
        Establishes connection immediately and logs connection status.
        
        Args:
            redis_url: Optional Redis connection URL. If not provided, uses settings.redis_url
                Format: redis://localhost:6379 or redis://user:pass@host:port/db
                
        Note:
            The service gracefully handles Redis unavailability by disabling caching
            operations rather than failing. TTL configuration is optimized for different
            data types (events: 30min, categories: 2h, search: 10min, etc.).
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis = None
        self._connection_failed = False

        # Cache configuration
        self.default_ttl = 3600  # 1 hour
        self.key_prefix = "kruzna_karta"

        # Cache TTL configurations for different data types
        self.ttl_config = {
            "events": 1800,  # 30 minutes
            "event_detail": 3600,  # 1 hour
            "categories": 7200,  # 2 hours
            "venues": 7200,  # 2 hours
            "popular_events": 900,  # 15 minutes
            "search_results": 600,  # 10 minutes
            "analytics": 1800,  # 30 minutes
            "user_session": 86400,  # 24 hours
            "translations": 10800,  # 3 hours
            "static_content": 21600,  # 6 hours
        }

        self._connect()

    def _connect(self) -> None:
        """Establish Redis connection with error handling."""
        try:
            if self.redis_url:
                self._redis = redis.from_url(
                    self.redis_url,
                    decode_responses=False,  # We'll handle encoding manually
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self._redis.ping()
                self._connection_failed = False
                logger.info("Redis connection established successfully")
            else:
                logger.warning("Redis URL not configured, caching disabled")
                self._connection_failed = True
        except (RedisError, ConnectionError) as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connection_failed = True
            self._redis = None

    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        if self._connection_failed or not self._redis:
            return False

        try:
            self._redis.ping()
            return True
        except (RedisError, ConnectionError):
            self._connection_failed = True
            return False

    def _make_key(self, namespace: str, key: str) -> str:
        """Generate cache key with namespace."""
        return f"{self.key_prefix}:{namespace}:{key}"

    def _json_default(self, obj: Any) -> Any:
        """Fallback serializer for non-JSON types."""
        if isinstance(obj, (datetime, timedelta)):
            return obj.isoformat()
        if hasattr(obj, "dict"):
            return obj.dict()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage using JSON."""
        try:
            return json.dumps(value, default=self._json_default).encode("utf-8")
        except (TypeError, ValueError) as e:
            logger.error(f"Failed to serialize cache value: {e}")
            raise

    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first (for simple types)
            return json.loads(value.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"Failed to deserialize cache value: {e}")
            return None

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization and error handling.
        
        Retrieves a cached value from the specified namespace using the provided key.
        Automatically deserializes JSON data and handles connection failures gracefully
        by returning None when Redis is unavailable.
        
        Args:
            namespace: Cache namespace (e.g., "events", "categories", "search_results")
                Used for logical separation and bulk operations
            key: Unique identifier within the namespace for the cached item
                
        Returns:
            Optional[Any]: The cached value if found and successfully deserialized,
                None if key doesn't exist, cache is unavailable, or deserialization fails
                
        Note:
            This method never raises exceptions, returning None on any error to ensure
            application resilience when caching is unavailable.
        """
        if not self.is_available:
            return None

        try:
            cache_key = self._make_key(namespace, key)
            value = self._redis.get(cache_key)

            if value is None:
                return None

            return self._deserialize_value(value)

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    def set(
        self, namespace: str, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL and automatic serialization.
        
        Stores a value in the cache with automatic JSON serialization and configurable
        time-to-live (TTL). Uses namespace-specific default TTLs or provided value.
        Handles serialization of complex objects including datetime and Pydantic models.
        
        Args:
            namespace: Cache namespace for logical separation and TTL configuration
            key: Unique identifier within the namespace for the cached item
            value: Any serializable Python object (dict, list, string, number, datetime,
                Pydantic models, objects with __dict__ attribute)
            ttl: Optional TTL in seconds. If None, uses namespace-specific default:
                - events: 1800s (30min), categories: 7200s (2h), search_results: 600s (10min)
                
        Returns:
            bool: True if value was successfully stored, False if operation failed
                or Redis is unavailable
                
        Note:
            The method automatically handles object serialization using JSON with
            custom handlers for datetime objects and Pydantic models.
        """
        if not self.is_available:
            return False

        try:
            cache_key = self._make_key(namespace, key)
            serialized_value = self._serialize_value(value)

            # Use namespace-specific TTL or default
            cache_ttl = ttl or self.ttl_config.get(namespace, self.default_ttl)

            result = self._redis.setex(cache_key, cache_ttl, serialized_value)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    def delete(self, namespace: str, key: str) -> bool:
        """Delete value from cache with error handling.
        
        Removes a specific cached item from the given namespace. Used for cache
        invalidation when data changes or manual cache management.
        
        Args:
            namespace: Cache namespace containing the key to delete
            key: Unique identifier of the cached item to remove
                
        Returns:
            bool: True if key was successfully deleted (or didn't exist),
                False if operation failed or Redis is unavailable
                
        Note:
            Returns True even if the key didn't exist, matching Redis behavior.
            Never raises exceptions to maintain application stability.
        """
        if not self.is_available:
            return False

        try:
            cache_key = self._make_key(namespace, key)
            result = self._redis.delete(cache_key)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    def invalidate_pattern(self, namespace: str, pattern: str = "*") -> int:
        """Invalidate all keys matching pattern in namespace with batch processing.
        
        Efficiently removes multiple cache keys matching a pattern within a namespace.
        Uses batch processing to handle large numbers of keys without blocking Redis.
        Essential for cache invalidation when related data changes.
        
        Args:
            namespace: Cache namespace to search within
            pattern: Redis pattern to match keys against (default: "*" for all keys)
                Supports wildcards: * (any chars), ? (single char), [abc] (char set)
                
        Returns:
            int: Number of keys successfully deleted from the cache
                
        Note:
            Uses SCAN for memory-efficient iteration and batches deletions in groups
            of 500 to prevent blocking Redis. Logs the number of deleted keys for
            monitoring cache invalidation operations.
        """
        if not self.is_available:
            return 0

        try:
            cache_pattern = self._make_key(namespace, pattern)
            deleted = 0
            batch: List[bytes] = []
            for key in self._redis.scan_iter(match=cache_pattern, count=1000):
                batch.append(key)
                if len(batch) >= 500:
                    deleted += self._redis.delete(*batch)
                    batch = []

            if batch:
                deleted += self._redis.delete(*batch)

            if deleted:
                logger.info(
                    f"Invalidated {deleted} cache keys matching {cache_pattern}"
                )
            return deleted

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    def get_multiple(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        if not self.is_available or not keys:
            return {}

        try:
            cache_keys = [self._make_key(namespace, key) for key in keys]
            values = self._redis.mget(cache_keys)

            result = {}
            for i, value in enumerate(values):
                if value is not None:
                    try:
                        result[keys[i]] = self._deserialize_value(value)
                    except Exception as e:
                        logger.error(
                            f"Error deserializing cache value for key {keys[i]}: {e}"
                        )

            return result

        except Exception as e:
            logger.error(f"Cache mget error: {e}")
            return {}

    def set_multiple(
        self, namespace: str, data: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """Set multiple values in cache."""
        if not self.is_available or not data:
            return False

        try:
            cache_ttl = ttl or self.ttl_config.get(namespace, self.default_ttl)
            pipe = self._redis.pipeline()

            for key, value in data.items():
                cache_key = self._make_key(namespace, key)
                serialized_value = self._serialize_value(value)
                pipe.setex(cache_key, cache_ttl, serialized_value)

            results = pipe.execute()
            return all(results)

        except Exception as e:
            logger.error(f"Cache mset error: {e}")
            return False

    def increment(
        self, namespace: str, key: str, amount: int = 1, ttl: Optional[int] = None
    ) -> Optional[int]:
        """Increment a counter in cache."""
        if not self.is_available:
            return None

        try:
            cache_key = self._make_key(namespace, key)

            # Use pipeline for atomic operation
            pipe = self._redis.pipeline()
            pipe.incr(cache_key, amount)

            if ttl:
                pipe.expire(cache_key, ttl)

            results = pipe.execute()
            return results[0]

        except Exception as e:
            logger.error(f"Cache increment error: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics and performance metrics.
        
        Retrieves detailed information about Redis performance, memory usage,
        connection status, and namespace-specific statistics. Essential for
        monitoring cache effectiveness and identifying performance issues.
        
        Returns:
            Dict containing cache statistics:
                - status: "available", "unavailable", or "error"
                - redis_connected: Boolean connection status
                - redis_version: Redis server version
                - used_memory: Human-readable memory usage
                - connected_clients: Number of client connections
                - total_commands_processed: Lifetime command count
                - keyspace_hits/misses: Cache hit/miss counters
                - hit_ratio: Cache hit ratio percentage
                - uptime_seconds: Redis server uptime
                - namespace_stats: Key counts per namespace
                
        Note:
            Returns limited information when Redis is unavailable. Used by
            monitoring systems to track cache performance and health.
        """
        if not self.is_available:
            return {"status": "unavailable", "redis_connected": False}

        try:
            info = self._redis.info()

            return {
                "status": "available",
                "redis_connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_ratio": self._calculate_hit_ratio(info),
                "uptime_seconds": info.get("uptime_in_seconds"),
                "namespace_stats": self._get_namespace_stats(),
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_ratio(self, info: Dict) -> float:
        """Calculate cache hit ratio."""
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses

        if total == 0:
            return 0.0

        return round((hits / total) * 100, 2)

    def _get_namespace_stats(self) -> Dict[str, int]:
        """Get statistics by namespace."""
        if not self.is_available:
            return {}

        try:
            namespace_counts = {}

            for namespace in self.ttl_config.keys():
                pattern = self._make_key(namespace, "*")
                count = sum(1 for _ in self._redis.scan_iter(match=pattern, count=1000))
                namespace_counts[namespace] = count

            return namespace_counts

        except Exception as e:
            logger.error(f"Error getting namespace stats: {e}")
            return {}

    def flush_namespace(self, namespace: str) -> int:
        """Flush all keys in a namespace."""
        return self.invalidate_pattern(namespace, "*")

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on cache service.
        
        Executes a series of tests to verify cache functionality including basic
        operations (set/get/delete), performance metrics, and connection status.
        Provides detailed diagnostics for monitoring and troubleshooting.
        
        Returns:
            Dict containing health check results:
                - timestamp: ISO format timestamp of the check
                - service: "cache" identifier
                - status: "healthy", "degraded", or "unhealthy"
                - redis_connected: Boolean connection status
                - issues: List of identified problems (if any)
                - set_success/get_success/delete_success: Operation test results
                - hit_ratio: Current cache hit ratio percentage
                - used_memory: Memory usage information
                - connected_clients: Number of active connections
                
        Note:
            Performs actual cache operations with a test key to verify functionality.
            Safe to call frequently as it uses minimal resources and cleans up test data.
        """
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "service": "cache",
            "status": "healthy",
        }

        if not self.is_available:
            health_data.update(
                {
                    "status": "unhealthy",
                    "issues": ["Redis connection failed"],
                    "redis_connected": False,
                }
            )
            return health_data

        try:
            # Test basic operations
            test_key = "health_check"
            test_value = {"timestamp": datetime.now().isoformat()}

            # Test set/get/delete
            set_success = self.set("health", test_key, test_value, ttl=60)
            get_result = self.get("health", test_key)
            delete_success = self.delete("health", test_key)

            if not set_success or get_result != test_value or not delete_success:
                health_data.update(
                    {
                        "status": "degraded",
                        "issues": ["Cache operations failing"],
                        "set_success": set_success,
                        "get_success": get_result == test_value,
                        "delete_success": delete_success,
                    }
                )

            # Add performance metrics
            stats = self.get_stats()
            health_data.update(
                {
                    "redis_connected": True,
                    "hit_ratio": stats.get("hit_ratio", 0),
                    "used_memory": stats.get("used_memory"),
                    "connected_clients": stats.get("connected_clients"),
                }
            )

        except Exception as e:
            health_data.update(
                {
                    "status": "unhealthy",
                    "issues": [f"Health check failed: {str(e)}"],
                    "error": str(e),
                }
            )

        return health_data


def cache_key_generator(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    # Create a string representation of arguments
    key_parts = []

    # Add positional arguments
    for arg in args:
        if hasattr(arg, "id"):  # Database objects
            key_parts.append(f"{type(arg).__name__}_{arg.id}")
        else:
            key_parts.append(str(arg))

    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, "id"):
            key_parts.append(f"{k}_{type(v).__name__}_{v.id}")
        else:
            key_parts.append(f"{k}_{v}")

    # Create hash for long keys
    key_string = "_".join(key_parts)
    if len(key_string) > 200:
        key_string = hashlib.md5(key_string.encode()).hexdigest()

    return key_string


def cached(
    namespace: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None
) -> Callable:
    """Decorator for caching function results with automatic key generation.
    
    Provides transparent caching for function calls by storing results in Redis
    and returning cached values on subsequent calls with the same arguments.
    Includes cache invalidation methods and handles cache misses gracefully.
    
    Args:
        namespace: Cache namespace for logical separation (e.g., "events", "search")
        ttl: Optional TTL in seconds. If None, uses namespace-specific default
        key_func: Optional custom function to generate cache keys from arguments
            Signature: key_func(*args, **kwargs) -> str
            
    Returns:
        Callable: Decorator function that wraps the target function with caching
        
    Note:
        The decorated function gains two additional methods:
        - invalidate(*args, **kwargs): Remove specific cached result
        - invalidate_all(): Remove all cached results for this function
        
        Automatic key generation handles database objects, basic types, and
        creates MD5 hashes for long keys to stay within Redis limits.
        
    Example:
        @cached("events", ttl=1800)
        def get_popular_events(category_id: int) -> List[Event]:
            return db.query(Event).filter(...).all()
    """

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get cache service
            cache = get_cache_service()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}_{cache_key_generator(*args, **kwargs)}"

            # Try to get from cache
            cached_result = cache.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(namespace, cache_key, result, ttl)

            return result

        # Add cache control methods
        wrapper.invalidate = lambda *args, **kwargs: get_cache_service().delete(
            namespace,
            (
                key_func(*args, **kwargs)
                if key_func
                else f"{func.__name__}_{cache_key_generator(*args, **kwargs)}"
            ),
        )
        wrapper.invalidate_all = lambda: get_cache_service().flush_namespace(namespace)

        return wrapper

    return decorator


def cache_invalidate_on_change(namespaces: List[str]) -> Callable:
    """Decorator to invalidate cache when data changes."""

    def decorator(func) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Invalidate specified namespaces
            cache = get_cache_service()
            for namespace in namespaces:
                cache.flush_namespace(namespace)
                logger.info(f"Invalidated cache namespace: {namespace}")

            return result

        return wrapper

    return decorator


# Global cache service instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get global cache service instance with lazy initialization.
    
    Returns the singleton CacheService instance, creating it on first access.
    Provides consistent access to caching functionality across the application
    without requiring manual initialization in most cases.
    
    Returns:
        CacheService: The global cache service instance with Redis connection
        
    Note:
        Uses lazy initialization pattern - the service is created on first access
        using default configuration from settings. For custom configuration,
        use init_cache_service() before first access.
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def init_cache_service(redis_url: str = None) -> CacheService:
    """Initialize cache service with custom configuration.
    
    Creates a new CacheService instance with custom Redis URL, replacing any
    existing global instance. Used for testing, development, or when multiple
    Redis instances are needed.
    
    Args:
        redis_url: Optional custom Redis connection URL. If not provided,
            uses the default from settings
            
    Returns:
        CacheService: Newly created cache service instance
        
    Note:
        This function replaces the global cache service instance, affecting
        all subsequent calls to get_cache_service(). Primarily used during
        application startup or in test environments.
    """
    global _cache_service
    _cache_service = CacheService(redis_url)
    return _cache_service
