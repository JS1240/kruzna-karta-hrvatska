"""
Comprehensive test suite for venues API routes.

Tests all endpoints in routes/venues.py with request/response validation,
error handling, geographic search, and business logic validation using
the established excellent testing patterns.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.schemas import VenueCreate, VenueSearchParams


class TestVenuesRoutes:
    """Test venues API routes."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session fixture."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_venue_data(self):
        """Sample venue data for testing."""
        return {
            "name": "Arena Zagreb",
            "city": "Zagreb",
            "address": "Savska cesta 25, Zagreb",
            "venue_type": "arena",
            "capacity": 15000,
            "latitude": 45.8051,
            "longitude": 15.9815,
            "phone": "+385 1 4667 777",
            "email": "info@arena-zagreb.hr",
            "website": "https://www.arena-zagreb.hr"
        }
    
    @pytest.fixture
    def sample_venue_response(self):
        """Sample venue response data."""
        return {
            "id": 1,
            "name": "Arena Zagreb",
            "city": "Zagreb",
            "address": "Savska cesta 25, Zagreb",
            "venue_type": "arena",
            "capacity": 15000,
            "latitude": 45.8051,
            "longitude": 15.9815,
            "phone": "+385 1 4667 777",
            "email": "info@arena-zagreb.hr",
            "website": "https://www.arena-zagreb.hr",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }


