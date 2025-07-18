import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from .config import settings

logger = logging.getLogger(__name__)

# Enhanced engine configuration with performance optimizations
engine_kwargs = {
    "poolclass": QueuePool,
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_max_overflow,
    "pool_timeout": settings.db_pool_timeout,
    "pool_recycle": settings.db_pool_recycle,
    "pool_pre_ping": True,  # Verify connections before use
    "echo": False,  # Set to True for SQL query logging in development
}

# Add performance-oriented connection arguments for PostgreSQL
if "postgresql" in settings.database_url:
    engine_kwargs["connect_args"] = {
        "options": "-c timezone=UTC",
        "application_name": "kruzna_karta_hrvatska",
        # Performance optimizations
        "connect_timeout": 10,
    }

engine = create_engine(settings.database_url, **engine_kwargs)

# Configure session with performance optimizations
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Keep objects accessible after commit
)

Base = declarative_base()


# Database event listeners for performance monitoring
@event.listens_for(engine, "before_cursor_execute")
def receive_before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log slow queries for performance monitoring."""
    context._query_start_time = time.time()


@event.listens_for(engine, "after_cursor_execute")
def receive_after_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
):
    """Log query execution time."""
    total = time.time() - context._query_start_time
    if total > 1.0:  # Log queries taking more than 1 second
        logger.warning(f"Slow query detected ({total:.2f}s): {statement[:200]}...")


def get_db():
    """Enhanced database dependency with robust transaction handling."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        try:
            # Ensure we rollback any failed transaction
            db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback transaction: {rollback_error}")
            # If rollback fails, close and recreate session
            try:
                db.close()
            except:
                pass
            db = SessionLocal()
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.warning(f"Error closing database session: {close_error}")


def get_fresh_db_session():
    """Get a fresh database session with error handling."""
    try:
        return SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise


def safe_db_operation(operation_func, *args, **kwargs):
    """Execute database operation with automatic retry and error handling."""
    max_retries = 3
    for attempt in range(max_retries):
        db = None
        try:
            db = get_fresh_db_session()
            result = operation_func(db, *args, **kwargs)
            return result
        except Exception as e:
            if db:
                try:
                    db.rollback()
                except:
                    pass
                try:
                    db.close()
                except:
                    pass
            
            # Check if this is a transaction error that we can retry
            if "transaction is aborted" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Transaction error on attempt {attempt + 1}, retrying...")
                continue
            else:
                logger.error(f"Database operation failed after {attempt + 1} attempts: {e}")
                raise
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass


def get_db_pool_status():
    """Get database connection pool status."""
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }


def reset_database_connections():
    """Reset database connection pool to clear any failed transactions."""
    try:
        # Dispose of all connections in the pool
        engine.dispose()
        logger.info("Database connection pool reset successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database connections: {e}")
        return False


def health_check_db():
    """Perform comprehensive database health check."""
    try:
        # Test basic connectivity
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db.commit()
            
            # Test event table access (the problematic table)
            db.execute(text("SELECT COUNT(*) FROM events LIMIT 1"))
            db.commit()
            
        finally:
            db.close()

        pool_status = get_db_pool_status()

        return {
            "status": "healthy",
            "database_connected": True,
            "pool_status": pool_status,
            "connectivity": "ok",
            "event_table": "accessible"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        
        # Try to reset connections if health check fails
        reset_success = reset_database_connections()
        
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "reset_attempted": reset_success,
        }


# Import time for query timing
import time
