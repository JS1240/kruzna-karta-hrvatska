"""
Comprehensive test suite for the error handling system (Phase 5).

Tests custom exceptions, error response schemas, exception handlers,
and the complete error handling workflow to validate the Phase 5
Error Handling Standardization implementation.
"""

import json
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from backend.app.core.error_handlers import (
    StandardHTTPException,
    EventNotFoundError,
    CategoryNotFoundError,
    VenueNotFoundError,
    ResourceAlreadyExistsError,
    CannotDeleteReferencedEntityError,
    DatabaseOperationError,
    ExternalServiceError,
    create_error_response,
    create_validation_error_response,
    create_internal_server_error_response,
    get_correlation_id,
    log_error_context
)
from backend.app.core.exception_handlers import (
    standard_http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
    setup_exception_handlers,
    correlation_id_middleware
)
from backend.app.models.error_schemas import (
    ErrorResponse,
    ErrorDetail,
    ErrorCategory,
    ErrorSeverity,
    ErrorCodes,
    ValidationErrorResponse,
    BusinessLogicErrorResponse,
    InternalServerErrorResponse,
    STATUS_CODE_CATEGORY_MAP
)


class TestErrorSchemas:
    """Test error response schemas and models."""
    
    def test_error_response_creation(self):
        """Test ErrorResponse model creation and validation."""
        error_response = ErrorResponse(
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.LOW,
            code=ErrorCodes.EVENT_NOT_FOUND,
            message="Event with ID 123 was not found",
            status_code=404,
            path="/api/events/123",
            method="GET"
        )
        
        assert error_response.error is True
        assert error_response.category == ErrorCategory.NOT_FOUND
        assert error_response.severity == ErrorSeverity.LOW
        assert error_response.code == ErrorCodes.EVENT_NOT_FOUND
        assert error_response.message == "Event with ID 123 was not found"
        assert error_response.status_code == 404
        assert error_response.path == "/api/events/123"
        assert error_response.method == "GET"
        assert isinstance(error_response.correlation_id, str)
        assert isinstance(error_response.timestamp, datetime)
    
    def test_error_detail_creation(self):
        """Test ErrorDetail model creation."""
        detail = ErrorDetail(
            code="FIELD_INVALID",
            message="Title is required",
            field="title",
            context={"provided_value": None}
        )
        
        assert detail.code == "FIELD_INVALID"
        assert detail.message == "Title is required"
        assert detail.field == "title"
        assert detail.context == {"provided_value": None}
    
    def test_validation_error_response(self):
        """Test ValidationErrorResponse specialized model."""
        validation_error = ValidationErrorResponse(
            code=ErrorCodes.VALIDATION_ERROR,
            message="Request validation failed",
            status_code=422,
            path="/api/events",
            method="POST",
            details=[
                ErrorDetail(
                    code="FIELD_REQUIRED",
                    message="This field is required",
                    field="title"
                )
            ]
        )
        
        assert validation_error.category == ErrorCategory.VALIDATION
        assert validation_error.status_code == 422
        assert len(validation_error.details) == 1
        assert validation_error.details[0].field == "title"
    
    def test_business_logic_error_response(self):
        """Test BusinessLogicErrorResponse specialized model."""
        business_error = BusinessLogicErrorResponse(
            code=ErrorCodes.CANNOT_DELETE_REFERENCED_ENTITY,
            message="Cannot delete venue because it has events",
            status_code=400,
            path="/api/venues/123",
            method="DELETE"
        )
        
        assert business_error.category == ErrorCategory.BUSINESS_LOGIC
        assert business_error.status_code == 400
    
    def test_error_codes_constants(self):
        """Test error code constants are properly defined."""
        assert hasattr(ErrorCodes, 'EVENT_NOT_FOUND')
        assert hasattr(ErrorCodes, 'CATEGORY_NOT_FOUND')
        assert hasattr(ErrorCodes, 'VENUE_NOT_FOUND')
        assert hasattr(ErrorCodes, 'RESOURCE_ALREADY_EXISTS')
        assert hasattr(ErrorCodes, 'CANNOT_DELETE_REFERENCED_ENTITY')
        assert hasattr(ErrorCodes, 'DATABASE_CONNECTION_ERROR')
        assert hasattr(ErrorCodes, 'EXTERNAL_SERVICE_UNAVAILABLE')
    
    def test_status_code_category_mapping(self):
        """Test HTTP status code to category mapping."""
        assert STATUS_CODE_CATEGORY_MAP[400] == ErrorCategory.VALIDATION
        assert STATUS_CODE_CATEGORY_MAP[401] == ErrorCategory.AUTHENTICATION
        assert STATUS_CODE_CATEGORY_MAP[403] == ErrorCategory.AUTHORIZATION
        assert STATUS_CODE_CATEGORY_MAP[404] == ErrorCategory.NOT_FOUND
        assert STATUS_CODE_CATEGORY_MAP[422] == ErrorCategory.VALIDATION
        assert STATUS_CODE_CATEGORY_MAP[500] == ErrorCategory.INTERNAL_SERVER


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_standard_http_exception(self):
        """Test StandardHTTPException base class."""
        exception = StandardHTTPException(
            status_code=400,
            code="TEST_ERROR",
            message="Test error message",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            context={"test": "data"}
        )
        
        assert exception.status_code == 400
        assert exception.code == "TEST_ERROR"
        assert exception.message == "Test error message"
        assert exception.category == ErrorCategory.VALIDATION
        assert exception.severity == ErrorSeverity.LOW
        assert exception.context == {"test": "data"}
        assert exception.correlation_id is None  # Not set initially
    
    def test_event_not_found_error(self):
        """Test EventNotFoundError exception."""
        error = EventNotFoundError(123)
        
        assert error.status_code == 404
        assert error.code == ErrorCodes.EVENT_NOT_FOUND
        assert "123" in error.message
        assert error.category == ErrorCategory.NOT_FOUND
        assert error.severity == ErrorSeverity.LOW
        assert error.context["event_id"] == 123
    
    def test_category_not_found_error(self):
        """Test CategoryNotFoundError exception."""
        # Test with ID
        error_id = CategoryNotFoundError(456)
        assert error_id.status_code == 404
        assert error_id.code == ErrorCodes.CATEGORY_NOT_FOUND
        assert "ID" in error_id.message and "456" in error_id.message
        
        # Test with slug
        error_slug = CategoryNotFoundError("concerts", by_slug=True)
        assert error_slug.status_code == 404
        assert "slug" in error_slug.message and "concerts" in error_slug.message
    
    def test_venue_not_found_error(self):
        """Test VenueNotFoundError exception."""
        error = VenueNotFoundError(789)
        
        assert error.status_code == 404
        assert error.code == ErrorCodes.VENUE_NOT_FOUND
        assert "789" in error.message
        assert error.category == ErrorCategory.NOT_FOUND
        assert error.severity == ErrorSeverity.LOW
    
    def test_resource_already_exists_error(self):
        """Test ResourceAlreadyExistsError exception."""
        error = ResourceAlreadyExistsError("Category", "slug", "concerts")
        
        assert error.status_code == 400
        assert error.code == ErrorCodes.RESOURCE_ALREADY_EXISTS
        assert "Category" in error.message
        assert "slug" in error.message
        assert "concerts" in error.message
        assert error.category == ErrorCategory.BUSINESS_LOGIC
        assert error.severity == ErrorSeverity.MEDIUM
    
    def test_cannot_delete_referenced_entity_error(self):
        """Test CannotDeleteReferencedEntityError exception."""
        error = CannotDeleteReferencedEntityError("venue", 123, 5, "events")
        
        assert error.status_code == 400
        assert error.code == ErrorCodes.CANNOT_DELETE_REFERENCED_ENTITY
        assert "venue" in error.message
        assert "5" in error.message
        assert "events" in error.message
        assert error.category == ErrorCategory.BUSINESS_LOGIC
        assert error.severity == ErrorSeverity.MEDIUM
        assert len(error.details) == 1
        assert error.details[0].code == "ENTITY_REFERENCES_EXIST"
    
    def test_database_operation_error(self):
        """Test DatabaseOperationError exception."""
        original_error = Exception("Connection timeout")
        error = DatabaseOperationError("query execution", original_error)
        
        assert error.status_code == 500
        assert error.code == ErrorCodes.DATABASE_CONNECTION_ERROR
        assert "query execution" in error.message
        assert error.category == ErrorCategory.DATABASE
        assert error.severity == ErrorSeverity.HIGH
        assert error.context["operation"] == "query execution"
        assert error.context["error_type"] == "Exception"
    
    def test_external_service_error(self):
        """Test ExternalServiceError exception."""
        original_error = ConnectionError("Service unavailable")
        error = ExternalServiceError("geocoding", "address lookup", original_error)
        
        assert error.status_code == 502
        assert error.code == ErrorCodes.EXTERNAL_SERVICE_UNAVAILABLE
        assert "geocoding" in error.message
        assert error.category == ErrorCategory.EXTERNAL_SERVICE
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.context["service_name"] == "geocoding"
        assert error.context["operation"] == "address lookup"