class TestGetVenues:
    """Test GET /api/venues/ endpoint."""
    
    def test_get_venues_success(self, client):
        """Test successful venues retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock venue
            mock_venue = Mock()
            mock_venue.id = 1
            mock_venue.name = "Arena Zagreb"
            mock_venue.city = "Zagreb"
            
            mock_db.query.return_value.count.return_value = 1
            mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_venue]
            
            response = client.get("/api/venues/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "venues" in data
            assert "total" in data
            assert "page" in data
            assert "size" in data
            assert "pages" in data
            assert data["total"] == 1
    
    def test_get_venues_with_search_query(self, client):
        """Test venues retrieval with search query."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.name = "Arena Zagreb"
            
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_venue]
            
            response = client.get("/api/venues/?q=arena")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
            
            # Verify search filter was applied
            mock_db.query.return_value.filter.assert_called()
    
    def test_get_venues_with_city_filter(self, client):
        """Test venues retrieval with city filter."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.city = "Zagreb"
            
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_venue]
            
            response = client.get("/api/venues/?city=Zagreb")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
    
    def test_get_venues_with_venue_type_filter(self, client):
        """Test venues retrieval with venue type filter."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.venue_type = "arena"
            
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_venue]
            
            response = client.get("/api/venues/?venue_type=arena")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
    
    def test_get_venues_with_geographic_search(self, client):
        """Test venues retrieval with geographic parameters."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.latitude = 45.8051
            mock_venue.longitude = 15.9815
            
            mock_db.query.return_value.filter.return_value.count.return_value = 1
            mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_venue]
            
            response = client.get("/api/venues/?latitude=45.815&longitude=15.982&radius_km=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
    
    def test_get_venues_with_pagination(self, client):
        """Test venues retrieval with pagination parameters."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.count.return_value = 50
            mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/venues/?page=2&size=10")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["page"] == 2
            assert data["size"] == 0  # No venues returned
            assert data["total"] == 50
            assert data["pages"] == 5
    
    def test_get_venues_combined_filters(self, client):
        """Test venues retrieval with multiple filters combined."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock chaining of filters
            mock_query = mock_db.query.return_value
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/venues/?q=arena&city=Zagreb&venue_type=arena")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify multiple filters were applied
            assert mock_query.filter.call_count >= 3
    
    def test_get_venues_empty_result(self, client):
        """Test venues retrieval with no results."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.count.return_value = 0
            mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
            
            response = client.get("/api/venues/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["venues"] == []
            assert data["total"] == 0
            assert data["pages"] == 0


class TestSearchVenues:
    """Test GET /api/venues/search endpoint."""
    
    def test_search_venues_success(self, client):
        """Test successful venues search."""
        with patch('backend.app.routes.venues.get_venues') as mock_get_venues:
            mock_get_venues.return_value = {
                "venues": [{"id": 1, "name": "Arena Zagreb"}],
                "total": 1,
                "page": 1,
                "size": 1,
                "pages": 1
            }
            
            response = client.get("/api/venues/search?q=arena&city=Zagreb")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
            
            # Verify get_venues was called with correct parameters
            mock_get_venues.assert_called_once()
            call_args = mock_get_venues.call_args
            assert call_args.kwargs["q"] == "arena"
            assert call_args.kwargs["city"] == "Zagreb"
    
    def test_search_venues_with_all_parameters(self, client):
        """Test venues search with all possible parameters."""
        with patch('backend.app.routes.venues.get_venues') as mock_get_venues:
            mock_get_venues.return_value = {
                "venues": [],
                "total": 0,
                "page": 1,
                "size": 0,
                "pages": 0
            }
            
            query_params = {
                "q": "concert hall",
                "city": "Split",
                "venue_type": "concert_hall",
                "latitude": "43.5085",
                "longitude": "16.4405",
                "radius_km": "5",
                "page": "1",
                "size": "20"
            }
            
            response = client.get("/api/venues/search", params=query_params)
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify all parameters were passed
            call_args = mock_get_venues.call_args
            assert call_args.kwargs["q"] == "concert hall"
            assert call_args.kwargs["city"] == "Split"
            assert call_args.kwargs["venue_type"] == "concert_hall"
            assert call_args.kwargs["latitude"] == 43.5085
            assert call_args.kwargs["longitude"] == 16.4405
            assert call_args.kwargs["radius_km"] == 5.0


class TestGetCities:
    """Test GET /api/venues/cities endpoint."""
    
    def test_get_cities_success(self, client):
        """Test successful cities list retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock cities query result
            mock_cities = [("Zagreb",), ("Split",), ("Rijeka",)]
            mock_db.query.return_value.distinct.return_value.order_by.return_value.all.return_value = mock_cities
            
            response = client.get("/api/venues/cities")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "cities" in data
            assert data["cities"] == ["Zagreb", "Split", "Rijeka"]
    
    def test_get_cities_empty_result(self, client):
        """Test cities list with no venues."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.distinct.return_value.order_by.return_value.all.return_value = []
            
            response = client.get("/api/venues/cities")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["cities"] == []


class TestGetVenueTypes:
    """Test GET /api/venues/types endpoint."""
    
    def test_get_venue_types_success(self, client):
        """Test successful venue types list retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock venue types query result
            mock_types = [("arena",), ("concert_hall",), ("theater",)]
            mock_db.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = mock_types
            
            response = client.get("/api/venues/types")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "types" in data
            assert data["types"] == ["arena", "concert_hall", "theater"]
    
    def test_get_venue_types_empty_result(self, client):
        """Test venue types list with no types."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.distinct.return_value.order_by.return_value.all.return_value = []
            
            response = client.get("/api/venues/types")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["types"] == []


class TestGetNearbyVenues:
    """Test GET /api/venues/nearby endpoint."""
    
    def test_get_nearby_venues_success(self, client):
        """Test successful nearby venues retrieval."""
        with patch('backend.app.routes.venues.get_venues') as mock_get_venues:
            mock_get_venues.return_value = {
                "venues": [{"id": 1, "name": "Nearby Venue"}],
                "total": 1,
                "page": 1,
                "size": 1,
                "pages": 1
            }
            
            response = client.get("/api/venues/nearby?latitude=45.815&longitude=15.982")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["venues"]) == 1
            
            # Verify get_venues was called with geographic parameters
            call_args = mock_get_venues.call_args
            assert call_args.kwargs["latitude"] == 45.815
            assert call_args.kwargs["longitude"] == 15.982
            assert call_args.kwargs["radius_km"] == 10  # Default radius
    
    def test_get_nearby_venues_with_custom_radius(self, client):
        """Test nearby venues with custom radius."""
        with patch('backend.app.routes.venues.get_venues') as mock_get_venues:
            mock_get_venues.return_value = {
                "venues": [],
                "total": 0,
                "page": 1,
                "size": 0,
                "pages": 0
            }
            
            response = client.get("/api/venues/nearby?latitude=45.815&longitude=15.982&radius_km=25")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify custom radius was used
            call_args = mock_get_venues.call_args
            assert call_args.kwargs["radius_km"] == 25.0
    
    def test_get_nearby_venues_missing_coordinates(self, client):
        """Test nearby venues with missing coordinates."""
        response = client.get("/api/venues/nearby")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
    
    def test_get_nearby_venues_invalid_coordinates(self, client):
        """Test nearby venues with invalid coordinates."""
        response = client.get("/api/venues/nearby?latitude=invalid&longitude=15.982")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"


