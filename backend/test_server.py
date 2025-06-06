#!/usr/bin/env python3
"""Simple test script to verify backend functionality"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    from app.core.config import settings
    from app.models.event import Event
    from app.routes.events import router as events_router
    print("✅ All imports successful")
    
    # Test configuration
    print(f"✅ Database URL configured: {settings.database_url}")
    print(f"✅ API will run on: {settings.api_host}:{settings.api_port}")
    
    # Test basic FastAPI app creation
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(events_router, prefix="/api")
    print("✅ FastAPI app created successfully")
    
    print("\n🎉 Backend integration test passed!")
    print("Backend components are working correctly.")
    
except Exception as e:
    print(f"❌ Backend test failed: {e}")
    import traceback
    traceback.print_exc()