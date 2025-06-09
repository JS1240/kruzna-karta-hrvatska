"""
Database and application monitoring API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Response, status
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..core.monitoring import get_monitoring_service, PrometheusMonitoring
from ..core.auth import get_current_superuser
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """Get comprehensive system health status."""
    try:
        monitoring_service = get_monitoring_service()
        health_status = await monitoring_service.get_health_status()
        
        return health_status
    
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health status: {str(e)}"
        )


@router.get("/metrics")
async def get_prometheus_metrics(response: Response):
    """Get metrics in Prometheus format."""
    try:
        monitoring_service = get_monitoring_service()
        
        # Update metrics before returning
        await monitoring_service.update_prometheus_metrics()
        
        # Get metrics data
        metrics_data = monitoring_service.get_metrics_data()
        
        # Set correct content type for Prometheus
        response.headers["Content-Type"] = "text/plain; version=0.0.4; charset=utf-8"
        
        return Response(content=metrics_data, media_type="text/plain")
    
    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}"
        )


@router.get("/database")
async def get_database_metrics(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get detailed database metrics."""
    try:
        monitoring_service = get_monitoring_service()
        db_metrics = await monitoring_service.get_cached_database_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "database_metrics": {
                "connections": {
                    "active": db_metrics.active_connections,
                    "idle": db_metrics.idle_connections,
                    "total": db_metrics.total_connections
                },
                "performance": {
                    "cache_hit_ratio": db_metrics.cache_hit_ratio,
                    "total_queries": db_metrics.total_queries,
                    "slow_queries": db_metrics.slow_queries,
                    "locks_waiting": db_metrics.locks_waiting
                },
                "storage": {
                    "database_size_bytes": db_metrics.database_size_bytes,
                    "database_size_mb": round(db_metrics.database_size_bytes / 1024 / 1024, 2),
                    "temp_files": db_metrics.temp_files,
                    "temp_bytes": db_metrics.temp_bytes
                },
                "checkpoints": {
                    "checkpoints_timed": db_metrics.checkpoints_timed,
                    "checkpoints_requested": db_metrics.checkpoints_requested,
                    "buffers_checkpoint": db_metrics.buffers_checkpoint,
                    "buffers_clean": db_metrics.buffers_clean,
                    "buffers_backend": db_metrics.buffers_backend
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database metrics: {str(e)}"
        )


@router.get("/application")
async def get_application_metrics(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get detailed application metrics."""
    try:
        monitoring_service = get_monitoring_service()
        app_metrics = await monitoring_service.collect_application_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "application_metrics": {
                "events": {
                    "total": app_metrics.total_events,
                    "active": app_metrics.active_events,
                    "inactive": app_metrics.total_events - app_metrics.active_events
                },
                "users": {
                    "total": app_metrics.total_users,
                    "active": app_metrics.active_users,
                    "inactive": app_metrics.total_users - app_metrics.active_users
                },
                "api": {
                    "requests_total": app_metrics.api_requests_total,
                    "requests_per_minute": app_metrics.api_requests_per_minute
                },
                "cache": {
                    "hit_ratio": app_metrics.cache_hit_ratio,
                    "miss_ratio": app_metrics.cache_miss_ratio
                },
                "scraping": {
                    "events_total": app_metrics.scraping_events_total,
                    "success_rate": app_metrics.scraping_success_rate
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get application metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get application metrics: {str(e)}"
        )


@router.get("/system")
async def get_system_metrics(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get detailed system metrics."""
    try:
        monitoring_service = get_monitoring_service()
        sys_metrics = monitoring_service.collect_system_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system_metrics": {
                "cpu": {
                    "usage_percent": sys_metrics.get('cpu_usage_percent', 0)
                },
                "memory": {
                    "usage_bytes": sys_metrics.get('memory_usage_bytes', 0),
                    "usage_mb": round(sys_metrics.get('memory_usage_bytes', 0) / 1024 / 1024, 2),
                    "usage_percent": sys_metrics.get('memory_usage_percent', 0)
                },
                "disk": {
                    "usage_by_mount": sys_metrics.get('disk_usage', {})
                },
                "network": {
                    "bytes_sent": sys_metrics.get('network_bytes_sent', 0),
                    "bytes_received": sys_metrics.get('network_bytes_received', 0)
                }
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system metrics: {str(e)}"
        )


@router.get("/alerts")
async def get_active_alerts(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get active alerts based on metric thresholds."""
    try:
        monitoring_service = get_monitoring_service()
        alerts = await monitoring_service.check_alerts()
        
        # Group alerts by severity
        critical_alerts = [a for a in alerts if a['severity'] == 'critical']
        warning_alerts = [a for a in alerts if a['severity'] == 'warning']
        info_alerts = [a for a in alerts if a['severity'] == 'info']
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts_summary": {
                "total": len(alerts),
                "critical": len(critical_alerts),
                "warning": len(warning_alerts),
                "info": len(info_alerts)
            },
            "alerts": {
                "critical": critical_alerts,
                "warning": warning_alerts,
                "info": info_alerts
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.post("/alerts/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Acknowledge a specific alert."""
    try:
        # In a real implementation, you would update alert status in a database
        # For now, we'll just return a success response
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} acknowledged",
            "acknowledged_by": current_user.email,
            "acknowledged_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to acknowledge alert: {str(e)}"
        )


