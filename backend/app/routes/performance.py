"""
Performance monitoring and cache management endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.auth import get_current_active_user
from ..core.permissions import require_admin
from ..core.cache import get_cache_service
from ..core.database import get_db, get_db_pool_status, health_check_db
from ..core.performance import get_performance_service
from ..models.user import User

router = APIRouter(prefix="/performance", tags=["performance"])


@router.get("/health")
def health_check():
    """Comprehensive system health check."""

    # Database health
    db_health = health_check_db()

    # Cache health
    cache_service = get_cache_service()
    cache_health = cache_service.health_check()

    # Overall status
    overall_status = "healthy"
    if db_health["status"] != "healthy" or cache_health["status"] != "healthy":
        overall_status = "unhealthy"
    elif cache_health["status"] == "degraded":
        overall_status = "degraded"

    return {
        "timestamp": datetime.now().isoformat(),
        "status": overall_status,
        "components": {"database": db_health, "cache": cache_health},
        "version": "1.0.0",
    }


@router.get("/stats")
def get_performance_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get detailed performance statistics (admin only)."""

    require_admin(current_user)

    performance_service = get_performance_service(db)
    stats = performance_service.get_performance_stats()

    return {"timestamp": datetime.now().isoformat(), "performance_stats": stats}


@router.get("/cache/stats")
def get_cache_stats(current_user: User = Depends(get_current_active_user)):
    """Get cache performance statistics (admin only)."""

    require_admin(current_user)

    cache_service = get_cache_service()
    return cache_service.get_stats()


@router.post("/cache/invalidate/{namespace}")
def invalidate_cache_namespace(
    namespace: str,
    pattern: str = Query(
        "*", description="Pattern to match keys (default: all keys in namespace)"
    ),
    current_user: User = Depends(get_current_active_user),
):
    """Invalidate cache namespace (admin only)."""

    require_admin(current_user)

    cache_service = get_cache_service()

    # Validate namespace
    valid_namespaces = [
        "events",
        "event_detail",
        "categories",
        "venues",
        "popular_events",
        "search_results",
        "analytics",
        "user_session",
        "translations",
        "static_content",
    ]

    if namespace not in valid_namespaces:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid namespace. Valid options: {', '.join(valid_namespaces)}",
        )

    deleted_count = cache_service.invalidate_pattern(namespace, pattern)

    return {
        "namespace": namespace,
        "pattern": pattern,
        "deleted_keys": deleted_count,
        "message": f"Invalidated {deleted_count} keys in namespace '{namespace}'",
    }


@router.post("/cache/flush/{namespace}")
def flush_cache_namespace(
    namespace: str, current_user: User = Depends(get_current_active_user)
):
    """Flush entire cache namespace (admin only)."""

    require_admin(current_user)

    cache_service = get_cache_service()
    deleted_count = cache_service.flush_namespace(namespace)

    return {
        "namespace": namespace,
        "deleted_keys": deleted_count,
        "message": f"Flushed namespace '{namespace}' - deleted {deleted_count} keys",
    }


@router.get("/database/pool")
def get_database_pool_stats(current_user: User = Depends(get_current_active_user)):
    """Get database connection pool statistics (admin only)."""

    require_admin(current_user)

    pool_stats = get_db_pool_status()

    return {
        "timestamp": datetime.now().isoformat(),
        "pool_stats": pool_stats,
        "recommendations": _generate_pool_recommendations(pool_stats),
    }


@router.get("/metrics/summary")
def get_performance_summary(
    include_cache: bool = Query(True, description="Include cache metrics"),
    include_database: bool = Query(True, description="Include database metrics"),
    current_user: User = Depends(get_current_active_user),
):
    """Get performance summary (admin only)."""

    require_admin(current_user)

    summary = {"timestamp": datetime.now().isoformat(), "system_status": "healthy"}

    if include_cache:
        cache_service = get_cache_service()
        cache_stats = cache_service.get_stats()

        summary["cache"] = {
            "status": cache_stats.get("status", "unknown"),
            "hit_ratio": cache_stats.get("hit_ratio", 0),
            "used_memory": cache_stats.get("used_memory", "Unknown"),
            "connected_clients": cache_stats.get("connected_clients", 0),
        }

        if cache_stats.get("status") != "available":
            summary["system_status"] = "degraded"

    if include_database:
        db_health = health_check_db()
        pool_stats = get_db_pool_status()

        summary["database"] = {
            "status": db_health.get("status", "unknown"),
            "pool_utilization": _calculate_pool_utilization(pool_stats),
            "active_connections": pool_stats.get("checked_out", 0),
            "available_connections": pool_stats.get("checked_in", 0),
        }

        if db_health.get("status") != "healthy":
            summary["system_status"] = "unhealthy"

    return summary


