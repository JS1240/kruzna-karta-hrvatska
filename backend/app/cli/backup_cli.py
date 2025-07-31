#!/usr/bin/env python3
"""
Command line interface for database backup operations.
"""

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.backup import PostgreSQLBackupService

# Configure logging for CLI - ensure output is visible to user
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simple format for CLI output
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def create_backup_service() -> PostgreSQLBackupService:
    """Create and return a backup service instance with default configuration.
    
    Factory function that initializes the PostgreSQL backup service with
    configuration from environment variables and application settings.
    Provides a consistent way to create backup service instances across CLI commands.
    
    Returns:
        PostgreSQLBackupService: Configured backup service instance ready for use
        
    Note:
        Uses default configuration from settings including database connection,
        backup directory, S3 configuration, and retention policies.
    """
    return PostgreSQLBackupService()


def cmd_create_full_backup(args) -> int:
    """Create a full database backup with all data and optional analytics.
    
    Performs a complete backup of the database including all tables, data,
    and optionally analytics tables. Supports custom filenames and automatic
    S3 upload if configured. Displays detailed backup metadata and timing.
    
    Args:
        args: Parsed command line arguments containing:
            - filename: Optional custom backup filename
            - include_analytics: Whether to include analytics tables (default: True)
            
    Returns:
        int: Exit code (0 for success, 1 for failure)
        
    Note:
        Backup includes schema, data, indexes, and constraints. Analytics tables
        can be excluded with --no-analytics flag to reduce backup size and time.
        Automatically uploads to S3 if S3 configuration is available.
    """
    try:
        backup_service = create_backup_service()

        logger.info("Starting full backup...")
        logger.info(f"Include analytics: {args.include_analytics}")
        if args.filename:
            logger.info(f"Custom filename: {args.filename}")

        metadata = backup_service.create_full_backup(
            custom_filename=args.filename, include_analytics=args.include_analytics
        )

        logger.info("✓ Full backup completed successfully!")
        logger.info(f"  Backup ID: {metadata.backup_id}")
        logger.info(f"  File: {metadata.file_path}")
        logger.info(f"  Size: {metadata.file_size:,} bytes")
        logger.info(f"  Duration: {metadata.duration_seconds:.2f} seconds")
        logger.info(f"  Tables: {len(metadata.tables_included)}")

        if metadata.storage_location:
            logger.info(f"  S3 Location: {metadata.storage_location}")

        return 0

    except Exception as e:
        logger.error(f"✗ Full backup failed: {e}")
        return 1


def cmd_create_schema_backup(args) -> int:
    """Create a schema-only backup."""
    try:
        backup_service = create_backup_service()

        logger.info("Starting schema backup...")

        metadata = backup_service.create_schema_backup()

        logger.info("✓ Schema backup completed successfully!")
        logger.info(f"  Backup ID: {metadata.backup_id}")
        logger.info(f"  File: {metadata.file_path}")
        logger.info(f"  Size: {metadata.file_size:,} bytes")
        logger.info(f"  Duration: {metadata.duration_seconds:.2f} seconds")

        return 0

    except Exception as e:
        logger.error(f"✗ Schema backup failed: {e}")
        return 1