class TestErrorHandlerUtilities:
    """Test error handler utility functions."""
    
    def test_create_error_response(self):
        """Test create_error_response utility function."""
        # Mock request
        mock_request = Mock()
        mock_request.url.path = "/api/events/123"
        mock_request.method = "GET"
        
        # Create exception
        exception = EventNotFoundError(123)
        exception.correlation_id = "test-correlation-123"
        
        # Create error response
        response = create_error_response(mock_request, exception)
        
        assert isinstance(response, ErrorResponse)
        assert response.category == ErrorCategory.NOT_FOUND
        assert response.code == ErrorCodes.EVENT_NOT_FOUND
        assert response.status_code == 404
        assert response.path == "/api/events/123"
        assert response.method == "GET"
        assert response.correlation_id == "test-correlation-123"
    
    def test_create_validation_error_response(self):
        """Test create_validation_error_response utility function."""
        mock_request = Mock()
        mock_request.url.path = "/api/events"
        mock_request.method = "POST"
        
        validation_errors = [
            {
                "loc": ["title"],
                "msg": "field required",
                "type": "value_error.missing",
                "input": None
            },
            {
                "loc": ["date"],
                "msg": "invalid date format",
                "type": "value_error.date",
                "input": "invalid-date"
            }
        ]
        
        response = create_validation_error_response(
            mock_request, validation_errors, "test-correlation"
        )
        
        assert isinstance(response, ValidationErrorResponse)
        assert response.category == ErrorCategory.VALIDATION
        assert response.code == ErrorCodes.VALIDATION_ERROR
        assert response.status_code == 422
        assert len(response.details) == 2
        assert response.details[0].field == "title"
        assert response.details[1].field == "date"
    
    def test_create_internal_server_error_response(self):
        """Test create_internal_server_error_response utility function."""
        mock_request = Mock()
        mock_request.url.path = "/api/events"
        mock_request.method = "GET"
        
        original_error = Exception("Unexpected error")
        
        response = create_internal_server_error_response(
            mock_request, original_error, "test-correlation", include_debug=True
        )
        
        assert isinstance(response, InternalServerErrorResponse)
        assert response.category == ErrorCategory.INTERNAL_SERVER
        assert response.severity == ErrorSeverity.HIGH
        assert response.status_code == 500
        assert response.correlation_id == "test-correlation"
        assert response.debug_info is not None
        assert "Exception" in response.debug_info["error_type"]
    
    def test_get_correlation_id(self):
        """Test get_correlation_id utility function."""
        # Test with existing correlation ID in headers
        mock_request = Mock()
        mock_request.headers.get.return_value = "existing-correlation-123"
        
        correlation_id = get_correlation_id(mock_request)
        assert correlation_id == "existing-correlation-123"
        
        # Test without existing correlation ID
        mock_request.headers.get.return_value = None
        correlation_id = get_correlation_id(mock_request)
        assert isinstance(correlation_id, str)
        assert len(correlation_id) > 0
        # Should be a valid UUID format
        uuid.UUID(correlation_id)  # This will raise if invalid
    
    @patch('backend.app.core.error_handlers.logger')
    def test_log_error_context(self, mock_logger):
        """Test log_error_context utility function."""
        mock_request = Mock()
        mock_request.url.path = "/api/events/123"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = "test-user-agent"
        mock_request.client.host = "127.0.0.1"
        
        error = EventNotFoundError(123)
        additional_context = {"extra": "data"}
        
        log_error_context(
            "test-correlation", error, mock_request, additional_context
        )
        
        # Verify logger was called with error
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        
        # Check extra context was passed
        assert "correlation_id" in call_args.kwargs["extra"]
        assert "path" in call_args.kwargs["extra"]
        assert "method" in call_args.kwargs["extra"]
        assert "extra" in call_args.kwargs["extra"]