@router.post("/optimize/cache-warmup")
def warm_up_cache(
    categories: bool = Query(True, description="Warm up categories cache"),
    venues: bool = Query(True, description="Warm up venues cache"),
    popular_events: bool = Query(True, description="Warm up popular events cache"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Warm up frequently accessed cache data (admin only)."""

    require_admin(current_user)

    performance_service = get_performance_service(db)
    warmed_caches = []

    try:
        if categories:
            performance_service.get_categories_optimized("hr")
            performance_service.get_categories_optimized("en")
            warmed_caches.append("categories")

        if venues:
            performance_service.get_venues_optimized(language="hr")
            performance_service.get_venues_optimized(language="en")
            warmed_caches.append("venues")

        if popular_events:
            performance_service.get_popular_events_optimized(limit=20, language="hr")
            performance_service.get_popular_events_optimized(limit=20, language="en")
            warmed_caches.append("popular_events")

        return {
            "status": "success",
            "warmed_caches": warmed_caches,
            "message": f"Successfully warmed up {len(warmed_caches)} cache namespaces",
        }

    except Exception as e:
        return {
            "status": "partial_success",
            "warmed_caches": warmed_caches,
            "error": str(e),
            "message": f"Warmed up {len(warmed_caches)} caches before error occurred",
        }


@router.get("/recommendations")
def get_performance_recommendations(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get performance optimization recommendations (admin only)."""

    require_admin(current_user)

    recommendations = []

    # Cache recommendations
    cache_service = get_cache_service()
    cache_stats = cache_service.get_stats()

    if not cache_stats.get("redis_connected", False):
        recommendations.append(
            {
                "category": "cache",
                "priority": "high",
                "title": "Redis Not Connected",
                "description": "Redis cache is not available, falling back to database queries",
                "action": "Check Redis connection and configuration",
            }
        )
    elif cache_stats.get("hit_ratio", 0) < 60:
        recommendations.append(
            {
                "category": "cache",
                "priority": "medium",
                "title": "Low Cache Hit Ratio",
                "description": f"Cache hit ratio is {cache_stats.get('hit_ratio', 0)}%, consider tuning TTL values",
                "action": "Review cache TTL configuration and usage patterns",
            }
        )

    # Database recommendations
    pool_stats = get_db_pool_status()
    pool_utilization = _calculate_pool_utilization(pool_stats)

    if pool_utilization > 80:
        recommendations.append(
            {
                "category": "database",
                "priority": "high",
                "title": "High Database Pool Utilization",
                "description": f"Connection pool is {pool_utilization}% utilized",
                "action": "Consider increasing pool size or optimizing query performance",
            }
        )
    elif pool_utilization > 60:
        recommendations.append(
            {
                "category": "database",
                "priority": "medium",
                "title": "Moderate Database Pool Utilization",
                "description": f"Connection pool is {pool_utilization}% utilized",
                "action": "Monitor pool usage and consider optimization",
            }
        )

    # Performance recommendations
    performance_service = get_performance_service(db)
    perf_stats = performance_service.get_performance_stats()

    if not perf_stats.get("optimization_status", {}).get("caching_enabled", False):
        recommendations.append(
            {
                "category": "performance",
                "priority": "high",
                "title": "Caching Disabled",
                "description": "Performance caching is disabled",
                "action": "Enable caching for better performance",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "category": "general",
                "priority": "info",
                "title": "System Running Optimally",
                "description": "No performance issues detected",
                "action": "Continue monitoring system metrics",
            }
        )

    return {
        "timestamp": datetime.now().isoformat(),
        "recommendations": recommendations,
        "total_recommendations": len(recommendations),
    }


def _calculate_pool_utilization(pool_stats: Dict[str, Any]) -> float:
    """Calculate database pool utilization percentage."""
    total_connections = pool_stats.get("pool_size", 0) + pool_stats.get("overflow", 0)
    active_connections = pool_stats.get("checked_out", 0)

    if total_connections == 0:
        return 0.0

    return round((active_connections / total_connections) * 100, 2)


def _generate_pool_recommendations(pool_stats: Dict[str, Any]) -> list:
    """Generate recommendations based on pool statistics."""
    recommendations = []
    utilization = _calculate_pool_utilization(pool_stats)

    if utilization > 90:
        recommendations.append(
            "Critical: Pool utilization very high. Increase pool size immediately."
        )
    elif utilization > 80:
        recommendations.append(
            "Warning: Pool utilization high. Consider increasing pool size."
        )
    elif utilization > 60:
        recommendations.append("Monitor: Pool utilization moderate. Watch for trends.")
    else:
        recommendations.append("Good: Pool utilization is healthy.")

    if pool_stats.get("invalid", 0) > 0:
        recommendations.append(
            f"Warning: {pool_stats['invalid']} invalid connections detected."
        )

    return recommendations
