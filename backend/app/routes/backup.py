"""
Backup management API endpoints.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..core.backup import get_backup_service, BackupType
from ..core.auth import get_current_superuser
from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["backup"])


@router.post("/create-full", dependencies=[Depends(get_current_superuser)])
async def create_full_backup(
    background_tasks: BackgroundTasks,
    include_analytics: bool = True,
    custom_filename: Optional[str] = None
) -> Dict[str, Any]:
    """Create a full database backup."""
    try:
        backup_service = get_backup_service()
        
        # Run backup in background
        background_tasks.add_task(
            backup_service.create_full_backup,
            custom_filename=custom_filename,
            include_analytics=include_analytics
        )
        
        return {
            "status": "started",
            "message": "Full backup initiated",
            "backup_type": "full",
            "include_analytics": include_analytics,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to initiate full backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate backup: {str(e)}"
        )


@router.post("/create-schema", dependencies=[Depends(get_current_superuser)])
async def create_schema_backup(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Create a schema-only backup."""
    try:
        backup_service = get_backup_service()
        
        # Run backup in background
        background_tasks.add_task(backup_service.create_schema_backup)
        
        return {
            "status": "started",
            "message": "Schema backup initiated",
            "backup_type": "schema_only",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to initiate schema backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate backup: {str(e)}"
        )


@router.get("/list")
async def list_backups(current_user: User = Depends(get_current_superuser)) -> List[Dict[str, Any]]:
    """List all available backups."""
    try:
        backup_service = get_backup_service()
        backups = backup_service.list_backups()
        
        return backups
    
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.get("/status")
async def get_backup_status(current_user: User = Depends(get_current_superuser)) -> Dict[str, Any]:
    """Get backup system status and statistics."""
    try:
        backup_service = get_backup_service()
        status_info = backup_service.get_backup_status()
        
        return status_info
    
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup status: {str(e)}"
        )


@router.post("/verify/{backup_id}")
async def verify_backup(
    backup_id: str,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Verify backup file integrity."""
    try:
        backup_service = get_backup_service()
        
        # Find backup by ID
        backups = backup_service.list_backups()
        backup_file = None
        
        for backup in backups:
            if backup.get("backup_id") == backup_id:
                backup_file = backup.get("file_path")
                break
        
        if not backup_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}"
            )
        
        verification_result = backup_service.verify_backup(backup_file)
        
        return verification_result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify backup {backup_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify backup: {str(e)}"
        )


@router.post("/restore")
async def restore_from_backup(
    backup_id: str,
    target_database: Optional[str] = None,
    drop_existing: bool = False,
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_superuser)
) -> Dict[str, Any]:
    """Restore database from backup."""
    try:
        backup_service = get_backup_service()
        
        # Find backup by ID
        backups = backup_service.list_backups()
        backup_file = None
        
        for backup in backups:
            if backup.get("backup_id") == backup_id:
                backup_file = backup.get("file_path")
                break
        
        if not backup_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}"
            )
        
        # Run restore in background if background_tasks is available
        if background_tasks:
            background_tasks.add_task(
                backup_service.restore_from_backup,
                backup_path=backup_file,
                target_database=target_database,
                drop_existing=drop_existing
            )
            
            return {
                "status": "started",
                "message": "Database restore initiated",
                "backup_id": backup_id,
                "target_database": target_database or backup_service.db_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Synchronous restore (use with caution)
            result = backup_service.restore_from_backup(
                backup_path=backup_file,
                target_database=target_database,
                drop_existing=drop_existing
            )
            
            return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore from backup {backup_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore from backup: {str(e)}"
        )


@router.post("/cleanup", dependencies=[Depends(get_current_superuser)])
async def cleanup_old_backups(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Clean up old backup files based on retention policy."""
    try:
        backup_service = get_backup_service()
        
        # Run cleanup in background
        background_tasks.add_task(backup_service.cleanup_old_backups)
        
        return {
            "status": "started",
            "message": "Backup cleanup initiated",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to initiate backup cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate cleanup: {str(e)}"
        )


@router.delete("/{backup_id}", dependencies=[Depends(get_current_superuser)])
async def delete_backup(backup_id: str) -> Dict[str, Any]:
    """Delete a specific backup file."""
    try:
        backup_service = get_backup_service()
        
        # Find backup by ID
        backups = backup_service.list_backups()
        backup_file = None
        
        for backup in backups:
            if backup.get("backup_id") == backup_id:
                backup_file = backup.get("file_path")
                break
        
        if not backup_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup not found: {backup_id}"
            )
        
        # Delete backup file and metadata
        from pathlib import Path
        backup_path = Path(backup_file)
        metadata_file = backup_service.backup_dir / "logs" / f"{backup_id}.json"
        
        if backup_path.exists():
            backup_path.unlink()
        
        if metadata_file.exists():
            metadata_file.unlink()
        
        logger.info(f"Deleted backup: {backup_id}")
        
        return {
            "status": "success",
            "message": f"Backup {backup_id} deleted successfully",
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete backup {backup_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )


# Health check for backup system
@router.get("/health")
async def backup_health_check() -> Dict[str, Any]:
    """Check backup system health."""
    try:
        backup_service = get_backup_service()
        
        # Basic health checks
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "backup_directory_accessible": backup_service.backup_dir.exists(),
            "temp_directory_accessible": backup_service.temp_dir.exists(),
            "s3_enabled": backup_service.s3_enabled,
            "compression_enabled": backup_service.compression_enabled
        }
        
        # Check S3 connectivity if enabled
        if backup_service.s3_enabled and backup_service.s3_client:
            try:
                backup_service.s3_client.head_bucket(Bucket=backup_service.s3_bucket)
                health_status["s3_accessible"] = True
            except Exception:
                health_status["s3_accessible"] = False
                health_status["status"] = "degraded"
        
        return health_status
    
    except Exception as e:
        logger.error(f"Backup health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }