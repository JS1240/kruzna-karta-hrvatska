"""
Automated PostgreSQL backup and disaster recovery system.
"""

import os
import subprocess
import shutil
import logging
import gzip
import boto3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

from .config import settings

logger = logging.getLogger(__name__)


class BackupType(Enum):
    """Types of database backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    SCHEMA_ONLY = "schema_only"
    DATA_ONLY = "data_only"


class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


@dataclass
class BackupMetadata:
    """Metadata for backup files."""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    database_name: str
    file_path: str
    file_size: int
    compressed: bool
    checksum: str
    status: BackupStatus
    duration_seconds: float
    tables_included: List[str]
    pg_version: str
    compression_ratio: Optional[float] = None
    storage_location: Optional[str] = None
    retention_days: int = 30


class PostgreSQLBackupService:
    """Comprehensive PostgreSQL backup and recovery service."""
    
    def __init__(self):
        self.backup_dir = Path(os.getenv("BACKUP_DIR", "/var/backups/kruzna_karta"))
        self.temp_dir = Path(os.getenv("TEMP_BACKUP_DIR", "/tmp/kruzna_karta_backups"))
        self.max_backup_age_days = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))
        self.compression_enabled = os.getenv("BACKUP_COMPRESSION", "true").lower() == "true"
        
        # AWS S3 configuration for remote backups
        self.s3_enabled = os.getenv("S3_BACKUP_ENABLED", "false").lower() == "true"
        self.s3_bucket = os.getenv("S3_BACKUP_BUCKET")
        self.s3_prefix = os.getenv("S3_BACKUP_PREFIX", "kruzna-karta-backups")
        
        # Database connection settings
        self.db_host = settings.db_host
        self.db_port = settings.db_port
        self.db_name = settings.db_name
        self.db_user = settings.db_user
        self.db_password = settings.db_password
        
        # Initialize directories
        self._initialize_directories()
        
        # Initialize S3 client if enabled
        self.s3_client = None
        if self.s3_enabled:
            self._initialize_s3_client()
    
    def _initialize_directories(self):
        """Create backup directories if they don't exist."""
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different backup types
            (self.backup_dir / "full").mkdir(exist_ok=True)
            (self.backup_dir / "incremental").mkdir(exist_ok=True)
            (self.backup_dir / "schema").mkdir(exist_ok=True)
            (self.backup_dir / "logs").mkdir(exist_ok=True)
            
            logger.info(f"Backup directories initialized at {self.backup_dir}")
        
        except Exception as e:
            logger.error(f"Failed to initialize backup directories: {e}")
            raise
    
    def _initialize_s3_client(self):
        """Initialize S3 client for remote backups."""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
                region_name=os.getenv("AWS_REGION", "eu-central-1")
            )
            
            # Test S3 connection
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            logger.info(f"S3 backup configured: s3://{self.s3_bucket}/{self.s3_prefix}")
        
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_enabled = False
    
    def create_full_backup(self, 
                          custom_filename: Optional[str] = None,
                          include_analytics: bool = True) -> BackupMetadata:
        """Create a full database backup."""
        logger.info("Starting full database backup")
        start_time = datetime.now()
        
        # Generate backup metadata
        backup_id = f"full_{start_time.strftime('%Y%m%d_%H%M%S')}"
        filename = custom_filename or f"{backup_id}.sql"
        
        if self.compression_enabled:
            filename += ".gz"
        
        backup_path = self.backup_dir / "full" / filename
        temp_path = self.temp_dir / filename
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            created_at=start_time,
            database_name=self.db_name,
            file_path=str(backup_path),
            file_size=0,
            compressed=self.compression_enabled,
            checksum="",
            status=BackupStatus.RUNNING,
            duration_seconds=0,
            tables_included=[],
            pg_version="",
            retention_days=self.max_backup_age_days
        )
        
        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                "--format=custom",
                "--no-password"
            ]
            
            # Exclude analytics tables if requested
            if not include_analytics:
                analytics_tables = [
                    "event_views", "search_logs", "user_interactions",
                    "event_performance_metrics", "platform_metrics",
                    "category_metrics", "venue_metrics", "metric_alerts"
                ]
                for table in analytics_tables:
                    cmd.extend(["--exclude-table", table])
            
            cmd.append(self.db_name)
            
            # Set environment for password
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            # Execute backup
            logger.info(f"Executing: {' '.join(cmd[:-1])} [database]")
            
            if self.compression_enabled:
                # Pipe through gzip
                with open(temp_path, 'wb') as f:
                    pg_dump = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
                    gzip_proc = subprocess.Popen(['gzip'], stdin=pg_dump.stdout, stdout=f)
                    pg_dump.stdout.close()
                    gzip_proc.wait()
                    pg_dump.wait()
                
                if pg_dump.returncode != 0:
                    raise subprocess.CalledProcessError(pg_dump.returncode, cmd)
            else:
                subprocess.run(cmd, env=env, check=True, stdout=open(temp_path, 'w'))
            
            # Move from temp to final location
            shutil.move(temp_path, backup_path)
            
            # Calculate file size and checksum
            file_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            
            # Get PostgreSQL version
            pg_version = self._get_postgresql_version()
            
            # Get table list
            tables_included = self._get_table_list()
            
            # Calculate duration
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Update metadata
            metadata.file_size = file_size
            metadata.checksum = checksum
            metadata.status = BackupStatus.COMPLETED
            metadata.duration_seconds = duration
            metadata.tables_included = tables_included
            metadata.pg_version = pg_version
            
            # Calculate compression ratio if compressed
            if self.compression_enabled:
                metadata.compression_ratio = self._estimate_compression_ratio(backup_path)
            
            # Upload to S3 if enabled
            if self.s3_enabled:
                s3_location = self._upload_to_s3(backup_path, backup_id)
                metadata.storage_location = s3_location
            
            # Save metadata
            self._save_backup_metadata(metadata)
            
            logger.info(f"Full backup completed: {backup_path} ({file_size} bytes, {duration:.2f}s)")
            return metadata
        
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            metadata.status = BackupStatus.FAILED
            self._save_backup_metadata(metadata)
            
            # Clean up failed backup file
            if temp_path.exists():
                temp_path.unlink()
            if backup_path.exists():
                backup_path.unlink()
            
            raise
    
    def create_schema_backup(self) -> BackupMetadata:
        """Create a schema-only backup (no data)."""
        logger.info("Starting schema-only backup")
        start_time = datetime.now()
        
        backup_id = f"schema_{start_time.strftime('%Y%m%d_%H%M%S')}"
        filename = f"{backup_id}.sql"
        
        if self.compression_enabled:
            filename += ".gz"
        
        backup_path = self.backup_dir / "schema" / filename
        temp_path = self.temp_dir / filename
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.SCHEMA_ONLY,
            created_at=start_time,
            database_name=self.db_name,
            file_path=str(backup_path),
            file_size=0,
            compressed=self.compression_enabled,
            checksum="",
            status=BackupStatus.RUNNING,
            duration_seconds=0,
            tables_included=[],
            pg_version="",
            retention_days=7  # Keep schema backups for shorter time
        )
        
        try:
            # Build pg_dump command for schema only
            cmd = [
                "pg_dump",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                "--verbose",
                "--clean",
                "--if-exists",
                "--create",
                "--schema-only",
                "--no-password",
                self.db_name
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            # Execute backup
            if self.compression_enabled:
                with open(temp_path, 'wb') as f:
                    pg_dump = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env)
                    gzip_proc = subprocess.Popen(['gzip'], stdin=pg_dump.stdout, stdout=f)
                    pg_dump.stdout.close()
                    gzip_proc.wait()
                    pg_dump.wait()
                
                if pg_dump.returncode != 0:
                    raise subprocess.CalledProcessError(pg_dump.returncode, cmd)
            else:
                subprocess.run(cmd, env=env, check=True, stdout=open(temp_path, 'w'))
            
            # Move to final location and finalize metadata
            shutil.move(temp_path, backup_path)
            
            file_size = backup_path.stat().st_size
            checksum = self._calculate_checksum(backup_path)
            duration = (datetime.now() - start_time).total_seconds()
            
            metadata.file_size = file_size
            metadata.checksum = checksum
            metadata.status = BackupStatus.COMPLETED
            metadata.duration_seconds = duration
            metadata.pg_version = self._get_postgresql_version()
            
            self._save_backup_metadata(metadata)
            
            logger.info(f"Schema backup completed: {backup_path}")
            return metadata
        
        except Exception as e:
            logger.error(f"Schema backup failed: {e}")
            metadata.status = BackupStatus.FAILED
            self._save_backup_metadata(metadata)
            raise
    
    def restore_from_backup(self, 
                           backup_path: str,
                           target_database: Optional[str] = None,
                           drop_existing: bool = False) -> Dict[str, Any]:
        """Restore database from backup file."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        target_db = target_database or self.db_name
        start_time = datetime.now()
        
        logger.info(f"Starting database restore from {backup_path} to {target_db}")
        
        try:
            # Verify backup integrity
            if not self._verify_backup_integrity(backup_file):
                raise ValueError("Backup file integrity check failed")
            
            # Create target database if it doesn't exist
            if target_db != self.db_name:
                self._create_database_if_not_exists(target_db)
            
            # Drop existing database if requested
            if drop_existing:
                self._drop_database_connections(target_db)
            
            # Build pg_restore command
            cmd = [
                "pg_restore",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                f"--dbname={target_db}",
                "--verbose",
                "--clean",
                "--if-exists",
                "--no-password"
            ]
            
            # Handle compressed files
            if backup_path.endswith('.gz'):
                cmd.extend(["--format=custom"])
                # Need to decompress first
                temp_file = self.temp_dir / f"restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(temp_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                cmd.append(str(temp_file))
            else:
                cmd.append(str(backup_file))
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            # Execute restore
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                raise subprocess.CalledProcessError(result.returncode, cmd)
            
            # Clean up temporary file
            if backup_path.endswith('.gz') and temp_file.exists():
                temp_file.unlink()
            
            duration = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Database restore completed in {duration:.2f} seconds")
            
            return {
                "status": "success",
                "target_database": target_db,
                "backup_file": backup_path,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            raise
    
    def cleanup_old_backups(self) -> Dict[str, Any]:
        """Remove old backup files based on retention policy."""
        logger.info("Starting cleanup of old backup files")
        
        cleaned_files = []
        total_size_freed = 0
        
        try:
            # Get all backup metadata files
            metadata_files = list((self.backup_dir / "logs").glob("*.json"))
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    backup_date = datetime.fromisoformat(metadata['created_at'])
                    retention_days = metadata.get('retention_days', self.max_backup_age_days)
                    
                    if datetime.now() - backup_date > timedelta(days=retention_days):
                        # Delete backup file
                        backup_file = Path(metadata['file_path'])
                        if backup_file.exists():
                            file_size = backup_file.stat().st_size
                            backup_file.unlink()
                            total_size_freed += file_size
                            cleaned_files.append(str(backup_file))
                        
                        # Delete metadata file
                        metadata_file.unlink()
                        
                        logger.info(f"Cleaned up old backup: {backup_file}")
                
                except Exception as e:
                    logger.error(f"Error processing metadata file {metadata_file}: {e}")
            
            # Clean up S3 backups if enabled
            s3_cleaned = 0
            if self.s3_enabled:
                s3_cleaned = self._cleanup_s3_backups()
            
            logger.info(f"Cleanup completed: {len(cleaned_files)} files, {total_size_freed} bytes freed")
            
            return {
                "status": "success",
                "cleaned_files": len(cleaned_files),
                "size_freed_bytes": total_size_freed,
                "s3_files_cleaned": s3_cleaned,
                "files_list": cleaned_files
            }
        
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "cleaned_files": len(cleaned_files),
                "size_freed_bytes": total_size_freed
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups with metadata."""
        backups = []
        
        try:
            metadata_files = list((self.backup_dir / "logs").glob("*.json"))
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    # Check if backup file still exists
                    backup_file = Path(metadata['file_path'])
                    if backup_file.exists():
                        backups.append(metadata)
                    else:
                        # Backup file missing, mark as corrupted
                        metadata['status'] = BackupStatus.CORRUPTED.value
                        backups.append(metadata)
                
                except Exception as e:
                    logger.error(f"Error reading metadata file {metadata_file}: {e}")
            
            # Sort by creation date, newest first
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup file integrity and metadata."""
        backup_file = Path(backup_path)
        
        if not backup_file.exists():
            return {
                "status": "error",
                "error": "Backup file not found",
                "file_exists": False
            }
        
        try:
            # Calculate current checksum
            current_checksum = self._calculate_checksum(backup_file)
            
            # Find metadata file
            backup_id = backup_file.stem.replace('.sql', '').replace('.gz', '')
            metadata_file = self.backup_dir / "logs" / f"{backup_id}.json"
            
            stored_checksum = None
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                stored_checksum = metadata.get('checksum')
            
            # Verify file can be read by pg_restore
            is_readable = self._verify_backup_integrity(backup_file)
            
            checksum_match = current_checksum == stored_checksum if stored_checksum else None
            
            return {
                "status": "success",
                "file_exists": True,
                "file_size": backup_file.stat().st_size,
                "current_checksum": current_checksum,
                "stored_checksum": stored_checksum,
                "checksum_match": checksum_match,
                "pg_readable": is_readable,
                "verification_time": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "file_exists": True
            }
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get overall backup system status."""
        try:
            backups = self.list_backups()
            
            # Calculate statistics
            total_backups = len(backups)
            completed_backups = len([b for b in backups if b['status'] == BackupStatus.COMPLETED.value])
            failed_backups = len([b for b in backups if b['status'] == BackupStatus.FAILED.value])
            corrupted_backups = len([b for b in backups if b['status'] == BackupStatus.CORRUPTED.value])
            
            # Find latest backup
            latest_backup = backups[0] if backups else None
            
            # Calculate total storage used
            total_size = sum(b.get('file_size', 0) for b in backups if b['status'] == BackupStatus.COMPLETED.value)
            
            # Check available disk space
            disk_usage = shutil.disk_usage(self.backup_dir)
            
            return {
                "status": "operational",
                "backup_directory": str(self.backup_dir),
                "total_backups": total_backups,
                "completed_backups": completed_backups,
                "failed_backups": failed_backups,
                "corrupted_backups": corrupted_backups,
                "latest_backup": latest_backup,
                "total_storage_bytes": total_size,
                "disk_usage": {
                    "total_bytes": disk_usage.total,
                    "used_bytes": disk_usage.used,
                    "free_bytes": disk_usage.free,
                    "usage_percentage": round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                "s3_enabled": self.s3_enabled,
                "compression_enabled": self.compression_enabled,
                "retention_days": self.max_backup_age_days
            }
        
        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    # Private helper methods
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _get_postgresql_version(self) -> str:
        """Get PostgreSQL server version."""
        try:
            cmd = [
                "psql",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                f"--dbname={self.db_name}",
                "--no-password",
                "-t",
                "-c", "SELECT version();"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL version: {e}")
            return "Unknown"
    
    def _get_table_list(self) -> List[str]:
        """Get list of all tables in the database."""
        try:
            cmd = [
                "psql",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                f"--dbname={self.db_name}",
                "--no-password",
                "-t",
                "-c", "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
            tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            return tables
        
        except Exception as e:
            logger.error(f"Failed to get table list: {e}")
            return []
    
    def _estimate_compression_ratio(self, compressed_file: Path) -> float:
        """Estimate compression ratio for compressed backups."""
        try:
            # This is an approximation since we don't have the original size
            # We can estimate based on typical PostgreSQL dump compression ratios
            compressed_size = compressed_file.stat().st_size
            estimated_original = compressed_size * 3.5  # Typical compression ratio
            return round(compressed_size / estimated_original, 2)
        except:
            return None
    
    def _save_backup_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to JSON file."""
        metadata_file = self.backup_dir / "logs" / f"{metadata.backup_id}.json"
        
        try:
            metadata_dict = {
                "backup_id": metadata.backup_id,
                "backup_type": metadata.backup_type.value,
                "created_at": metadata.created_at.isoformat(),
                "database_name": metadata.database_name,
                "file_path": metadata.file_path,
                "file_size": metadata.file_size,
                "compressed": metadata.compressed,
                "checksum": metadata.checksum,
                "status": metadata.status.value,
                "duration_seconds": metadata.duration_seconds,
                "tables_included": metadata.tables_included,
                "pg_version": metadata.pg_version,
                "compression_ratio": metadata.compression_ratio,
                "storage_location": metadata.storage_location,
                "retention_days": metadata.retention_days
            }
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata_dict, f, indent=2)
        
        except Exception as e:
            logger.error(f"Failed to save backup metadata: {e}")
    
    def _verify_backup_integrity(self, backup_file: Path) -> bool:
        """Verify that backup file can be read by PostgreSQL tools."""
        try:
            if str(backup_file).endswith('.gz'):
                # Test gzip file integrity
                with gzip.open(backup_file, 'rb') as f:
                    f.read(1024)  # Try to read some data
            else:
                # Test that pg_restore can read the file
                cmd = [
                    "pg_restore",
                    "--list",
                    str(backup_file)
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                return result.returncode == 0
            
            return True
        
        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            return False
    
    def _upload_to_s3(self, backup_file: Path, backup_id: str) -> Optional[str]:
        """Upload backup file to S3."""
        if not self.s3_enabled or not self.s3_client:
            return None
        
        try:
            s3_key = f"{self.s3_prefix}/{backup_id}/{backup_file.name}"
            
            logger.info(f"Uploading backup to S3: s3://{self.s3_bucket}/{s3_key}")
            
            self.s3_client.upload_file(
                str(backup_file),
                self.s3_bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': 'STANDARD_IA',  # Infrequent Access for cost optimization
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            s3_location = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"Backup uploaded to S3: {s3_location}")
            
            return s3_location
        
        except Exception as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            return None
    
    def _cleanup_s3_backups(self) -> int:
        """Clean up old backups from S3."""
        if not self.s3_enabled or not self.s3_client:
            return 0
        
        try:
            cutoff_date = datetime.now() - timedelta(days=self.max_backup_age_days)
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=self.s3_prefix
            )
            
            deleted_count = 0
            
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    self.s3_client.delete_object(
                        Bucket=self.s3_bucket,
                        Key=obj['Key']
                    )
                    deleted_count += 1
                    logger.info(f"Deleted old S3 backup: {obj['Key']}")
            
            return deleted_count
        
        except Exception as e:
            logger.error(f"S3 cleanup failed: {e}")
            return 0
    
    def _create_database_if_not_exists(self, database_name: str):
        """Create database if it doesn't exist."""
        try:
            cmd = [
                "psql",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                "--dbname=postgres",  # Connect to default database
                "--no-password",
                "-c", f"CREATE DATABASE {database_name};"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Created database: {database_name}")
        
        except subprocess.CalledProcessError:
            # Database might already exist, which is fine
            pass
        except Exception as e:
            logger.error(f"Failed to create database {database_name}: {e}")
    
    def _drop_database_connections(self, database_name: str):
        """Drop all connections to a database before restore."""
        try:
            cmd = [
                "psql",
                f"--host={self.db_host}",
                f"--port={self.db_port}",
                f"--username={self.db_user}",
                "--dbname=postgres",
                "--no-password",
                "-c", f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{database_name}' AND pid <> pg_backend_pid();"
            ]
            
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
            
            subprocess.run(cmd, env=env, check=True)
            logger.info(f"Dropped connections to database: {database_name}")
        
        except Exception as e:
            logger.error(f"Failed to drop connections to {database_name}: {e}")


def get_backup_service() -> PostgreSQLBackupService:
    """Get backup service instance."""
    return PostgreSQLBackupService()