# Database Migrations for Kruzna Karta Hrvatska

This directory contains Alembic migrations for the Croatian event platform database.

## Overview

The migration system uses Alembic to manage database schema changes and provides version control for the PostgreSQL database.

## Migration Files

### Initial Migrations
1. **20250606_232105_initial_migration_with_enhanced_event_schema.py**
   - Creates the core database schema with three tables:
     - `event_categories` - Event categorization
     - `venues` - Event venues with geographic data
     - `events` - Enhanced events table with full feature set
   - Includes comprehensive indexing for performance
   - Sets up foreign key relationships and constraints

2. **20250606_232129_add_database_functions_and_triggers.py**
   - Adds PostgreSQL functions for automatic timestamp updates
   - Adds function for automatic search vector generation
   - Creates triggers for events and venues tables

3. **20250606_232301_add_sample_data.py**
   - Inserts sample Croatian event categories (10 categories)
   - Inserts sample Croatian venues (15 venues across Croatia)
   - Inserts sample Croatian events (12 events with full data)

## Usage

### Using the Database Management Script

```bash
# Set up database from scratch
python manage_db.py setup

# Run pending migrations
python manage_db.py migrate

# Create a new migration
python manage_db.py create "Add new feature"

# Show current database version
python manage_db.py current

# Show migration history
python manage_db.py history

# Rollback last migration
python manage_db.py rollback

# Reset database (WARNING: Deletes all data!)
python manage_db.py reset
```

### Using Alembic Directly

```bash
# Run migrations
.venv/bin/alembic upgrade head

# Create new migration
.venv/bin/alembic revision --autogenerate -m "Description"

# Show current revision
.venv/bin/alembic current

# Show history
.venv/bin/alembic history

# Rollback one migration
.venv/bin/alembic downgrade -1
```

## Database Schema

### Tables
- **event_categories**: Event categorization system
- **venues**: Physical locations for events with coordinates
- **events**: Main events table with enhanced features

### Key Features
- Full-text search capabilities using PostgreSQL tsvector
- Geographic data for mapping (latitude/longitude)
- Event categorization and tagging
- Venue management with capacity and facilities
- Automatic timestamp updates
- Data integrity constraints
- Comprehensive indexing

### Relationships
- Events can belong to a category (many-to-one)
- Events can be held at a venue (many-to-one)
- Foreign key constraints maintain data integrity

## Configuration

The migration system is configured to:
- Use PostgreSQL as the database
- Read database connection from app settings
- Auto-import SQLAlchemy models for detection
- Support both online and offline migration modes

## Environment Setup

Ensure your `.env` file contains the correct database configuration:

```
DATABASE_URL=postgresql://username:password@localhost:5432/kruzna_karta_hrvatska
```

## Production Deployment

For production deployments:

1. Always backup the database before running migrations
2. Test migrations on a staging environment first
3. Use the database management script for consistency
4. Monitor migration execution for any errors

## Development Workflow

1. Make changes to SQLAlchemy models
2. Create migration: `python manage_db.py create "Description of changes"`
3. Review the generated migration file
4. Test migration on development database
5. Commit migration file to version control
6. Deploy to staging/production environments