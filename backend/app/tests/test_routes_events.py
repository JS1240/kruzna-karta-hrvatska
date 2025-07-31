"""
Comprehensive test suite for events API routes.

Tests all endpoints in routes/events.py with request/response validation,
error handling, authentication, and business logic validation using
the established excellent testing patterns.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.error_handlers import (
    DatabaseOperationError
)
from backend.app.models.schemas import EventCreate


class TestEventsRoutes:
    """Test events API routes."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session fixture."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_event_data(self):
        """Sample event data for testing."""
        return {
            "title": "Test Concert",
            "description": "A test concert event",
            "date": "2024-06-15",
            "time": "20:00",
            "location": "Test Venue, Zagreb",
            "source": "test",
            "price": "50 EUR",
            "organizer": "Test Organizer",
            "category_id": 1,
            "venue_id": 1
        }
    
    @pytest.fixture
    def sample_event_response(self):
        """Sample event response data."""
        return {
            "id": 1,
            "title": "Test Concert",
            "description": "A test concert event",
            "date": "2024-06-15",
            "time": "20:00",
            "location": "Test Venue, Zagreb",
            "source": "test",
            "price": "50 EUR",
            "organizer": "Test Organizer",
            "category_id": 1,
            "venue_id": 1,
            "latitude": None,
            "longitude": None,
            "view_count": 0,
            "is_featured": False,
            "event_status": "active",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }


class TestGetEvents:
    """Test GET /api/events/ endpoint."""
    
    def test_get_events_success(self, client):
        """Test successful events retrieval."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [{"id": 1, "title": "Test Event"}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/events/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "events" in data
            assert "total" in data
            assert data["total"] == 1
    
    def test_get_events_with_pagination(self, client):
        """Test events retrieval with pagination parameters."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [],
                "total": 100,
                "page": 2,
                "size": 10,
                "pages": 10
            }
            
            response = client.get("/api/events/?page=2&size=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["page"] == 2
            assert data["size"] == 10
    
    def test_get_events_with_search_query(self, client):
        """Test events retrieval with search query."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [{"id": 1, "title": "Concert Event"}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/events/?q=concert")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify search parameters were passed correctly
            call_args = mock_search.call_args
            search_params = call_args[0][0]
            assert hasattr(search_params, 'q')
    
    def test_get_events_with_filters(self, client):
        """Test events retrieval with category and venue filters."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0
            }
            
            response = client.get("/api/events/?category_id=1&venue_id=2&city=Zagreb")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_events_with_date_range(self, client):
        """Test events retrieval with date range filters."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0
            }
            
            response = client.get("/api/events/?date_from=2024-06-01&date_to=2024-06-30")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_events_with_geographic_search(self, client):
        """Test events retrieval with geographic parameters."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0
            }
            
            response = client.get("/api/events/?latitude=45.815&longitude=15.982&radius_km=10")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_events_database_error(self, client):
        """Test events retrieval with database error."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.side_effect = DatabaseOperationError("query execution")
            
            response = client.get("/api/events/")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] is True
            assert data["category"] == "database"


class TestGetFeaturedEvents:
    """Test GET /api/events/featured endpoint."""
    
    def test_get_featured_events_success(self, client):
        """Test successful featured events retrieval."""
        with patch('backend.app.routes.events._safe_get_featured_events') as mock_featured:
            mock_featured.return_value = {
                "events": [{"id": 1, "title": "Featured Event", "is_featured": True}],
                "total": 1,
                "page": 1,
                "size": 10,
                "pages": 1
            }
            
            response = client.get("/api/events/featured")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["events"]) == 1
            assert data["events"][0]["is_featured"] is True
    
    def test_get_featured_events_with_pagination(self, client):
        """Test featured events with pagination."""
        with patch('backend.app.routes.events._safe_get_featured_events') as mock_featured:
            mock_featured.return_value = {
                "events": [],
                "total": 0,
                "page": 2,
                "size": 5,
                "pages": 0
            }
            
            response = client.get("/api/events/featured?page=2&size=5")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["page"] == 2
            assert data["size"] == 5


class TestSearchEvents:
    """Test GET /api/events/search endpoint."""
    
    def test_search_events_success(self, client):
        """Test successful events search."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [{"id": 1, "title": "Concert in Zagreb"}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/events/search?q=concert&city=Zagreb")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["events"]) == 1
    
    def test_search_events_complex_query(self, client):
        """Test search with complex query parameters."""
        with patch('backend.app.routes.events._safe_search_events') as mock_search:
            mock_search.return_value = {
                "events": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0
            }
            
            query_params = {
                "q": "music festival",
                "category_id": "1",
                "city": "Split",
                "date_from": "2024-07-01",
                "date_to": "2024-07-31",
                "is_featured": "true",
                "page": "1",
                "size": "10"
            }
            
            response = client.get("/api/events/search", params=query_params)
            
            assert response.status_code == status.HTTP_200_OK