@router.post("/metrics/update")
async def update_metrics(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Manually trigger metrics collection update."""
    try:
        monitoring_service = get_monitoring_service()
        await monitoring_service.update_prometheus_metrics()
        
        return {
            "status": "success",
            "message": "Metrics updated successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to update metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update metrics: {str(e)}"
        )


@router.get("/dashboard")
async def get_monitoring_dashboard(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    try:
        monitoring_service = get_monitoring_service()
        
        # Collect all metrics
        health_status = await monitoring_service.get_health_status()
        alerts = await monitoring_service.check_alerts()
        
        # Create dashboard summary
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": health_status["status"],
            "summary": {
                "database": {
                    "status": "healthy" if health_status["database"]["cache_hit_ratio"] > 90 else "warning",
                    "active_connections": health_status["database"]["active_connections"],
                    "cache_hit_ratio": health_status["database"]["cache_hit_ratio"],
                    "database_size_mb": health_status["database"]["database_size_mb"]
                },
                "application": {
                    "total_events": health_status["application"]["total_events"],
                    "active_events": health_status["application"]["active_events"],
                    "total_users": health_status["application"]["total_users"],
                    "active_users": health_status["application"]["active_users"]
                },
                "system": {
                    "cpu_usage": health_status["system"]["cpu_usage_percent"],
                    "memory_usage": health_status["system"]["memory_usage_percent"],
                    "status": "healthy" if health_status["system"]["cpu_usage_percent"] < 80 else "warning"
                },
                "alerts": {
                    "total": len(alerts),
                    "critical": len([a for a in alerts if a['severity'] == 'critical']),
                    "warning": len([a for a in alerts if a['severity'] == 'warning'])
                }
            },
            "quick_stats": {
                "uptime": "N/A",  # Would be calculated from application start time
                "requests_today": 0,  # Would be calculated from logs/metrics
                "errors_today": 0,    # Would be calculated from logs/metrics
                "avg_response_time": 0.0  # Would be calculated from metrics
            },
            "recent_alerts": alerts[:5]  # Last 5 alerts
        }
        
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}"
        )


@router.get("/config")
async def get_monitoring_config(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get monitoring system configuration."""
    try:
        monitoring_service = get_monitoring_service()
        
        return {
            "monitoring": {
                "enabled": monitoring_service.enabled,
                "collection_interval": monitoring_service.collection_interval,
                "last_collection": monitoring_service.last_collection_time.isoformat()
            },
            "alerts": {
                "total_configured": len(monitoring_service.alert_configs),
                "enabled_alerts": len([a for a in monitoring_service.alert_configs if a.enabled]),
                "alert_configs": [
                    {
                        "metric_name": alert.metric_name,
                        "threshold": alert.threshold,
                        "comparison": alert.comparison,
                        "severity": alert.severity.value,
                        "enabled": alert.enabled
                    }
                    for alert in monitoring_service.alert_configs
                ]
            },
            "prometheus": {
                "metrics_endpoint": "/api/monitoring/metrics",
                "metrics_count": len(monitoring_service.registry._collector_to_names)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get monitoring config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring config: {str(e)}"
        )


@router.post("/config/alerts/{metric_name}/toggle")
async def toggle_alert(
    metric_name: str,
    enabled: bool,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Enable or disable a specific alert."""
    try:
        monitoring_service = get_monitoring_service()
        
        # Find and update alert configuration
        alert_found = False
        for alert_config in monitoring_service.alert_configs:
            if alert_config.metric_name == metric_name:
                alert_config.enabled = enabled
                alert_found = True
                break
        
        if not alert_found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert configuration not found: {metric_name}"
            )
        
        return {
            "status": "success",
            "message": f"Alert {metric_name} {'enabled' if enabled else 'disabled'}",
            "metric_name": metric_name,
            "enabled": enabled,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle alert {metric_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle alert: {str(e)}"
        )