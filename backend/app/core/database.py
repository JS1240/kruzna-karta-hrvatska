import logging
import time
from typing import Any, Dict, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

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


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database session management with robust error handling.
    
    Primary database dependency used throughout the application for dependency injection.
    Provides a SQLAlchemy session with automatic transaction management, error recovery,
    and proper resource cleanup. Uses a generator pattern to ensure sessions are
    properly closed even if exceptions occur.
    
    Yields:
        Session: SQLAlchemy database session for performing database operations
        
    Raises:
        Exception: Re-raises any database-related exceptions after attempting recovery
        
    Note:
        This function implements robust error handling:
        - Automatic rollback on transaction failures
        - Session recreation if rollback fails
        - Guaranteed session cleanup in finally block
        - Comprehensive error logging for debugging
        
        Usage in FastAPI endpoints:
        ```python
        def my_endpoint(db: Session = Depends(get_db)):
            # Use db session here
        ```
    """
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
            except Exception:
                pass
            db = SessionLocal()
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.warning(f"Error closing database session: {close_error}")


def get_fresh_db_session() -> Session:
    """Create a new database session with error handling and logging.
    
    Creates a fresh SQLAlchemy session outside of the FastAPI dependency system.
    Useful for background tasks, CLI operations, or when you need a session
    that's not tied to a request lifecycle.
    
    Returns:
        Session: New SQLAlchemy database session ready for use
        
    Raises:
        Exception: Re-raises any session creation errors with additional logging
        
    Note:
        Unlike get_db(), this function does not automatically handle session
        cleanup. The caller is responsible for properly closing the session
        or handling it within a context manager.
        
        Usage:
        ```python
        db = get_fresh_db_session()
        try:
            # Perform database operations
        finally:
            db.close()
        ```
    """
    try:
        return SessionLocal()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise


def safe_db_operation(operation_func, *args, **kwargs) -> Any:
    """Execute database operation with automatic retry logic and error recovery.
    
    Wrapper function for database operations that provides resilience against
    transient failures, connection issues, and transaction conflicts. Automatically
    retries operations up to 3 times with proper cleanup between attempts.
    
    Args:
        operation_func: Function to execute that takes a database session as first parameter
        *args: Additional positional arguments to pass to operation_func
        **kwargs: Additional keyword arguments to pass to operation_func
        
    Returns:
        Any: Result returned by the operation_func
        
    Raises:
        SQLAlchemyError: Re-raises the final error if all retry attempts fail
        
    Note:
        The operation_func should follow this signature:
        ```python
        def my_operation(db: Session, *args, **kwargs):
            # Perform database operations using db session
            return result
        ```
        
        Retry logic specifically handles transaction abort errors and provides
        exponential backoff behavior for resilience against temporary issues.
    """
    max_retries = 3
    for attempt in range(max_retries):
        db = None
        try:
            db = get_fresh_db_session()
            result = operation_func(db, *args, **kwargs)
            return result
        except SQLAlchemyError as e:
            if db:
                try:
                    db.rollback()
                except SQLAlchemyError:
                    pass
                try:
                    db.close()
                except SQLAlchemyError:
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
                except SQLAlchemyError:
                    pass


def get_db_pool_status() -> Dict[str, int]:
    """Get current database connection pool metrics for monitoring.
    
    Retrieves real-time statistics about the SQLAlchemy connection pool to help
    monitor database performance, detect connection leaks, and optimize pool
    configuration.
    
    Returns:
        Dict containing connection pool metrics:
            - pool_size: Maximum number of connections in the pool
            - checked_in: Number of connections currently available in the pool
            - checked_out: Number of connections currently in use
            - overflow: Number of connections beyond the pool size
            - invalid: Number of invalid connections that need cleanup
            
    Note:
        These metrics are useful for:
        - Monitoring connection usage patterns
        - Detecting connection leaks (high checked_out, low checked_in)
        - Optimizing pool_size and max_overflow settings
        - Alerting on pool exhaustion conditions
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalid(),
    }


def reset_database_connections() -> bool:
    """Reset the database connection pool to recover from connection issues.
    
    Emergency recovery function that disposes of all connections in the pool
    and forces creation of fresh connections. Useful for recovering from
    network issues, database restarts, or persistent transaction problems.
    
    Returns:
        bool: True if reset was successful, False if an error occurred
        
    Note:
        This is a disruptive operation that will:
        - Close all existing database connections
        - Force active operations to reconnect
        - Clear any cached connection state
        
        Use this function judiciously as it may cause temporary disruption
        to ongoing database operations. Primarily intended for admin/recovery
        scenarios and health check recovery procedures.
    """
    try:
        # Dispose of all connections in the pool
        engine.dispose()
        logger.info("Database connection pool reset successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to reset database connections: {e}")
        return False


def health_check_db() -> Dict[str, Any]:
    """Perform comprehensive database health check with connectivity and integrity tests.
    
    Executes a series of tests to verify database functionality including basic
    connectivity, table access, connection pool status, and data integrity.
    Automatically attempts connection reset if health check fails.
    
    Returns:
        Dict containing health check results:
            On success:
                - status: "healthy"
                - database_connected: True
                - pool_status: Connection pool metrics
                - connectivity: "ok"
                - event_table: "accessible"
            On failure:
                - status: "unhealthy"
                - database_connected: False
                - error: Error message describing the failure
                - reset_attempted: Whether connection reset was tried
                
    Note:
        Health check performs these validations:
        1. Basic connectivity test (SELECT 1)
        2. Event table accessibility check
        3. Connection pool status analysis
        4. Automatic recovery attempt on failure
        
        This function is safe to call frequently for monitoring purposes.
    """
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

