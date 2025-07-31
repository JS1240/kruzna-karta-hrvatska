#!/usr/bin/env python3
"""
Error Handling Validation Test Script

Tests the standardized error handling implementation to ensure:
- Custom exceptions are properly caught and converted
- Error responses have consistent JSON structure  
- HTTP status codes are correct
- Correlation IDs are generated and included
- All route endpoints use the new error handling system

This script validates Phase 5: Error Handling Standardization implementation.
"""

import json
import logging
import sys
from typing import Dict, Any

from fastapi.testclient import TestClient

# Import the FastAPI app and test it
try:
    from backend.app.main import app
    client = TestClient(app)
except ImportError as e:
    print(f"Error importing FastAPI app: {e}")
    print("Please ensure you're running this from the backend directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_error_response_structure(response_data: Dict[str, Any], expected_code: str = None) -> bool:
    """Validate that error response has the expected structure."""
    required_fields = [
        'error', 'correlation_id', 'timestamp', 'category', 'severity', 
        'code', 'message', 'status_code'
    ]
    
    # Check all required fields are present
    for field in required_fields:
        if field not in response_data:
            logger.error(f"Missing required field: {field}")
            return False
    
    # Validate field types
    if not isinstance(response_data['error'], bool) or response_data['error'] != True:
        logger.error("'error' field should be True")
        return False
        
    if not isinstance(response_data['correlation_id'], str):
        logger.error("'correlation_id' should be a string")
        return False
        
    if not isinstance(response_data['status_code'], int):
        logger.error("'status_code' should be an integer")
        return False
    
    # Validate expected error code if provided
    if expected_code and response_data.get('code') != expected_code:
        logger.error(f"Expected error code '{expected_code}', got '{response_data.get('code')}'")
        return False
    
    return True


def test_event_not_found():
    """Test EventNotFoundError handling."""
    logger.info("Testing Event Not Found error...")
    
    response = client.get("/api/events/99999")  # Non-existent event ID
    
    if response.status_code != 404:
        logger.error(f"Expected 404, got {response.status_code}")
        return False
    
    response_data = response.json()
    if not validate_error_response_structure(response_data, "EVENT_NOT_FOUND"):
        return False
    
    # Check error message contains event ID
    if "99999" not in response_data['message']:
        logger.error("Error message should contain the event ID")
        return False
    
    logger.info("✅ Event Not Found test passed")
    return True


def test_category_not_found():
    """Test CategoryNotFoundError handling."""
    logger.info("Testing Category Not Found error...")
    
    response = client.get("/api/categories/99999")  # Non-existent category ID
    
    if response.status_code != 404:
        logger.error(f"Expected 404, got {response.status_code}")
        return False
    
    response_data = response.json()
    if not validate_error_response_structure(response_data, "CATEGORY_NOT_FOUND"):
        return False
    
    # Check error message contains category ID
    if "99999" not in response_data['message']:
        logger.error("Error message should contain the category ID")
        return False
    
    logger.info("✅ Category Not Found test passed")
    return True


def test_venue_not_found():
    """Test VenueNotFoundError handling."""
    logger.info("Testing Venue Not Found error...")
    
    response = client.get("/api/venues/99999")  # Non-existent venue ID
    
    if response.status_code != 404:
        logger.error(f"Expected 404, got {response.status_code}")
        return False
    
    response_data = response.json()
    if not validate_error_response_structure(response_data, "VENUE_NOT_FOUND"):
        return False
    
    # Check error message contains venue ID
    if "99999" not in response_data['message']:
        logger.error("Error message should contain the venue ID")
        return False
    
    logger.info("✅ Venue Not Found test passed")
    return True


def test_validation_error():
    """Test validation error handling."""
    logger.info("Testing Validation Error handling...")
    
    # Try to create event with invalid data
    invalid_event_data = {
        "title": "",  # Empty title should fail validation
        "description": "Test event"
        # Missing required fields
    }
    
    response = client.post("/api/events/", json=invalid_event_data)
    
    if response.status_code != 422:
        logger.error(f"Expected 422, got {response.status_code}")
        return False
    
    response_data = response.json()
    if not validate_error_response_structure(response_data, "VALIDATION_ERROR"):
        return False
    
    # Check that details are provided for validation errors
    if 'details' not in response_data or not response_data['details']:
        logger.error("Validation errors should include details")
        return False
    
    logger.info("✅ Validation Error test passed")
    return True


def test_correlation_id_consistency():
    """Test that correlation IDs are consistent and included in headers."""
    logger.info("Testing Correlation ID consistency...")
    
    # Make request with custom correlation ID
    custom_correlation_id = "test-correlation-123"
    headers = {"X-Correlation-ID": custom_correlation_id}
    
    response = client.get("/api/events/99999", headers=headers)
    
    # Check that correlation ID is in response headers
    if "X-Correlation-ID" not in response.headers:
        logger.error("Response should include X-Correlation-ID header")
        return False
    
    if response.headers["X-Correlation-ID"] != custom_correlation_id:
        logger.error("Response correlation ID should match request correlation ID")
        return False
    
    # Check that correlation ID is in error response body
    response_data = response.json()
    if response_data.get('correlation_id') != custom_correlation_id:
        logger.error("Error response should include the same correlation ID")
        return False
    
    logger.info("✅ Correlation ID consistency test passed")
    return True


def test_health_endpoint():
    """Test that health endpoint still works correctly."""
    logger.info("Testing Health endpoint...")
    
    response = client.get("/health")
    
    if response.status_code != 200:
        logger.error(f"Health endpoint should return 200, got {response.status_code}")
        return False
    
    response_data = response.json()
    if response_data.get('status') != 'healthy':
        logger.error("Health endpoint should return status 'healthy'")
        return False
    
    logger.info("✅ Health endpoint test passed")
    return True


def run_validation_tests():
    """Run all validation tests."""
    logger.info("🔍 Starting Error Handling Validation Tests...")
    logger.info("=" * 60)
    
    tests = [
        test_health_endpoint,
        test_event_not_found,
        test_category_not_found, 
        test_venue_not_found,
        test_validation_error,
        test_correlation_id_consistency,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            logger.error(f"Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    logger.info("=" * 60)
    logger.info(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED - Error handling implementation is working correctly!")
        return True
    else:
        logger.error(f"❌ {failed} tests failed - Error handling needs fixes")
        return False


if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)