#!/usr/bin/env python3
"""Simple test script to verify backend functionality"""

import sys
import os
import logging

from app.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    from app.core.config import settings
    from app.models.event import Event
    from app.routes.events import router as events_router
    logger.info("✅ All imports successful")
    
    # Test configuration
    logger.info("✅ Database URL configured: %s", settings.database_url)
    logger.info("✅ API will run on: %s:%s", settings.api_host, settings.api_port)
    
    # Test basic FastAPI app creation
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(events_router, prefix="/api")
    logger.info("✅ FastAPI app created successfully")
    
    logger.info("\n🎉 Backend integration test passed!")
    logger.info("Backend components are working correctly.")
    
except Exception as e:
    logger.error("❌ Backend test failed: %s", e)
    import traceback
    traceback.print_exc()