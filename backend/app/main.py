from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .core.config import settings
from .routes import events_router, scraping_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting Kruzna Karta Hrvatska API...")
    
    # Start scheduler if enabled
    enable_scheduler = settings.enable_scheduler
    if enable_scheduler:
        from .tasks.scheduler import start_scheduler
        development = settings.debug
        start_scheduler(development=development)
    
    yield
    
    # Shutdown
    if enable_scheduler:
        from .tasks.scheduler import stop_scheduler
        stop_scheduler()
    print("Shutting down Kruzna Karta Hrvatska API...")

app = FastAPI(
    title="Kruzna Karta Hrvatska API",
    description="Backend API for Croatian Events Platform",
    version="1.0.0",
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events_router, prefix="/api")
app.include_router(scraping_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Kruzna Karta Hrvatska API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}