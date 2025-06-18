import logging

from sqlalchemy import create_engine, event
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
    """Enhanced database dependency with performance monitoring."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


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


def health_check_db():
    """Perform database health check."""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()

        pool_status = get_db_pool_status()

        return {
            "status": "healthy",
            "database_connected": True,
            "pool_status": pool_status,
        }
    except Exception as e:
        return {"status": "unhealthy", "database_connected": False, "error": str(e)}


# Import time for query timing
import time
