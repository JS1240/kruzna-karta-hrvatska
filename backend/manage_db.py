#!/usr/bin/env python3
"""
Database management utility script for Kruzna Karta Hrvatska.
Provides commands for running migrations, creating new migrations, and database operations.
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append(os.path.dirname(__file__))
logger = logging.getLogger(__name__)

def run_migrations():
    """Run all pending migrations."""
    logger.info("Running database migrations...")
    os.system(".venv/bin/alembic upgrade head")

def create_migration(message):
    """Create a new migration with autogenerate."""
    logger.info(f"Creating new migration: {message}")
    os.system(f'.venv/bin/alembic revision --autogenerate -m "{message}"')

def rollback_migration():
    """Rollback the last migration."""
    logger.info("Rolling back last migration...")
    os.system(".venv/bin/alembic downgrade -1")

def show_current_revision():
    """Show current database revision."""
    logger.info("Current database revision:")
    os.system(".venv/bin/alembic current")

def show_migration_history():
    """Show migration history."""
    logger.info("Migration history:")
    os.system(".venv/bin/alembic history")

def reset_database():
    """Reset database to base (WARNING: This will delete all data!)."""
    response = input("WARNING: This will delete all data! Are you sure? (yes/no): ")
    if response.lower() == 'yes':
        logger.info("Resetting database...")
        os.system(".venv/bin/alembic downgrade base")
        logger.info("Database reset complete.")
    else:
        logger.info("Database reset cancelled.")

def setup_database():
    """Set up database from scratch."""
    logger.info("Setting up database from scratch...")
    logger.info("1. Running migrations...")
    run_migrations()
    logger.info("Database setup complete!")

def main():
    parser = argparse.ArgumentParser(description='Database management for Kruzna Karta Hrvatska')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migration commands
    subparsers.add_parser('migrate', help='Run all pending migrations')
    subparsers.add_parser('setup', help='Set up database from scratch')
    
    create_parser = subparsers.add_parser('create', help='Create a new migration')
    create_parser.add_argument('message', help='Migration message')
    
    subparsers.add_parser('rollback', help='Rollback the last migration')
    subparsers.add_parser('current', help='Show current database revision')
    subparsers.add_parser('history', help='Show migration history')
    subparsers.add_parser('reset', help='Reset database to base (WARNING: Deletes all data!)')
    
    args = parser.parse_args()
    
    if args.command == 'migrate':
        run_migrations()
    elif args.command == 'setup':
        setup_database()
    elif args.command == 'create':
        create_migration(args.message)
    elif args.command == 'rollback':
        rollback_migration()
    elif args.command == 'current':
        show_current_revision()
    elif args.command == 'history':
        show_migration_history()
    elif args.command == 'reset':
        reset_database()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()