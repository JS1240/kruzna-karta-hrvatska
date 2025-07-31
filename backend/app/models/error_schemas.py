"""
Standardized error response schemas for consistent API error handling.

This module provides Pydantic models for structured error responses that ensure
consistency across all API endpoints and improve debugging capabilities.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorCategory(str, Enum):
    """Enumeration of error categories for systematic error classification."""
    
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    NOT_FOUND = "not_found"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    INTERNAL_SERVER = "internal_server"
    RATE_LIMIT = "rate_limit"
    MAINTENANCE = "maintenance"


class ErrorSeverity(str, Enum):
    """Error severity levels for monitoring and alerting."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorDetail(BaseModel):
    """Individual error detail with specific context."""
    
    code: str = Field(..., description="Specific error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field name if error is field-specific")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Standardized error response model for all API endpoints."""
    
    error: bool = Field(True, description="Always true for error responses")
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for request tracing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when error occurred"
    )
    category: ErrorCategory = Field(..., description="Error category for systematic handling")
    severity: ErrorSeverity = Field(ErrorSeverity.MEDIUM, description="Error severity level")
    
    # Main error information
    code: str = Field(..., description="Primary error code")
    message: str = Field(..., description="Primary error message")
    details: Optional[List[ErrorDetail]] = Field(
        None, 
        description="Detailed error information for complex errors"
    )
    
    # HTTP context
    status_code: int = Field(..., description="HTTP status code")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    method: Optional[str] = Field(None, description="HTTP method used")
    
    # Debugging information (only in development/staging)
    debug_info: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional debugging information"
    )
    
    # Internationalization support
    locale: Optional[str] = Field("en", description="Language code for error messages")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "error": True,
                "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2024-01-15T10:30:00Z",
                "category": "not_found",
                "severity": "low",
                "code": "EVENT_NOT_FOUND",
                "message": "Event with ID 123 was not found",
                "status_code": 404,
                "path": "/api/events/123",
                "method": "GET",
                "locale": "en"
            }
        }


class ValidationErrorResponse(ErrorResponse):
    """Specialized error response for validation errors."""
    
    category: ErrorCategory = Field(ErrorCategory.VALIDATION, description="Always validation category")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "error": True,
                "correlation_id": "550e8400-e29b-41d4-a716-446655440001",
                "timestamp": "2024-01-15T10:30:00Z",
                "category": "validation",
                "severity": "low",
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": [
                    {
                        "code": "FIELD_REQUIRED",
                        "message": "This field is required",
                        "field": "title",
                        "context": {"provided_value": None}
                    }
                ],
                "status_code": 422,
                "path": "/api/events",
                "method": "POST",
                "locale": "en"
            }
        }


class BusinessLogicErrorResponse(ErrorResponse):
    """Specialized error response for business logic violations."""
    
    category: ErrorCategory = Field(ErrorCategory.BUSINESS_LOGIC, description="Always business logic category")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "error": True,
                "correlation_id": "550e8400-e29b-41d4-a716-446655440002",
                "timestamp": "2024-01-15T10:30:00Z",
                "category": "business_logic",
                "severity": "medium",
                "code": "CANNOT_DELETE_REFERENCED_ENTITY",
                "message": "Cannot delete venue because it has associated events",
                "details": [
                    {
                        "code": "ENTITY_REFERENCES_EXIST",
                        "message": "This venue has 5 associated events",
                        "context": {"venue_id": 123, "event_count": 5}
                    }
                ],
                "status_code": 400,
                "path": "/api/venues/123",
                "method": "DELETE",
                "locale": "en"
            }
        }


class InternalServerErrorResponse(ErrorResponse):
    """Specialized error response for internal server errors."""
    
    category: ErrorCategory = Field(ErrorCategory.INTERNAL_SERVER, description="Always internal server category")
    severity: ErrorSeverity = Field(ErrorSeverity.HIGH, description="Always high severity")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None
        }
        schema_extra = {
            "example": {
                "error": True,
                "correlation_id": "550e8400-e29b-41d4-a716-446655440003",
                "timestamp": "2024-01-15T10:30:00Z",
                "category": "internal_server",
                "severity": "high",
                "code": "DATABASE_CONNECTION_ERROR",
                "message": "An internal error occurred while processing your request",
                "status_code": 500,
                "path": "/api/events",
                "method": "GET",
                "locale": "en"
            }
        }


# Error code constants for consistent usage across the application
class ErrorCodes:
    """Centralized error codes for consistent error handling."""
    
    # Generic errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    INVALID_REQUEST = "INVALID_REQUEST"
    
    # Authentication & Authorization
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    
    # Resource errors
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    EVENT_NOT_FOUND = "EVENT_NOT_FOUND"
    CATEGORY_NOT_FOUND = "CATEGORY_NOT_FOUND"
    VENUE_NOT_FOUND = "VENUE_NOT_FOUND"
    
    # Validation errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    FIELD_REQUIRED = "FIELD_REQUIRED"
    FIELD_INVALID = "FIELD_INVALID"
    FIELD_TOO_LONG = "FIELD_TOO_LONG"
    FIELD_TOO_SHORT = "FIELD_TOO_SHORT"
    
    # Business logic errors
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    CATEGORY_SLUG_EXISTS = "CATEGORY_SLUG_EXISTS"
    VENUE_NAME_EXISTS = "VENUE_NAME_EXISTS"
    CANNOT_DELETE_REFERENCED_ENTITY = "CANNOT_DELETE_REFERENCED_ENTITY"
    
    # Database errors  
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    DATABASE_TRANSACTION_ERROR = "DATABASE_TRANSACTION_ERROR"
    DATABASE_TIMEOUT = "DATABASE_TIMEOUT"
    
    # External service errors
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE"
    GEOCODING_SERVICE_ERROR = "GEOCODING_SERVICE_ERROR"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# HTTP status code to error category mapping
STATUS_CODE_CATEGORY_MAP = {
    400: ErrorCategory.VALIDATION,
    401: ErrorCategory.AUTHENTICATION,
    403: ErrorCategory.AUTHORIZATION,
    404: ErrorCategory.NOT_FOUND,
    422: ErrorCategory.VALIDATION,
    429: ErrorCategory.RATE_LIMIT,
    500: ErrorCategory.INTERNAL_SERVER,
    502: ErrorCategory.EXTERNAL_SERVICE,
    503: ErrorCategory.MAINTENANCE,
}