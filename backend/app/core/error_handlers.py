"""
Centralized error handling utilities and custom exceptions.

This module provides utilities for creating consistent error responses,
custom exception classes, and helper functions for error handling across
the Croatian events platform API.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Union

from fastapi import Request, HTTPException

from app.models.error_schemas import (
    ErrorResponse,
    ErrorDetail,
    ErrorCategory,
    ErrorSeverity,
    ErrorCodes,
    ValidationErrorResponse,
    InternalServerErrorResponse,
    STATUS_CODE_CATEGORY_MAP
)

logger = logging.getLogger(__name__)


class StandardHTTPException(HTTPException):
    """Enhanced HTTPException with structured error response support."""
    
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None,
        details: Optional[List[ErrorDetail]] = None,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        """Initialize standardized HTTP exception.
        
        Args:
            status_code: HTTP status code
            code: Application-specific error code
            message: Human-readable error message
            category: Error category for systematic handling
            severity: Error severity level
            details: List of detailed error information
            context: Additional error context
            correlation_id: Request correlation ID for tracing
        """
        super().__init__(status_code=status_code, detail=message)
        self.code = code
        self.message = message
        self.category = category or STATUS_CODE_CATEGORY_MAP.get(status_code, ErrorCategory.INTERNAL_SERVER)
        self.severity = severity or ErrorSeverity.MEDIUM
        self.details = details or []
        self.context = context or {}
        self.correlation_id = correlation_id


class EventNotFoundError(StandardHTTPException):
    """Exception for event not found scenarios."""
    
    def __init__(self, event_id: Union[int, str], correlation_id: Optional[str] = None):
        super().__init__(
            status_code=404,
            code=ErrorCodes.EVENT_NOT_FOUND,
            message=f"Event with ID {event_id} was not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            context={"event_id": event_id},
            correlation_id=correlation_id
        )


class CategoryNotFoundError(StandardHTTPException):
    """Exception for category not found scenarios."""
    
    def __init__(self, identifier: Union[int, str], by_slug: bool = False, correlation_id: Optional[str] = None):
        identifier_type = "slug" if by_slug else "ID"
        super().__init__(
            status_code=404,
            code=ErrorCodes.CATEGORY_NOT_FOUND,
            message=f"Category with {identifier_type} '{identifier}' was not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            context={"identifier": identifier, "identifier_type": identifier_type},
            correlation_id=correlation_id
        )


class VenueNotFoundError(StandardHTTPException):
    """Exception for venue not found scenarios."""
    
    def __init__(self, venue_id: Union[int, str], correlation_id: Optional[str] = None):
        super().__init__(
            status_code=404,
            code=ErrorCodes.VENUE_NOT_FOUND,
            message=f"Venue with ID {venue_id} was not found",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            context={"venue_id": venue_id},
            correlation_id=correlation_id
        )


class ResourceAlreadyExistsError(StandardHTTPException):
    """Exception for resource conflict scenarios."""
    
    def __init__(
        self, 
        resource_type: str, 
        field: str, 
        value: str, 
        correlation_id: Optional[str] = None
    ):
        super().__init__(
            status_code=400,
            code=ErrorCodes.RESOURCE_ALREADY_EXISTS,
            message=f"{resource_type} with {field} '{value}' already exists",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            context={"resource_type": resource_type, "field": field, "value": value},
            correlation_id=correlation_id
        )


class CannotDeleteReferencedEntityError(StandardHTTPException):
    """Exception for deletion constraint violations."""
    
    def __init__(
        self, 
        entity_type: str, 
        entity_id: Union[int, str], 
        reference_count: int, 
        reference_type: str,
        correlation_id: Optional[str] = None
    ):
        super().__init__(
            status_code=400,
            code=ErrorCodes.CANNOT_DELETE_REFERENCED_ENTITY,
            message=f"Cannot delete {entity_type}. It has {reference_count} associated {reference_type}",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            details=[
                ErrorDetail(
                    code="ENTITY_REFERENCES_EXIST",
                    message=f"This {entity_type} has {reference_count} associated {reference_type}",
                    context={
                        "entity_id": entity_id,
                        "entity_type": entity_type,
                        "reference_count": reference_count,
                        "reference_type": reference_type
                    }
                )
            ],
            correlation_id=correlation_id
        )


class DatabaseOperationError(StandardHTTPException):
    """Exception for database operation failures."""
    
    def __init__(
        self, 
        operation: str, 
        original_error: Optional[Exception] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(
            status_code=500,
            code=ErrorCodes.DATABASE_CONNECTION_ERROR,
            message=f"Database error occurred during {operation}",
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            context={
                "operation": operation,
                "error_type": type(original_error).__name__ if original_error else None
            },
            correlation_id=correlation_id
        )


class ExternalServiceError(StandardHTTPException):
    """Exception for external service failures."""
    
    def __init__(
        self, 
        service_name: str, 
        operation: str,
        original_error: Optional[Exception] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(
            status_code=502,
            code=ErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE,
            message=f"{service_name} service is currently unavailable",
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            context={
                "service_name": service_name,
                "operation": operation,
                "error_type": type(original_error).__name__ if original_error else None
            },
            correlation_id=correlation_id
        )


def create_error_response(
    request: Optional[Request],
    exception: StandardHTTPException,
    include_debug: bool = False
) -> ErrorResponse:
    """Create standardized error response from exception.
    
    Args:
        request: FastAPI request object for context
        exception: Standard HTTP exception to convert
        include_debug: Whether to include debug information
        
    Returns:
        ErrorResponse: Standardized error response model
    """
    return ErrorResponse(
        category=exception.category,
        severity=exception.severity,
        code=exception.code,
        message=exception.message,
        details=exception.details if exception.details else None,
        status_code=exception.status_code,
        path=request.url.path if request else None,
        method=request.method if request else None,
        correlation_id=exception.correlation_id,
        debug_info=exception.context if include_debug else None
    )


def create_validation_error_response(
    request: Optional[Request],
    validation_errors: List[Dict[str, Any]],
    correlation_id: Optional[str] = None
) -> ValidationErrorResponse:
    """Create validation error response from Pydantic validation errors.
    
    Args:
        request: FastAPI request object for context
        validation_errors: List of Pydantic validation errors
        correlation_id: Request correlation ID
        
    Returns:
        ValidationErrorResponse: Specialized validation error response
    """
    details = []
    for error in validation_errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        details.append(ErrorDetail(
            code="FIELD_INVALID",
            message=error.get("msg", "Invalid field value"),
            field=field,
            context={"provided_value": error.get("input")}
        ))
    
    return ValidationErrorResponse(
        code=ErrorCodes.VALIDATION_ERROR,
        message="Request validation failed",
        details=details,
        status_code=422,
        path=request.url.path if request else None,
        method=request.method if request else None,
        correlation_id=correlation_id
    )


def create_internal_server_error_response(
    request: Optional[Request],
    original_error: Exception,
    correlation_id: Optional[str] = None,
    include_debug: bool = False
) -> InternalServerErrorResponse:
    """Create internal server error response.
    
    Args:
        request: FastAPI request object for context
        original_error: Original exception that caused the error
        correlation_id: Request correlation ID
        include_debug: Whether to include debug information
        
    Returns:
        InternalServerErrorResponse: Specialized internal server error response
    """
    # Log the full error for debugging
    logger.error(
        f"Internal server error: {str(original_error)}",
        exc_info=True,
        extra={"correlation_id": correlation_id}
    )
    
    debug_info = None
    if include_debug:
        debug_info = {
            "error_type": type(original_error).__name__,
            "error_message": str(original_error),
            "traceback": traceback.format_exc()
        }
    
    return InternalServerErrorResponse(
        code=ErrorCodes.INTERNAL_SERVER_ERROR,
        message="An internal error occurred while processing your request",
        status_code=500,
        path=request.url.path if request else None,
        method=request.method if request else None,
        correlation_id=correlation_id,
        debug_info=debug_info
    )


def get_correlation_id(request: Request) -> str:
    """Extract or generate correlation ID for request tracing.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Correlation ID for request tracing
    """
    # Try to get correlation ID from headers
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        # Generate new correlation ID if not provided
        import uuid
        correlation_id = str(uuid.uuid4())
    
    return correlation_id


def log_error_context(
    correlation_id: str,
    error: Exception,
    request: Optional[Request] = None,
    additional_context: Optional[Dict[str, Any]] = None
):
    """Log error with full context for debugging and monitoring.
    
    Args:
        correlation_id: Request correlation ID
        error: Exception that occurred
        request: FastAPI request object
        additional_context: Additional context information
    """
    context = {
        "correlation_id": correlation_id,
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    
    if request:
        context.update({
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        })
    
    if additional_context:
        context.update(additional_context)
    
    logger.error(f"Error occurred: {str(error)}", extra=context, exc_info=True)