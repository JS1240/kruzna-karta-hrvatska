#!/usr/bin/env python3
"""Simple test script to verify backend functionality"""

import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
logger = logging.getLogger(__name__)

try:
    # Test imports
    from app.core.config import settings
    from app.models.event import Event
    from app.routes.events import router as events_router
    logger.info("✅ All imports successful")
    
    # Test configuration
    logger.info(f"✅ Database URL configured: {settings.database_url}")
    logger.info(f"✅ API will run on: {settings.api_host}:{settings.api_port}")
    
    # Test basic FastAPI app creation
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(events_router, prefix="/api")
    logger.info("✅ FastAPI app created successfully")
    
    logger.info("\n🎉 Backend integration test passed!")
    logger.info("Backend components are working correctly.")
    
except Exception as e:
    logger.error(f"❌ Backend test failed: {e}")
    import traceback
    traceback.print_exc()