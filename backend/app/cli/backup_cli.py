#!/usr/bin/env python3
"""
Command line interface for database backup operations.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.backup import PostgreSQLBackupService


def create_backup_service():
    """Create and return a backup service instance."""
    return PostgreSQLBackupService()


def cmd_create_full_backup(args):
    """Create a full database backup."""
    try:
        backup_service = create_backup_service()

        print(f"Starting full backup...")
        print(f"Include analytics: {args.include_analytics}")
        if args.filename:
            print(f"Custom filename: {args.filename}")

        metadata = backup_service.create_full_backup(
            custom_filename=args.filename, include_analytics=args.include_analytics
        )

        print(f"✓ Full backup completed successfully!")
        print(f"  Backup ID: {metadata.backup_id}")
        print(f"  File: {metadata.file_path}")
        print(f"  Size: {metadata.file_size:,} bytes")
        print(f"  Duration: {metadata.duration_seconds:.2f} seconds")
        print(f"  Tables: {len(metadata.tables_included)}")

        if metadata.storage_location:
            print(f"  S3 Location: {metadata.storage_location}")

        return 0

    except Exception as e:
        print(f"✗ Full backup failed: {e}")
        return 1


def cmd_create_schema_backup(args):
    """Create a schema-only backup."""
    try:
        backup_service = create_backup_service()

        print("Starting schema backup...")

        metadata = backup_service.create_schema_backup()

        print(f"✓ Schema backup completed successfully!")
        print(f"  Backup ID: {metadata.backup_id}")
        print(f"  File: {metadata.file_path}")
        print(f"  Size: {metadata.file_size:,} bytes")
        print(f"  Duration: {metadata.duration_seconds:.2f} seconds")

        return 0

    except Exception as e:
        print(f"✗ Schema backup failed: {e}")
        return 1


def cmd_list_backups(args):
    """List all available backups."""
    try:
        backup_service = create_backup_service()
        backups = backup_service.list_backups()

        if not backups:
            print("No backups found.")
            return 0

        print(f"\nFound {len(backups)} backup(s):\n")

        for backup in backups:
            created_at = datetime.fromisoformat(backup["created_at"])
            size_mb = backup["file_size"] / 1024 / 1024

            print(f"ID: {backup['backup_id']}")
            print(f"  Type: {backup['backup_type']}")
            print(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Size: {size_mb:.1f} MB")
            print(f"  Status: {backup['status']}")
            print(f"  File: {backup['file_path']}")

            if backup.get("storage_location"):
                print(f"  S3: {backup['storage_location']}")

            print()

        return 0

    except Exception as e:
        print(f"✗ Failed to list backups: {e}")
        return 1


def cmd_verify_backup(args):
    """Verify backup integrity."""
    try:
        backup_service = create_backup_service()

        print(f"Verifying backup: {args.backup_path}")

        result = backup_service.verify_backup(args.backup_path)

        if result["status"] == "success":
            print("✓ Backup verification successful!")
            print(f"  File exists: {result['file_exists']}")
            print(f"  File size: {result['file_size']:,} bytes")
            print(f"  PostgreSQL readable: {result['pg_readable']}")

            if result["checksum_match"] is not None:
                print(f"  Checksum match: {result['checksum_match']}")
                print(f"  Current checksum: {result['current_checksum']}")
        else:
            print(f"✗ Backup verification failed: {result['error']}")
            return 1

        return 0

    except Exception as e:
        print(f"✗ Backup verification failed: {e}")
        return 1


def cmd_restore_backup(args):
    """Restore from backup."""
    try:
        backup_service = create_backup_service()

        print(f"Restoring from backup: {args.backup_path}")
        if args.target_database:
            print(f"Target database: {args.target_database}")
        print(f"Drop existing: {args.drop_existing}")

        # Confirmation prompt
        if not args.yes:
            response = input(
                "Are you sure you want to proceed? This will modify the database. (y/N): "
            )
            if response.lower() != "y":
                print("Restore cancelled.")
                return 0

        result = backup_service.restore_from_backup(
            backup_path=args.backup_path,
            target_database=args.target_database,
            drop_existing=args.drop_existing,
        )

        print("✓ Database restore completed successfully!")
        print(f"  Target database: {result['target_database']}")
        print(f"  Duration: {result['duration_seconds']:.2f} seconds")

        return 0

    except Exception as e:
        print(f"✗ Database restore failed: {e}")
        return 1


def cmd_cleanup_backups(args):
    """Clean up old backups."""
    try:
        backup_service = create_backup_service()

        print("Cleaning up old backups...")

        # Confirmation prompt
        if not args.yes:
            response = input(
                f"This will delete backups older than {backup_service.max_backup_age_days} days. Continue? (y/N): "
            )
            if response.lower() != "y":
                print("Cleanup cancelled.")
                return 0

        result = backup_service.cleanup_old_backups()

        if result["status"] == "success":
            print("✓ Backup cleanup completed successfully!")
            print(f"  Files cleaned: {result['cleaned_files']}")
            print(f"  Space freed: {result['size_freed_bytes']:,} bytes")

            if result.get("s3_files_cleaned"):
                print(f"  S3 files cleaned: {result['s3_files_cleaned']}")
        else:
            print(f"✗ Backup cleanup failed: {result['error']}")
            return 1

        return 0

    except Exception as e:
        print(f"✗ Backup cleanup failed: {e}")
        return 1


def cmd_status(args):
    """Show backup system status."""
    try:
        backup_service = create_backup_service()
        status = backup_service.get_backup_status()

        print("Backup System Status")
        print("=" * 50)
        print(f"Status: {status['status']}")
        print(f"Backup Directory: {status['backup_directory']}")
        print(f"Total Backups: {status['total_backups']}")
        print(f"Completed: {status['completed_backups']}")
        print(f"Failed: {status['failed_backups']}")
        print(f"Corrupted: {status['corrupted_backups']}")
        print(f"Total Storage: {status['total_storage_bytes']:,} bytes")
        print(f"S3 Enabled: {status['s3_enabled']}")
        print(f"Compression: {status['compression_enabled']}")
        print(f"Retention Days: {status['retention_days']}")

        if status.get("latest_backup"):
            latest = status["latest_backup"]
            created_at = datetime.fromisoformat(latest["created_at"])
            print(f"\nLatest Backup:")
            print(f"  ID: {latest['backup_id']}")
            print(f"  Type: {latest['backup_type']}")
            print(f"  Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Status: {latest['status']}")

        # Disk usage
        disk = status["disk_usage"]
        print(f"\nDisk Usage:")
        print(f"  Total: {disk['total_bytes']:,} bytes")
        print(f"  Used: {disk['used_bytes']:,} bytes")
        print(f"  Free: {disk['free_bytes']:,} bytes")
        print(f"  Usage: {disk['usage_percentage']:.1f}%")

        return 0

    except Exception as e:
        print(f"✗ Failed to get backup status: {e}")
        return 1


def main():
    """Main CLI entry point."""
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
