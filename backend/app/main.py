import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

from fastapi import Request, Response

from .core.config import settings
from .core.cors_middleware import CustomCORSMiddleware
from .routes import (
    analytics_router,
    auth_router,
    backup_router,
    booking_router,
    categories_router,
    croatian_router,
    events_router,
    gdpr_router,
    monitoring_router,
    performance_router,
    recurring_events_router,
    scraping_router,
    social_router,
    system_test_router,
    recommendations_router,
    third_party_router,
    translations_router,
    user_events_router,
    users_router,
    venue_management_router,
    venues_router,
)
from .routes.stripe_webhooks import router as stripe_webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Kruzna Karta Hrvatska API...")

    # Start scheduler if enabled
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "false").lower() == "true"
    if enable_scheduler:
        from .tasks.scheduler import start_scheduler

        development = settings.debug
        start_scheduler(development=development)

    yield

    # Shutdown
    if enable_scheduler:
        from .tasks.scheduler import stop_scheduler

        stop_scheduler()
    logger.info("Shutting down Kruzna Karta Hrvatska API...")


app = FastAPI(
    title="Kruzna Karta Hrvatska API",
    description="Backend API for Croatian Events Platform",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan,
)

# Custom CORS middleware to handle OPTIONS requests before route validation
app.add_middleware(
    CustomCORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(events_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(venues_router, prefix="/api")
app.include_router(translations_router, prefix="/api")
app.include_router(scraping_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(performance_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(monitoring_router, prefix="/api")
app.include_router(gdpr_router, prefix="/api")
app.include_router(croatian_router, prefix="/api")
app.include_router(booking_router, prefix="/api")
app.include_router(recurring_events_router, prefix="/api")
app.include_router(venue_management_router, prefix="/api")
app.include_router(social_router, prefix="/api")
app.include_router(user_events_router, prefix="/api")
app.include_router(system_test_router, prefix="/api")
app.include_router(recommendations_router, prefix="/api")
app.include_router(third_party_router, prefix="/api")
app.include_router(stripe_webhooks_router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Kruzna Karta Hrvatska API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