def cmd_list_backups(args) -> int:
    """List all available backups with detailed information.
    
    Displays a comprehensive list of all backups including metadata such as
    backup type, creation time, file size, status, and storage location.
    Useful for backup management and selecting backups for restore operations.
    
    Args:
        args: Parsed command line arguments (no arguments used for this command)
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
        
    Note:
        Shows both local and S3-stored backups if S3 is configured. Displays
        human-readable file sizes and formatted creation timestamps for easy reading.
    """
    try:
        backup_service = create_backup_service()
        backups = backup_service.list_backups()

        if not backups:
            logger.info("No backups found.")
            return 0

        logger.info(f"\nFound {len(backups)} backup(s):\n")

        for backup in backups:
            created_at = datetime.fromisoformat(backup["created_at"])
            size_mb = backup["file_size"] / 1024 / 1024

            logger.info(f"ID: {backup['backup_id']}")
            logger.info(f"  Type: {backup['backup_type']}")
            logger.info(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  Size: {size_mb:.1f} MB")
            logger.info(f"  Status: {backup['status']}")
            logger.info(f"  File: {backup['file_path']}")

            if backup.get("storage_location"):
                logger.info(f"  S3: {backup['storage_location']}")

            logger.info()

        return 0

    except Exception as e:
        logger.error(f"✗ Failed to list backups: {e}")
        return 1


def cmd_verify_backup(args) -> int:
    """Verify backup integrity."""
    try:
        backup_service = create_backup_service()

        logger.info(f"Verifying backup: {args.backup_path}")

        result = backup_service.verify_backup(args.backup_path)

        if result["status"] == "success":
            logger.info("✓ Backup verification successful!")
            logger.info(f"  File exists: {result['file_exists']}")
            logger.info(f"  File size: {result['file_size']:,} bytes")
            logger.info(f"  PostgreSQL readable: {result['pg_readable']}")

            if result["checksum_match"] is not None:
                logger.info(f"  Checksum match: {result['checksum_match']}")
                logger.info(f"  Current checksum: {result['current_checksum']}")
        else:
            logger.error(f"✗ Backup verification failed: {result['error']}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"✗ Backup verification failed: {e}")
        return 1


def cmd_restore_backup(args) -> int:
    """Restore from backup."""
    try:
        backup_service = create_backup_service()

        logger.info(f"Restoring from backup: {args.backup_path}")
        if args.target_database:
            logger.info(f"Target database: {args.target_database}")
        logger.info(f"Drop existing: {args.drop_existing}")

        # Confirmation prompt
        if not args.yes:
            response = input(
                "Are you sure you want to proceed? This will modify the database. (y/N): "
            )
            if response.lower() != "y":
                logger.info("Restore cancelled.")
                return 0

        result = backup_service.restore_from_backup(
            backup_path=args.backup_path,
            target_database=args.target_database,
            drop_existing=args.drop_existing,
        )

        logger.info("✓ Database restore completed successfully!")
        logger.info(f"  Target database: {result['target_database']}")
        logger.info(f"  Duration: {result['duration_seconds']:.2f} seconds")

        return 0

    except Exception as e:
        logger.error(f"✗ Database restore failed: {e}")
        return 1


def cmd_cleanup_backups(args) -> int:
    """Clean up old backups."""
    try:
        backup_service = create_backup_service()

        logger.info("Cleaning up old backups...")

        # Confirmation prompt
        if not args.yes:
            response = input(
                f"This will delete backups older than {backup_service.max_backup_age_days} days. Continue? (y/N): "
            )
            if response.lower() != "y":
                logger.info("Cleanup cancelled.")
                return 0

        result = backup_service.cleanup_old_backups()

        if result["status"] == "success":
            logger.info("✓ Backup cleanup completed successfully!")
            logger.info(f"  Files cleaned: {result['cleaned_files']}")
            logger.info(f"  Space freed: {result['size_freed_bytes']:,} bytes")

            if result.get("s3_files_cleaned"):
                logger.info(f"  S3 files cleaned: {result['s3_files_cleaned']}")
        else:
            logger.error(f"✗ Backup cleanup failed: {result['error']}")
            return 1

        return 0

    except Exception as e:
        logger.error(f"✗ Backup cleanup failed: {e}")
        return 1


def cmd_status(args) -> int:
    """Show comprehensive backup system status and health information.
    
    Displays detailed information about the backup system including configuration,
    statistics, latest backup information, and disk usage. Essential for monitoring
    backup system health and troubleshooting issues.
    
    Args:
        args: Parsed command line arguments (no arguments used for this command)
        
    Returns:
        int: Exit code (0 for success, 1 for failure)
        
    Note:
        Status includes backup counts by status, storage usage, S3 configuration,
        retention settings, and disk space information for capacity planning.
    """
    try:
        backup_service = create_backup_service()
        status = backup_service.get_backup_status()

        logger.info("Backup System Status")
        logger.info("=" * 50)
        logger.info(f"Status: {status['status']}")
        logger.info(f"Backup Directory: {status['backup_directory']}")
        logger.info(f"Total Backups: {status['total_backups']}")
        logger.info(f"Completed: {status['completed_backups']}")
        logger.error(f"Failed: {status['failed_backups']}")
        logger.info(f"Corrupted: {status['corrupted_backups']}")
        logger.info(f"Total Storage: {status['total_storage_bytes']:,} bytes")
        logger.info(f"S3 Enabled: {status['s3_enabled']}")
        logger.info(f"Compression: {status['compression_enabled']}")
        logger.info(f"Retention Days: {status['retention_days']}")

        if status.get("latest_backup"):
            latest = status["latest_backup"]
            created_at = datetime.fromisoformat(latest["created_at"])
            logger.info("\nLatest Backup:")
            logger.info(f"  ID: {latest['backup_id']}")
            logger.info(f"  Type: {latest['backup_type']}")
            logger.info(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"  Status: {latest['status']}")

        # Disk usage
        disk = status["disk_usage"]
        logger.info("\nDisk Usage:")
        logger.info(f"  Total: {disk['total_bytes']:,} bytes")
        logger.info(f"  Used: {disk['used_bytes']:,} bytes")
        logger.info(f"  Free: {disk['free_bytes']:,} bytes")
        logger.info(f"  Usage: {disk['usage_percentage']:.1f}%")

        return 0

    except Exception as e:
        logger.error(f"✗ Failed to get backup status: {e}")
        return 1


def main() -> None:
    """Main CLI entry point with command parsing and execution.
    
    Parses command line arguments and routes to appropriate backup command functions.
    Provides a comprehensive command-line interface for all backup operations
    including creation, listing, verification, restoration, and system status.
    
    Returns:
        int: Exit code from executed command (0 for success, 1 for failure)
        
    Note:
        Available commands:
        - full: Create full database backup with optional analytics
        - schema: Create schema-only backup (no data)
        - list: List all available backups
        - verify: Verify backup file integrity
        - restore: Restore database from backup file
        - cleanup: Clean up old backups according to retention policy
        - status: Show backup system status and statistics
    """
    parser = argparse.ArgumentParser(
        description="Kruzna Karta Hrvatska Database Backup CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Full backup command
    parser_full = subparsers.add_parser("full", help="Create full database backup")
    parser_full.add_argument("--filename", help="Custom backup filename")
    parser_full.add_argument(
        "--no-analytics",
        action="store_false",
        dest="include_analytics",
        help="Exclude analytics tables from backup",
    )
    parser_full.set_defaults(func=cmd_create_full_backup)

    # Schema backup command
    parser_schema = subparsers.add_parser("schema", help="Create schema-only backup")
    parser_schema.set_defaults(func=cmd_create_schema_backup)

    # List backups command
    parser_list = subparsers.add_parser("list", help="List all backups")
    parser_list.set_defaults(func=cmd_list_backups)

    # Verify backup command
    parser_verify = subparsers.add_parser("verify", help="Verify backup integrity")
    parser_verify.add_argument("backup_path", help="Path to backup file")
    parser_verify.set_defaults(func=cmd_verify_backup)

    # Restore backup command
    parser_restore = subparsers.add_parser("restore", help="Restore from backup")
    parser_restore.add_argument("backup_path", help="Path to backup file")
    parser_restore.add_argument("--target-database", help="Target database name")
    parser_restore.add_argument(
        "--drop-existing",
        action="store_true",
        help="Drop existing database connections before restore",
    )
    parser_restore.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )
    parser_restore.set_defaults(func=cmd_restore_backup)

    # Cleanup command
    parser_cleanup = subparsers.add_parser("cleanup", help="Clean up old backups")
    parser_cleanup.add_argument(
        "-y", "--yes", action="store_true", help="Skip confirmation prompt"
    )
    parser_cleanup.set_defaults(func=cmd_cleanup_backups)

    # Status command
    parser_status = subparsers.add_parser("status", help="Show backup system status")
    parser_status.set_defaults(func=cmd_status)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Execute the command
    return args.func(args)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
