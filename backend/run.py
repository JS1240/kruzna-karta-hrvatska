#!/usr/bin/env python3
"""Development server runner for Kruzna Karta Hrvatska backend."""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.development.reload,
        log_level="info" if not settings.api.debug else "debug"
    )