class TestGetSpecificVenue:
    """Test GET /api/venues/{venue_id} endpoint."""
    
    def test_get_venue_success(self, client):
        """Test successful single venue retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock venue
            mock_venue = Mock()
            mock_venue.id = 1
            mock_venue.name = "Arena Zagreb"
            mock_venue.city = "Zagreb"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            
            response = client.get("/api/venues/1")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_venue_not_found(self, client):
        """Test venue not found scenario."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock no venue found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/venues/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "VENUE_NOT_FOUND"
            assert "99999" in data["message"]
    
    def test_get_venue_invalid_id(self, client):
        """Test venue retrieval with invalid ID format."""
        response = client.get("/api/venues/invalid-id")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"


class TestCreateVenue:
    """Test POST /api/venues/ endpoint."""
    
    def test_create_venue_success(self, client, sample_venue_data):
        """Test successful venue creation."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock no existing venue with same name and city
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock successful creation
            mock_venue = Mock()
            mock_venue.id = 1
            mock_venue.name = sample_venue_data["name"]
            mock_venue.city = sample_venue_data["city"]
            
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            response = client.post("/api/venues/", json=sample_venue_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_create_venue_duplicate_name_city(self, client, sample_venue_data):
        """Test venue creation with duplicate name and city combination."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock existing venue with same name and city
            existing_venue = Mock()
            existing_venue.name = sample_venue_data["name"]
            existing_venue.city = sample_venue_data["city"]
            mock_db.query.return_value.filter.return_value.first.return_value = existing_venue
            
            response = client.post("/api/venues/", json=sample_venue_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "RESOURCE_ALREADY_EXISTS"
            assert sample_venue_data["name"] in data["message"]
            assert sample_venue_data["city"] in data["message"]
    
    def test_create_venue_validation_error(self, client):
        """Test venue creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "city": "",  # Empty city
            "capacity": -100,  # Negative capacity
            "latitude": 91.0,  # Invalid latitude
            "longitude": 181.0  # Invalid longitude
        }
        
        response = client.post("/api/venues/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        assert "details" in data
    
    def test_create_venue_missing_required_fields(self, client):
        """Test venue creation with missing required fields."""
        incomplete_data = {
            "address": "Some address"
            # Missing required name and city
        }
        
        response = client.post("/api/venues/", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateVenue:
    """Test PUT /api/venues/{venue_id} endpoint."""
    
    def test_update_venue_success(self, client):
        """Test successful venue update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock existing venue
            mock_venue = Mock()
            mock_venue.id = 1
            mock_venue.name = "Old Name"
            mock_venue.city = "Zagreb"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            
            update_data = {
                "name": "Updated Name",
                "capacity": 20000
            }
            
            response = client.put("/api/venues/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.commit.assert_called_once()
    
    def test_update_venue_not_found(self, client):
        """Test updating non-existent venue."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            update_data = {"name": "New Name"}
            
            response = client.put("/api/venues/99999", json=update_data)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "VENUE_NOT_FOUND"
    
    def test_update_venue_name_city_conflict(self, client):
        """Test updating venue with conflicting name/city combination."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock target venue
            target_venue = Mock()
            target_venue.id = 1
            target_venue.name = "Old Name"
            target_venue.city = "Zagreb"
            
            # Mock conflicting venue
            conflicting_venue = Mock()
            conflicting_venue.id = 2
            conflicting_venue.name = "New Name"
            conflicting_venue.city = "Zagreb"
            
            # First query returns target venue, second returns conflicting venue
            mock_db.query.return_value.filter.return_value.first.side_effect = [target_venue, conflicting_venue]
            
            update_data = {"name": "New Name"}
            
            response = client.put("/api/venues/1", json=update_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["code"] == "RESOURCE_ALREADY_EXISTS"
    
    def test_update_venue_partial_update(self, client):
        """Test partial venue update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.id = 1
            mock_venue.name = "Arena Zagreb"
            mock_venue.capacity = 15000
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            
            # Only update capacity
            update_data = {"capacity": 18000}
            
            response = client.put("/api/venues/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK


class TestDeleteVenue:
    """Test DELETE /api/venues/{venue_id} endpoint."""
    
    def test_delete_venue_success(self, client):
        """Test successful venue deletion."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.id = 1
            
            # Mock venue exists and no events associated
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            response = client.delete("/api/venues/1")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Venue deleted successfully"
            mock_db.delete.assert_called_once_with(mock_venue)
            mock_db.commit.assert_called_once()
    
    def test_delete_venue_not_found(self, client):
        """Test deleting non-existent venue."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.delete("/api/venues/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "VENUE_NOT_FOUND"
    
    def test_delete_venue_with_events(self, client):
        """Test deleting venue that has associated events."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.id = 1
            
            # Mock venue exists but has associated events
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            mock_db.query.return_value.filter.return_value.count.return_value = 3
            
            response = client.delete("/api/venues/1")
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CANNOT_DELETE_REFERENCED_ENTITY"
            assert "3" in data["message"]
            assert "events" in data["message"]


class TestGetVenueEvents:
    """Test GET /api/venues/{venue_id}/events endpoint."""
    
    def test_get_venue_events_success(self, client):
        """Test successful venue events retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.routes.events.get_events') as mock_get_events:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock venue exists
            mock_venue = Mock()
            mock_venue.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            
            # Mock events response
            mock_get_events.return_value = {
                "events": [{"id": 1, "title": "Test Event", "venue_id": 1}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/venues/1/events")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 1
            
            # Verify get_events was called with correct parameters
            mock_get_events.assert_called_once()
            call_args = mock_get_events.call_args
            assert call_args.kwargs["venue_id"] == 1
    
    def test_get_venue_events_with_pagination(self, client):
        """Test venue events with pagination parameters."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.routes.events.get_events') as mock_get_events:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_venue = Mock()
            mock_venue.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_venue
            
            mock_get_events.return_value = {
                "events": [],
                "total": 30,
                "page": 3,
                "size": 10,
                "pages": 3
            }
            
            response = client.get("/api/venues/1/events?page=3&size=10")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify pagination parameters were passed
            call_args = mock_get_events.call_args
            assert call_args.kwargs["page"] == 3
            assert call_args.kwargs["size"] == 10
    
    def test_get_venue_events_venue_not_found(self, client):
        """Test venue events when venue doesn't exist."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock venue not found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/venues/99999/events")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "VENUE_NOT_FOUND"


# Additional test utilities and fixtures
@pytest.fixture
def mock_venue_create():
    """Create mock VenueCreate object."""
    return VenueCreate(
        name="Test Venue",
        city="Zagreb",
        address="Test Address 123",
        venue_type="concert_hall",
        capacity=1000,
        latitude=45.8051,
        longitude=15.9815
    )


@pytest.fixture  
def mock_venue_list():
    """Create list of mock venues."""
    venues = []
    for i in range(5):
        venue = Mock()
        venue.id = i + 1
        venue.name = f"Venue {i + 1}"
        venue.city = f"City {i + 1}"
        venues.append(venue)
    return venues


@pytest.fixture
def mock_venue_search_params():
    """Create mock VenueSearchParams object."""
    return VenueSearchParams(
        q="test venue",
        city="Zagreb",
        venue_type="arena",
        latitude=45.8051,
        longitude=15.9815,
        radius_km=10.0,
        page=1,
        size=20
    )


if __name__ == "__main__":
    # Run venues route tests
    pytest.main([__file__, "-v"])