class TestGetNearbyEvents:
    """Test GET /api/events/nearby endpoint."""
    
    def test_get_nearby_events_success(self, client):
        """Test successful nearby events retrieval."""
        with patch('backend.app.routes.events.get_events') as mock_get_events:
            mock_get_events.return_value = {
                "events": [{"id": 1, "title": "Nearby Event"}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/events/nearby?latitude=45.815&longitude=15.982")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["events"]) == 1
    
    def test_get_nearby_events_with_radius(self, client):
        """Test nearby events with custom radius."""
        with patch('backend.app.routes.events.get_events') as mock_get_events:
            mock_get_events.return_value = {
                "events": [],
                "total": 0,
                "page": 1,
                "size": 20,
                "pages": 0
            }
            
            response = client.get("/api/events/nearby?latitude=45.815&longitude=15.982&radius_km=25")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_nearby_events_missing_coordinates(self, client):
        """Test nearby events with missing coordinates."""
        response = client.get("/api/events/nearby")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"


class TestGetSpecificEvent:
    """Test GET /api/events/{event_id} endpoint."""
    
    def test_get_event_success(self, client):
        """Test successful single event retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock event
            mock_event = Mock()
            mock_event.id = 1
            mock_event.title = "Test Event"
            mock_event.view_count = 5
            
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_event
            
            response = client.get("/api/events/1")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify view count was incremented
            assert mock_event.view_count == 6
            mock_db.commit.assert_called_once()
    
    def test_get_event_not_found(self, client):
        """Test event not found scenario."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock no event found
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/events/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "EVENT_NOT_FOUND"
            assert "99999" in data["message"]
    
    def test_get_event_with_language(self, client):
        """Test event retrieval with language parameter."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 1
            mock_event.view_count = 0
            
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_event
            
            response = client.get("/api/events/1?language=en")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_event_with_accept_language_header(self, client):
        """Test event retrieval with Accept-Language header."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 1
            mock_event.view_count = 0
            
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_event
            
            headers = {"Accept-Language": "hr,en;q=0.9"}
            response = client.get("/api/events/1", headers=headers)
            
            assert response.status_code == status.HTTP_200_OK


class TestGetEventBySlug:
    """Test GET /api/events/slug/{slug} endpoint."""
    
    def test_get_event_by_slug_success(self, client):
        """Test successful event retrieval by slug."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 1
            mock_event.slug = "test-event"
            mock_event.view_count = 10
            
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = mock_event
            
            response = client.get("/api/events/slug/test-event")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify view count was incremented
            assert mock_event.view_count == 11
    
    def test_get_event_by_slug_not_found(self, client):
        """Test event by slug not found scenario."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.options.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/events/slug/nonexistent-event")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "EVENT_NOT_FOUND"


class TestCreateEvent:
    """Test POST /api/events/ endpoint."""
    
    def test_create_event_success(self, client, sample_event_data):
        """Test successful event creation."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock successful creation
            mock_event = Mock()
            mock_event.id = 1
            mock_event.title = sample_event_data["title"]
            
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            response = client.post("/api/events/", json=sample_event_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_create_event_validation_error(self, client):
        """Test event creation with validation errors."""
        invalid_data = {
            "title": "",  # Empty title
            "date": "invalid-date",  # Invalid date format
            "time": "25:00"  # Invalid time
        }
        
        response = client.post("/api/events/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        assert "details" in data
    
    def test_create_event_missing_required_fields(self, client):
        """Test event creation with missing required fields."""
        incomplete_data = {
            "title": "Test Event"
            # Missing other required fields
        }
        
        response = client.post("/api/events/", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateEvent:
    """Test PUT /api/events/{event_id} endpoint."""
    
    def test_update_event_success(self, client):
        """Test successful event update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock existing event
            mock_event = Mock()
            mock_event.id = 1
            mock_event.title = "Old Title"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_event
            
            update_data = {
                "title": "New Title",
                "description": "Updated description"
            }
            
            response = client.put("/api/events/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.commit.assert_called_once()
    
    def test_update_event_not_found(self, client):
        """Test updating non-existent event."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            update_data = {"title": "New Title"}
            
            response = client.put("/api/events/99999", json=update_data)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "EVENT_NOT_FOUND"
    
    def test_update_event_partial_update(self, client):
        """Test partial event update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 1
            mock_event.title = "Original Title"
            mock_event.price = "100 EUR"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_event
            
            # Only update price
            update_data = {"price": "120 EUR"}
            
            response = client.put("/api/events/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK


class TestDeleteEvent:
    """Test DELETE /api/events/{event_id} endpoint."""
    
    def test_delete_event_success(self, client):
        """Test successful event deletion."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 1
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_event
            
            response = client.delete("/api/events/1")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Event deleted successfully"
            mock_db.delete.assert_called_once_with(mock_event)
            mock_db.commit.assert_called_once()
    
    def test_delete_event_not_found(self, client):
        """Test deleting non-existent event."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.delete("/api/events/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "EVENT_NOT_FOUND"


class TestGeocodingEndpoints:
    """Test geocoding-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_geocode_events_success(self, client):
        """Test successful event geocoding."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.core.geocoding_service.geocoding_service.batch_geocode_venues') as mock_geocode:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock events without coordinates
            mock_event = Mock()
            mock_event.id = 1
            mock_event.location = "Zagreb, Croatia"
            mock_event.latitude = None
            mock_event.longitude = None
            
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_event]
            
            # Mock geocoding results
            mock_geocode.return_value = {
                "Zagreb, Croatia": Mock(latitude=45.815, longitude=15.982, confidence=0.9, accuracy="city")
            }
            
            response = client.post("/api/events/geocode?limit=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["geocoded_count"] == 1
            assert "geocoding_results" in data
    
    def test_geocode_events_no_events(self, client):
        """Test geocoding when no events need geocoding."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # No events without coordinates
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
            
            response = client.post("/api/events/geocode")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["geocoded_count"] == 0
            assert "No events found" in data["message"]
    
    @pytest.mark.asyncio
    async def test_geocode_events_service_error(self, client):
        """Test geocoding with external service error."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.core.geocoding_service.geocoding_service.batch_geocode_venues') as mock_geocode:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.location = "Test Location"
            mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = [mock_event]
            
            # Mock geocoding service error
            mock_geocode.side_effect = Exception("Geocoding service unavailable")
            
            response = client.post("/api/events/geocode")
            
            assert response.status_code == status.HTTP_502_BAD_GATEWAY
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "EXTERNAL_SERVICE_UNAVAILABLE"


class TestHealthAndStatusEndpoints:
    """Test health and status endpoints."""
    
    def test_get_geocoding_status(self, client):
        """Test geocoding status endpoint."""
        with patch('backend.app.routes.events.safe_db_operation') as mock_safe_db:
            mock_safe_db.return_value = {
                "total_events": 100,
                "events_with_coordinates": 80,
                "events_need_geocoding": 15,
                "events_without_location": 5,
                "geocoding_percentage": 80.0
            }
            
            response = client.get("/api/events/geocoding-status/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_events"] == 100
            assert data["geocoding_percentage"] == 80.0
    
    def test_get_database_health(self, client):
        """Test database health endpoint."""
        with patch('backend.app.routes.events.health_check_db') as mock_health:
            mock_health.return_value = {
                "status": "healthy",
                "database_connected": True,
                "connectivity": "ok"
            }
            
            response = client.get("/api/events/db-health/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "healthy"
    
    def test_database_health_error(self, client):
        """Test database health with error."""
        with patch('backend.app.routes.events.health_check_db') as mock_health:
            mock_health.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/events/db-health/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "error"
            assert "error" in data
    
    def test_reset_database_pool_success(self, client):
        """Test database pool reset success."""
        with patch('backend.app.routes.events.reset_database_connections') as mock_reset:
            mock_reset.return_value = True
            
            response = client.post("/api/events/db-reset/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "success"
    
    def test_reset_database_pool_failure(self, client):
        """Test database pool reset failure."""
        with patch('backend.app.routes.events.reset_database_connections') as mock_reset:
            mock_reset.return_value = False
            
            response = client.post("/api/events/db-reset/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["status"] == "failed"
    
    def test_reset_database_pool_error(self, client):
        """Test database pool reset with exception."""
        with patch('backend.app.routes.events.reset_database_connections') as mock_reset:
            mock_reset.side_effect = Exception("Reset failed")
            
            response = client.post("/api/events/db-reset/")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "DATABASE_CONNECTION_ERROR"


class TestDataIntegrityEndpoints:
    """Test data integrity and debugging endpoints."""
    
    def test_debug_coordinates(self, client):
        """Test debug coordinates endpoint."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_event = Mock()
            mock_event.id = 7
            mock_event.title = "Test Event"
            mock_event.latitude = Decimal("45.815")
            mock_event.longitude = Decimal("15.982")
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_event
            
            response = client.get("/api/events/debug-coordinates/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["event_id"] == 7
            assert data["latitude_type"] == "Decimal"
            assert data["latitude_float"] == 45.815
    
    def test_debug_coordinates_not_found(self, client):
        """Test debug coordinates with no event."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/events/debug-coordinates/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "error" in data
            assert data["error"] == "Event not found"
    
    def test_check_data_integrity(self, client):
        """Test data integrity check endpoint."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.routes.events._safe_search_events') as mock_search:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock integrity check queries
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            mock_db.query.return_value.count.return_value = 100
            mock_db.execute.return_value.scalar.return_value = 1
            
            # Mock API test
            mock_search.return_value = Mock(events=[Mock(latitude=45.0)])
            
            response = client.get("/api/events/data-integrity/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "status" in data
            assert "total_events" in data
            assert "checks_performed" in data


# Additional test utilities and fixtures
@pytest.fixture
def mock_event_create():
    """Create mock EventCreate object."""
    return EventCreate(
        title="Test Event",
        description="Test Description",
        date=date(2024, 6, 15),
        time="20:00",
        location="Test Location",
        source="test"
    )


@pytest.fixture  
def mock_event_list():
    """Create list of mock events."""
    events = []
    for i in range(5):
        event = Mock()
        event.id = i + 1
        event.title = f"Test Event {i + 1}"
        event.date = date(2024, 6, 15 + i)
        events.append(event)
    return events


if __name__ == "__main__":
    # Run events route tests
    pytest.main([__file__, "-v"])