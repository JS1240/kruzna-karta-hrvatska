from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.mock_events import router as mock_events_router

app = FastAPI(
    title="Diidemo.hr API (Demo)",
    description="Demo Backend API for Croatian Events Discovery Platform",
    version="1.0.0-demo",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include mock events router
app.include_router(mock_events_router, prefix="/api/events", tags=["events"])


@app.get("/")
def read_root():
    return {"message": "Diidemo.hr API (Demo)", "version": "1.0.0-demo"}


@app.get("/health")
def health_check():
    return {"status": "healthy", "mode": "demo"}


@app.get("/api/scraping/status")
def scraping_status():
    return {"status": "disabled", "message": "Scraping disabled in demo mode"}
