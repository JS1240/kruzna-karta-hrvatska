"""
Database and application monitoring system with Prometheus integration.
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

import psutil
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to collect."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"
    INFO = "info"


class AlertSeverity(Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class MetricAlert:
    """Configuration for metric-based alerts."""

    metric_name: str
    threshold: float
    comparison: str  # gt, lt, eq, gte, lte
    severity: AlertSeverity
    message: str
    enabled: bool = True


@dataclass
class DatabaseMetrics:
    """Database performance metrics."""

    active_connections: int
    idle_connections: int
    total_connections: int
    database_size_bytes: int
    total_queries: int
    slow_queries: int
    cache_hit_ratio: float
    deadlocks: int
    locks_waiting: int
    temp_files: int
    temp_bytes: int
    checkpoints_timed: int
    checkpoints_requested: int
    buffers_checkpoint: int
    buffers_clean: int
    buffers_backend: int


@dataclass
class ApplicationMetrics:
    """Application-level metrics."""

    total_events: int
    active_events: int
    total_users: int
    active_users: int
    api_requests_total: int
    api_requests_per_minute: float
    cache_hit_ratio: float
    cache_miss_ratio: float
    scraping_events_total: int
    scraping_success_rate: float


class PrometheusMonitoring:
    """Prometheus metrics collection and monitoring service."""

    def __init__(self):
        # Create custom registry for our metrics
        self.registry = CollectorRegistry()

        # Database metrics
        self.db_connections_active = Gauge(
            "kruzna_karta_db_connections_active",
            "Number of active database connections",
            registry=self.registry,
        )

        self.db_connections_idle = Gauge(
            "kruzna_karta_db_connections_idle",
            "Number of idle database connections",
            registry=self.registry,
        )

        self.db_size_bytes = Gauge(
            "kruzna_karta_db_size_bytes",
            "Database size in bytes",
            registry=self.registry,
        )

        self.db_cache_hit_ratio = Gauge(
            "kruzna_karta_db_cache_hit_ratio",
            "Database buffer cache hit ratio",
            registry=self.registry,
        )

        self.db_slow_queries = Counter(
            "kruzna_karta_db_slow_queries_total",
            "Total number of slow queries (>1s)",
            registry=self.registry,
        )

        self.db_deadlocks = Counter(
            "kruzna_karta_db_deadlocks_total",
            "Total number of deadlocks",
            registry=self.registry,
        )

        # Application metrics
        self.api_requests_total = Counter(
            "kruzna_karta_api_requests_total",
            "Total API requests",
            ["method", "endpoint", "status"],
            registry=self.registry,
        )

        self.api_request_duration = Histogram(
            "kruzna_karta_api_request_duration_seconds",
            "API request duration",
            ["method", "endpoint"],
            registry=self.registry,
        )

        self.events_total = Gauge(
            "kruzna_karta_events_total",
            "Total number of events",
            ["status"],
            registry=self.registry,
        )

        self.users_total = Gauge(
            "kruzna_karta_users_total",
            "Total number of users",
            ["status"],
            registry=self.registry,
        )

        self.cache_operations = Counter(
            "kruzna_karta_cache_operations_total",
            "Total cache operations",
            ["operation", "result"],
            registry=self.registry,
        )

        self.scraping_events = Counter(
            "kruzna_karta_scraping_events_total",
            "Total scraping events",
            ["source", "status"],
            registry=self.registry,
        )

        # System metrics
        self.system_cpu_usage = Gauge(
            "kruzna_karta_system_cpu_usage_percent",
            "System CPU usage percentage",
            registry=self.registry,
        )

        self.system_memory_usage = Gauge(
            "kruzna_karta_system_memory_usage_bytes",
            "System memory usage in bytes",
            registry=self.registry,
        )

        self.system_disk_usage = Gauge(
            "kruzna_karta_system_disk_usage_percent",
            "System disk usage percentage",
            ["mount_point"],
            registry=self.registry,
        )

        # Application info
        self.app_info = Info(
            "kruzna_karta_app_info", "Application information", registry=self.registry
        )

        # Set application info
        self.app_info.info(
            {
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "database": settings.db_name,
                "python_version": "3.11",
            }
        )

        # Alert configurations
        self.alert_configs = [
            MetricAlert(
                metric_name="db_connections_active",
                threshold=80,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                message="High database connection usage: {value}% of pool",
            ),
            MetricAlert(
                metric_name="db_cache_hit_ratio",
                threshold=0.90,
                comparison="lt",
                severity=AlertSeverity.WARNING,
                message="Low database cache hit ratio: {value}%",
            ),
            MetricAlert(
                metric_name="api_request_duration_p95",
                threshold=2.0,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                message="High API response time: P95 = {value}s",
            ),
            MetricAlert(
                metric_name="system_cpu_usage",
                threshold=80.0,
                comparison="gt",
                severity=AlertSeverity.WARNING,
                message="High CPU usage: {value}%",
            ),
            MetricAlert(
                metric_name="system_memory_usage",
                threshold=85.0,
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                message="High memory usage: {value}%",
            ),
            MetricAlert(
                metric_name="db_deadlocks_rate",
                threshold=5,
                comparison="gt",
                severity=AlertSeverity.CRITICAL,
                message="High deadlock rate: {value} deadlocks/hour",
            ),
        ]

        # Metrics collection state
        self.last_collection_time = datetime.now()
        self.collection_interval = 30  # seconds
        self.enabled = os.getenv("MONITORING_ENABLED", "true").lower() == "true"

        # Cached database metrics and refresh settings
        # Metrics are refreshed only after this interval (default 60s) to avoid
        # excessive database queries. Adjust via DB_METRICS_REFRESH_INTERVAL
        # environment variable.
        self.db_metrics_refresh_interval = int(
            os.getenv("DB_METRICS_REFRESH_INTERVAL", "60")
        )  # seconds
        self.db_metrics_cache: Optional[DatabaseMetrics] = None
        self.db_metrics_last_updated = datetime.min

        logger.info("Prometheus monitoring service initialized")

    async def collect_database_metrics(
        self, force_refresh: bool = False
    ) -> DatabaseMetrics:
        """Collect comprehensive database metrics with simple caching.

        Metrics are cached for ``self.db_metrics_refresh_interval`` seconds to
        reduce database load. Use ``force_refresh=True`` to bypass the cache.
        """
        now = datetime.now()
        if (
            not force_refresh
            and self.db_metrics_cache is not None
            and now - self.db_metrics_last_updated
            < timedelta(seconds=self.db_metrics_refresh_interval)
        ):
            return self.db_metrics_cache

        try:
            db = next(get_db())

            # Connection statistics
            connection_stats = db.execute(
                text(
                    """
                SELECT 
                    state,
                    COUNT(*) as count
                FROM pg_stat_activity 
                WHERE datname = :db_name
                GROUP BY state
            """
                ),
                {"db_name": settings.db_name},
            ).fetchall()

            active_connections = 0
            idle_connections = 0
            total_connections = 0

            for stat in connection_stats:
                count = stat.count
                total_connections += count
                if stat.state == "active":
                    active_connections = count
                elif stat.state == "idle":
                    idle_connections = count

            # Database size
            db_size_result = db.execute(
                text(
                    """
                SELECT pg_database_size(:db_name) as size_bytes
            """
                ),
                {"db_name": settings.db_name},
            ).fetchone()

            database_size_bytes = db_size_result.size_bytes if db_size_result else 0

            # Query statistics
            query_stats = db.execute(
                text(
                    """
                SELECT 
                    SUM(calls) as total_queries,
                    SUM(CASE WHEN mean_time > 1000 THEN calls ELSE 0 END) as slow_queries
                FROM pg_stat_statements
                WHERE dbid = (SELECT oid FROM pg_database WHERE datname = :db_name)
            """
                ),
                {"db_name": settings.db_name},
            ).fetchone()

            total_queries = (
                query_stats.total_queries
                if query_stats and query_stats.total_queries
                else 0
            )
            slow_queries = (
                query_stats.slow_queries
                if query_stats and query_stats.slow_queries
                else 0
            )

            # Cache hit ratio
            cache_stats = db.execute(
                text(
                    """
                SELECT 
                    ROUND(
                        (blks_hit::float / (blks_hit + blks_read)) * 100, 2
                    ) as cache_hit_ratio
                FROM pg_stat_database 
                WHERE datname = :db_name
            """
                )
            ).fetchone()

            cache_hit_ratio = cache_stats.cache_hit_ratio if cache_stats else 0.0

            # Lock statistics
            lock_stats = db.execute(
                text(
                    """
                SELECT 
                    COUNT(*) FILTER (WHERE NOT granted) as locks_waiting
                FROM pg_locks
            """
                )
            ).fetchone()

            locks_waiting = lock_stats.locks_waiting if lock_stats else 0

            # Checkpoint and buffer statistics
            bgwriter_stats = db.execute(
                text(
                    """
                SELECT 
                    checkpoints_timed,
                    checkpoints_req as checkpoints_requested,
                    buffers_checkpoint,
                    buffers_clean,
                    buffers_backend
                FROM pg_stat_bgwriter
            """
                )
            ).fetchone()

            checkpoints_timed = (
                bgwriter_stats.checkpoints_timed if bgwriter_stats else 0
            )
            checkpoints_requested = (
                bgwriter_stats.checkpoints_requested if bgwriter_stats else 0
            )
            buffers_checkpoint = (
                bgwriter_stats.buffers_checkpoint if bgwriter_stats else 0
            )
            buffers_clean = bgwriter_stats.buffers_clean if bgwriter_stats else 0
            buffers_backend = bgwriter_stats.buffers_backend if bgwriter_stats else 0

            # Temporary file statistics
            temp_stats = db.execute(
                text(
                    """
                SELECT 
                    SUM(temp_files) as temp_files,
                    SUM(temp_bytes) as temp_bytes
                FROM pg_stat_database
                WHERE datname = :db_name
            """
                ),
                {"db_name": settings.db_name},
            ).fetchone()

            temp_files = (
                temp_stats.temp_files if temp_stats and temp_stats.temp_files else 0
            )
            temp_bytes = (
                temp_stats.temp_bytes if temp_stats and temp_stats.temp_bytes else 0
            )

            db.close()

            metrics = DatabaseMetrics(
                active_connections=active_connections,
                idle_connections=idle_connections,
                total_connections=total_connections,
                database_size_bytes=database_size_bytes,
                total_queries=total_queries,
                slow_queries=slow_queries,
                cache_hit_ratio=cache_hit_ratio,
                deadlocks=0,  # Will be collected separately
                locks_waiting=locks_waiting,
                temp_files=temp_files,
                temp_bytes=temp_bytes,
                checkpoints_timed=checkpoints_timed,
                checkpoints_requested=checkpoints_requested,
                buffers_checkpoint=buffers_checkpoint,
                buffers_clean=buffers_clean,
                buffers_backend=buffers_backend,
            )

            # Update cache with latest metrics
            self.db_metrics_cache = metrics
            self.db_metrics_last_updated = now

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {e}")
            return DatabaseMetrics(
                active_connections=0,
                idle_connections=0,
                total_connections=0,
                database_size_bytes=0,
                total_queries=0,
                slow_queries=0,
                cache_hit_ratio=0.0,
                deadlocks=0,
                locks_waiting=0,
                temp_files=0,
                temp_bytes=0,
                checkpoints_timed=0,
                checkpoints_requested=0,
                buffers_checkpoint=0,
                buffers_clean=0,
                buffers_backend=0,
            )

    async def get_cached_database_metrics(self) -> DatabaseMetrics:
        """Get cached database metrics without forcing a refresh."""
        return await self.collect_database_metrics()

    async def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-level metrics."""
        try:
            db = next(get_db())

            # Event statistics
            event_stats = db.execute(
                text(
                    """
                SELECT 
                    event_status,
                    COUNT(*) as count
                FROM events
                GROUP BY event_status
            """
                )
            ).fetchall()

            total_events = sum(stat.count for stat in event_stats)
            active_events = sum(
                stat.count for stat in event_stats if stat.event_status == "active"
            )

            # User statistics
            user_stats = db.execute(
                text(
                    """
                SELECT 
                    is_active,
                    COUNT(*) as count
                FROM users
                GROUP BY is_active
            """
                )
            ).fetchall()

            total_users = sum(stat.count for stat in user_stats)
            active_users = sum(stat.count for stat in user_stats if stat.is_active)

            # API request statistics (from logs or metrics)
            # This would typically be collected from application logs or a metrics store
            api_requests_total = 0  # Placeholder
            api_requests_per_minute = 0.0  # Placeholder

            # Cache statistics (would be collected from Redis monitoring)
            cache_hit_ratio = 0.0  # Placeholder
            cache_miss_ratio = 0.0  # Placeholder

            # Scraping statistics
            scraping_stats = db.execute(
                text(
                    """
                SELECT 
                    COUNT(*) as total_scraped,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 day') as recent_scraped
                FROM events
                WHERE source IS NOT NULL
            """
                )
            ).fetchone()

            scraping_events_total = (
                scraping_stats.total_scraped if scraping_stats else 0
            )
            scraping_success_rate = (
                95.0  # Placeholder - would calculate from scraping logs
            )

            db.close()

            return ApplicationMetrics(
                total_events=total_events,
                active_events=active_events,
                total_users=total_users,
                active_users=active_users,
                api_requests_total=api_requests_total,
                api_requests_per_minute=api_requests_per_minute,
                cache_hit_ratio=cache_hit_ratio,
                cache_miss_ratio=cache_miss_ratio,
                scraping_events_total=scraping_events_total,
                scraping_success_rate=scraping_success_rate,
            )

        except Exception as e:
            logger.error(f"Failed to collect application metrics: {e}")
            return ApplicationMetrics(
                total_events=0,
                active_events=0,
                total_users=0,
                active_users=0,
                api_requests_total=0,
                api_requests_per_minute=0.0,
                cache_hit_ratio=0.0,
                cache_miss_ratio=0.0,
                scraping_events_total=0,
                scraping_success_rate=0.0,
            )

    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect system-level metrics."""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)

            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage_bytes = memory.used
            memory_usage_percent = memory.percent

            # Disk usage
            disk_usage = {}
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.mountpoint] = (usage.used / usage.total) * 100
                except PermissionError:
                    continue

            # Network I/O (optional)
            network = psutil.net_io_counters()

            return {
                "cpu_usage_percent": cpu_usage,
                "memory_usage_bytes": memory_usage_bytes,
                "memory_usage_percent": memory_usage_percent,
                "disk_usage": disk_usage,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_received": network.bytes_recv,
            }

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}

    async def update_prometheus_metrics(self):
        """Update all Prometheus metrics."""
        if not self.enabled:
            return

        try:
            # Collect metrics
            db_metrics = await self.collect_database_metrics()
            app_metrics = await self.collect_application_metrics()
            sys_metrics = self.collect_system_metrics()

            # Update database metrics
            self.db_connections_active.set(db_metrics.active_connections)
            self.db_connections_idle.set(db_metrics.idle_connections)
            self.db_size_bytes.set(db_metrics.database_size_bytes)
            self.db_cache_hit_ratio.set(db_metrics.cache_hit_ratio)

            # Update application metrics
            self.events_total.labels(status="active").set(app_metrics.active_events)
            self.events_total.labels(status="total").set(app_metrics.total_events)
            self.users_total.labels(status="active").set(app_metrics.active_users)
            self.users_total.labels(status="total").set(app_metrics.total_users)

            # Update system metrics
            if "cpu_usage_percent" in sys_metrics:
                self.system_cpu_usage.set(sys_metrics["cpu_usage_percent"])

            if "memory_usage_bytes" in sys_metrics:
                self.system_memory_usage.set(sys_metrics["memory_usage_bytes"])

            if "disk_usage" in sys_metrics:
                for mount_point, usage_percent in sys_metrics["disk_usage"].items():
                    self.system_disk_usage.labels(mount_point=mount_point).set(
                        usage_percent
                    )

            self.last_collection_time = datetime.now()

            logger.debug("Prometheus metrics updated successfully")

        except Exception as e:
            logger.error(f"Failed to update Prometheus metrics: {e}")

    def get_metrics_data(self) -> str:
        """Get metrics data in Prometheus format."""
        return generate_latest(self.registry)

    def record_api_request(
        self, method: str, endpoint: str, status_code: int, duration: float
    ):
        """Record API request metrics."""
        if not self.enabled:
            return

        # Normalize endpoint to avoid high cardinality
        normalized_endpoint = self._normalize_endpoint(endpoint)

        self.api_requests_total.labels(
            method=method, endpoint=normalized_endpoint, status=str(status_code)
        ).inc()

        self.api_request_duration.labels(
            method=method, endpoint=normalized_endpoint
        ).observe(duration)

    def record_cache_operation(self, operation: str, result: str):
        """Record cache operation metrics."""
        if not self.enabled:
            return

        self.cache_operations.labels(operation=operation, result=result).inc()

    def record_scraping_event(self, source: str, status: str):
        """Record scraping event metrics."""
        if not self.enabled:
            return

        self.scraping_events.labels(source=source, status=status).inc()

    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint to reduce cardinality."""
        # Replace dynamic parts with placeholders
        import re

        # Replace UUIDs and IDs with placeholders
        endpoint = re.sub(r"/\d+", "/{id}", endpoint)
        endpoint = re.sub(r"/[a-f0-9-]{36}", "/{uuid}", endpoint)
        endpoint = re.sub(r"/[a-f0-9-]{32}", "/{hash}", endpoint)

        return endpoint

    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check metric thresholds and generate alerts."""
        alerts = []

        if not self.enabled:
            return alerts

        try:
            # Collect current metrics
            db_metrics = await self.collect_database_metrics()
            app_metrics = await self.collect_application_metrics()
            sys_metrics = self.collect_system_metrics()

            # Create metrics dictionary for easy access
            current_metrics = {
                "db_connections_active": db_metrics.active_connections,
                "db_cache_hit_ratio": db_metrics.cache_hit_ratio / 100.0,
                "system_cpu_usage": sys_metrics.get("cpu_usage_percent", 0),
                "system_memory_usage": sys_metrics.get("memory_usage_percent", 0),
                "db_deadlocks_rate": 0,  # Placeholder
                "api_request_duration_p95": 0.5,  # Placeholder
            }

            # Check each alert configuration
            for alert_config in self.alert_configs:
                if not alert_config.enabled:
                    continue

                metric_value = current_metrics.get(alert_config.metric_name)
                if metric_value is None:
                    continue

                # Check threshold
                threshold_exceeded = False

                if (
                    alert_config.comparison == "gt"
                    and metric_value > alert_config.threshold
                ):
                    threshold_exceeded = True
                elif (
                    alert_config.comparison == "lt"
                    and metric_value < alert_config.threshold
                ):
                    threshold_exceeded = True
                elif (
                    alert_config.comparison == "gte"
                    and metric_value >= alert_config.threshold
                ):
                    threshold_exceeded = True
                elif (
                    alert_config.comparison == "lte"
                    and metric_value <= alert_config.threshold
                ):
                    threshold_exceeded = True
                elif (
                    alert_config.comparison == "eq"
                    and metric_value == alert_config.threshold
                ):
                    threshold_exceeded = True

                if threshold_exceeded:
                    alert = {
                        "metric_name": alert_config.metric_name,
                        "current_value": metric_value,
                        "threshold": alert_config.threshold,
                        "severity": alert_config.severity.value,
                        "message": alert_config.message.format(value=metric_value),
                        "timestamp": datetime.now().isoformat(),
                        "comparison": alert_config.comparison,
                    }
                    alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Failed to check alerts: {e}")
            return []

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            db_metrics = await self.collect_database_metrics()
            app_metrics = await self.collect_application_metrics()
            sys_metrics = self.collect_system_metrics()
            alerts = await self.check_alerts()

            # Determine overall health
            critical_alerts = [a for a in alerts if a["severity"] == "critical"]
            warning_alerts = [a for a in alerts if a["severity"] == "warning"]

            if critical_alerts:
                overall_status = "critical"
            elif warning_alerts:
                overall_status = "warning"
            else:
                overall_status = "healthy"

            return {
                "status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "active_connections": db_metrics.active_connections,
                    "cache_hit_ratio": db_metrics.cache_hit_ratio,
                    "database_size_mb": round(
                        db_metrics.database_size_bytes / 1024 / 1024, 2
                    ),
                    "slow_queries": db_metrics.slow_queries,
                },
                "application": {
                    "total_events": app_metrics.total_events,
                    "active_events": app_metrics.active_events,
                    "total_users": app_metrics.total_users,
                    "active_users": app_metrics.active_users,
                },
                "system": {
                    "cpu_usage_percent": sys_metrics.get("cpu_usage_percent", 0),
                    "memory_usage_percent": sys_metrics.get("memory_usage_percent", 0),
                    "disk_usage": sys_metrics.get("disk_usage", {}),
                },
                "alerts": {
                    "critical": len(critical_alerts),
                    "warning": len(warning_alerts),
                    "total": len(alerts),
                    "details": alerts,
                },
                "monitoring": {
                    "enabled": self.enabled,
                    "last_collection": self.last_collection_time.isoformat(),
                    "collection_interval": self.collection_interval,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get health status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }


# Global monitoring instance
monitoring_service = PrometheusMonitoring()


def get_monitoring_service() -> PrometheusMonitoring:
    """Get monitoring service instance."""
    return monitoring_service


# Decorator for automatic API request monitoring
def monitor_api_request(func: Callable) -> Callable:
    """Decorator to automatically monitor API requests."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        method = "GET"  # Default, would be extracted from request
        endpoint = func.__name__
        status_code = 200

        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            status_code = 500
            raise
        finally:
            duration = time.time() - start_time
            monitoring_service.record_api_request(
                method, endpoint, status_code, duration
            )

    return wrapper


# Decorator for cache operation monitoring
def monitor_cache_operation(operation: str):
    """Decorator to monitor cache operations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                monitoring_service.record_cache_operation(
                    operation, "hit" if result else "miss"
                )
                return result
            except Exception as e:
                monitoring_service.record_cache_operation(operation, "error")
                raise

        return wrapper

    return decorator