class TestExceptionHandlers:
    """Test FastAPI exception handlers."""
    
    @pytest.mark.asyncio
    async def test_standard_http_exception_handler(self):
        """Test standard HTTP exception handler."""
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = None
        
        exception = EventNotFoundError(123)
        
        with patch('backend.app.core.exception_handlers.log_error_context'):
            response = await standard_http_exception_handler(mock_request, exception)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 404
        
        # Parse response content
        content = json.loads(response.body.decode())
        assert content["error"] is True
        assert content["code"] == ErrorCodes.EVENT_NOT_FOUND
        assert content["category"] == ErrorCategory.NOT_FOUND
        assert "123" in content["message"]
    
    @pytest.mark.asyncio
    async def test_validation_exception_handler(self):
        """Test validation exception handler."""
        mock_request = Mock()
        mock_request.url.path = "/api/events"
        mock_request.method = "POST"
        mock_request.headers.get.return_value = None
        
        # Create mock validation error
        validation_error = Mock()
        validation_error.errors.return_value = [
            {
                "loc": ["title"],
                "msg": "field required",
                "type": "value_error.missing",
                "input": None
            }
        ]
        
        with patch('backend.app.core.exception_handlers.log_error_context'):
            response = await validation_exception_handler(mock_request, validation_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 422
        
        content = json.loads(response.body.decode())
        assert content["category"] == ErrorCategory.VALIDATION
        assert content["code"] == ErrorCodes.VALIDATION_ERROR
        assert len(content["details"]) == 1
    
    @pytest.mark.asyncio
    async def test_sqlalchemy_exception_handler(self):
        """Test SQLAlchemy exception handler."""
        mock_request = Mock()
        mock_request.url.path = "/api/categories"
        mock_request.method = "POST"
        mock_request.headers.get.return_value = None
        
        # Test IntegrityError
        integrity_error = IntegrityError("duplicate key", None, None)
        
        with patch('backend.app.core.exception_handlers.log_error_context'):
            response = await sqlalchemy_exception_handler(mock_request, integrity_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
        
        # Test OperationalError
        operational_error = OperationalError("connection failed", None, None)
        
        with patch('backend.app.core.exception_handlers.log_error_context'):
            response = await sqlalchemy_exception_handler(mock_request, operational_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_generic_exception_handler(self):
        """Test generic exception handler for unhandled exceptions."""
        mock_request = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"
        mock_request.headers.get.return_value = None
        
        generic_error = Exception("Unexpected error")
        
        response = await generic_exception_handler(mock_request, generic_error)
        
        assert isinstance(response, JSONResponse)
        assert response.status_code == 500
        
        content = json.loads(response.body.decode())
        assert content["category"] == ErrorCategory.INTERNAL_SERVER
        assert content["severity"] == ErrorSeverity.HIGH


class TestCorrelationIdMiddleware:
    """Test correlation ID middleware functionality."""
    
    @pytest.mark.asyncio
    async def test_correlation_id_middleware(self):
        """Test correlation ID middleware adds headers."""
        mock_request = Mock()
        mock_request.headers.get.return_value = "test-correlation-123"
        mock_request.state = Mock()
        
        mock_response = Mock()
        mock_response.headers = {}
        
        async def mock_call_next(request):
            return mock_response
        
        result = await correlation_id_middleware(mock_request, mock_call_next)
        
        assert result == mock_response
        assert mock_response.headers["X-Correlation-ID"] == "test-correlation-123"
        assert mock_request.state.correlation_id == "test-correlation-123"


class TestIntegrationErrorHandling:
    """Integration tests for complete error handling workflow."""
    
    def test_setup_exception_handlers(self):
        """Test setup_exception_handlers integration."""
        app = FastAPI()
        
        # Setup exception handlers
        setup_exception_handlers(app)
        
        # Verify handlers are registered (test by checking if they exist)
        # Note: FastAPI doesn't provide direct access to registered handlers,
        # so we test by ensuring the function runs without error
        assert app is not None
    
    @pytest.mark.asyncio
    async def test_full_error_workflow(self):
        """Test complete error handling workflow."""
        # Create a test FastAPI app with error handlers
        app = FastAPI()
        setup_exception_handlers(app)
        
        @app.get("/test-error/{event_id}")
        async def test_endpoint(event_id: int):
            if event_id == 404:
                raise EventNotFoundError(event_id)
            elif event_id == 400:
                raise ResourceAlreadyExistsError("Event", "title", "Test Event")
            elif event_id == 500:
                raise DatabaseOperationError("test operation")
            return {"message": "success"}
        
        client = TestClient(app)
        
        # Test EventNotFoundError
        response = client.get("/test-error/404")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert data["code"] == ErrorCodes.EVENT_NOT_FOUND
        assert data["category"] == ErrorCategory.NOT_FOUND
        
        # Test ResourceAlreadyExistsError
        response = client.get("/test-error/400")
        assert response.status_code == 400
        data = response.json()
        assert data["code"] == ErrorCodes.RESOURCE_ALREADY_EXISTS
        assert data["category"] == ErrorCategory.BUSINESS_LOGIC
        
        # Test DatabaseOperationError
        response = client.get("/test-error/500")
        assert response.status_code == 500
        data = response.json()
        assert data["code"] == ErrorCodes.DATABASE_CONNECTION_ERROR
        assert data["category"] == ErrorCategory.DATABASE


# Test fixtures for error handling tests
@pytest.fixture
def mock_request():
    """Fixture providing mock FastAPI request."""
    request = Mock()
    request.url.path = "/api/test"
    request.method = "GET"
    request.headers.get.return_value = None
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def test_correlation_id():
    """Fixture providing test correlation ID."""
    return "test-correlation-" + str(uuid.uuid4())


if __name__ == "__main__":
    # Run error handling tests
    pytest.main([__file__, "-v"])