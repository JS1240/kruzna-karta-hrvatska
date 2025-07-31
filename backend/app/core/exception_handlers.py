"""
FastAPI exception handlers for centralized error processing.

This module provides FastAPI exception handlers that automatically convert
exceptions into standardized error responses, ensuring consistent error
handling across all API endpoints.
"""

import logging
from typing import Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error_handlers import (
    StandardHTTPException,
    DatabaseOperationError,
    create_error_response,
    create_validation_error_response,
    create_internal_server_error_response,
    get_correlation_id,
    log_error_context
)
from app.models.error_schemas import ErrorCategory, ErrorSeverity, ErrorCodes

logger = logging.getLogger(__name__)


async def standard_http_exception_handler(
    request: Request, 
    exc: StandardHTTPException
) -> JSONResponse:
    """Handler for StandardHTTPException with structured error responses.
    
    Args:
        request: FastAPI request object
        exc: StandardHTTPException to handle
        
    Returns:
        JSONResponse: Standardized error response
    """
    # Get or generate correlation ID
    correlation_id = exc.correlation_id or get_correlation_id(request)
    exc.correlation_id = correlation_id
    
    # Log error context
    log_error_context(correlation_id, exc, request)
    
    # Create structured error response
    error_response = create_error_response(
        request=request,
        exception=exc,
        include_debug=False  # TODO: Make configurable based on environment
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


async def starlette_http_exception_handler(
    request: Request, 
    exc: StarletteHTTPException
) -> JSONResponse:
    """Handler for standard Starlette HTTPException.
    
    Converts standard HTTP exceptions to standardized error responses.
    
    Args:
        request: FastAPI request object  
        exc: Starlette HTTPException to handle
        
    Returns:
        JSONResponse: Standardized error response
    """
    correlation_id = get_correlation_id(request)
    
    # Convert to StandardHTTPException for consistent handling
    standard_exc = StandardHTTPException(
        status_code=exc.status_code,
        code=ErrorCodes.INVALID_REQUEST,
        message=str(exc.detail),
        correlation_id=correlation_id
    )
    
    return await standard_http_exception_handler(request, standard_exc)


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """Handler for Pydantic validation errors.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSONResponse: Structured validation error response
    """
    correlation_id = get_correlation_id(request)
    
    # Log validation error
    log_error_context(
        correlation_id=correlation_id,
        error=exc,
        request=request,
        additional_context={"validation_errors": exc.errors()}
    )
    
    # Create validation error response
    error_response = create_validation_error_response(
        request=request,
        validation_errors=exc.errors(),
        correlation_id=correlation_id
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


async def sqlalchemy_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """Handler for SQLAlchemy database errors.
    
    Args:
        request: FastAPI request object
        exc: SQLAlchemy exception
        
    Returns:
        JSONResponse: Standardized database error response
    """
    correlation_id = get_correlation_id(request)
    
    # Log database error with context
    log_error_context(
        correlation_id=correlation_id,
        error=exc,
        request=request,
        additional_context={"database_error": True}
    )
    
    # Determine specific error type and status code
    if isinstance(exc, IntegrityError):
        # Database constraint violations
        db_error = StandardHTTPException(
            status_code=400,
            code=ErrorCodes.DATABASE_TRANSACTION_ERROR,
            message="Database constraint violation occurred",
            category=ErrorCategory.BUSINESS_LOGIC,
            severity=ErrorSeverity.MEDIUM,
            correlation_id=correlation_id
        )
    elif isinstance(exc, OperationalError):
        # Database connection or operational issues
        db_error = DatabaseOperationError(
            operation="database query",
            original_error=exc,
            correlation_id=correlation_id
        )
    else:
        # Generic database errors
        db_error = DatabaseOperationError(
            operation="database operation",
            original_error=exc,
            correlation_id=correlation_id
        )
    
    return await standard_http_exception_handler(request, db_error)


async def generic_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """Handler for unhandled exceptions.
    
    Catches all unhandled exceptions and converts them to standardized
    internal server error responses.
    
    Args:
        request: FastAPI request object
        exc: Unhandled exception
        
    Returns:
        JSONResponse: Standardized internal server error response
    """
    correlation_id = get_correlation_id(request)
    
    # Create internal server error response
    error_response = create_internal_server_error_response(
        request=request,
        original_error=exc,
        correlation_id=correlation_id,
        include_debug=False  # TODO: Make configurable based on environment
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Setup all exception handlers for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Standard HTTP exceptions (our custom ones)
    app.add_exception_handler(StandardHTTPException, standard_http_exception_handler)
    
    # Starlette HTTP exceptions (built-in FastAPI)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # SQLAlchemy database errors
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("Exception handlers configured successfully")


# Middleware for adding correlation ID to request context
async def correlation_id_middleware(request: Request, call_next):
    """Middleware to add correlation ID to request context.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/endpoint in chain
        
    Returns:
        Response with correlation ID header
    """
    # Get or generate correlation ID
    correlation_id = get_correlation_id(request)
    
    # Add correlation ID to request state for access in route handlers
    request.state.correlation_id = correlation_id
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response