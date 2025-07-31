import logging
import os
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


from app.core.config import settings
from app.core.cors_middleware import CustomCORSMiddleware
from app.core.exception_handlers import setup_exception_handlers, correlation_id_middleware
from app.routes import (
    categories_router,
    events_router,
    venues_router,
)
# Stripe webhooks removed for MVP


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Kruzna Karta Hrvatska API...")
    logger.info("Centralized exception handlers and correlation ID middleware configured")

    # Start scheduler if enabled
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    if enable_scheduler:
        from app.tasks.scheduler import start_scheduler

        development = settings.debug
        start_scheduler(development=development)

    yield

    # Shutdown
    if enable_scheduler:
        from app.tasks.scheduler import stop_scheduler

        stop_scheduler()
    logger.info("Shutting down Kruzna Karta Hrvatska API...")


app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version,
    debug=settings.api.debug,
    lifespan=lifespan,
)

# Setup centralized exception handlers for consistent error responses
setup_exception_handlers(app)

# Custom CORS middleware to handle OPTIONS requests before route validation
app.add_middleware(
    CustomCORSMiddleware,
    allow_origins=settings.api.cors_origins + [settings.frontend_url],
    allow_credentials=settings.api.cors_credentials,
    allow_methods=settings.api.cors_methods,
    allow_headers=settings.api.cors_headers,
    expose_headers=["*"],
    max_age=600,
)

# Add correlation ID middleware for request tracing
app.middleware("http")(correlation_id_middleware)

# Include routers
app.include_router(events_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(venues_router, prefix="/api")
# Stripe webhooks router removed for MVP


@app.get("/")
def read_root() -> Dict[str, str]:
    """Get API information and version details.
    
    Root endpoint providing basic information about the Kruzna Karta Hrvatska API.
    Useful for API discovery, documentation tools, and verification that the
    service is running and accessible.
    
    Returns:
        Dict containing:
            - message: Human-readable API name and description
            - version: Current API version for compatibility checking
            
    Note:
        This endpoint is publicly accessible and does not require authentication.
        It serves as the entry point for API documentation and health verification.
    """
    return {"message": "Kruzna Karta Hrvatska API", "version": "1.0.0"}


@app.get("/health")
def health_check() -> Dict[str, str]:
    """Perform basic application health check.
    
    Simple health endpoint for monitoring systems and load balancers to verify
    that the application is running and responsive. This is a lightweight check
    that only verifies application startup, not database connectivity or
    external service availability.
    
    Returns:
        Dict containing:
            - status: "healthy" if application is running normally
            
    Note:
        For comprehensive health checking including database and external services,
        use the /api/events/db-health/ endpoint. This endpoint is designed for
        high-frequency monitoring with minimal resource usage.
    """
    return {"status": "healthy"}
