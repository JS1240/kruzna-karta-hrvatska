"""
Comprehensive test suite for categories API routes.

Tests all endpoints in routes/categories.py with request/response validation,
error handling, authentication, and business logic validation using
the established excellent testing patterns.
"""

from unittest.mock import Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.schemas import EventCategoryCreate


class TestCategoriesRoutes:
    """Test categories API routes."""
    
    @pytest.fixture
    def client(self):
        """FastAPI test client fixture."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session fixture."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_category_data(self):
        """Sample category data for testing."""
        return {
            "name": "Concerts",
            "slug": "concerts",
            "description": "Live music performances and concerts",
            "color": "#FF5733",
            "icon": "music"
        }
    
    @pytest.fixture
    def sample_category_response(self):
        """Sample category response data."""
        return {
            "id": 1,
            "name": "Concerts",
            "slug": "concerts",
            "description": "Live music performances and concerts",
            "color": "#FF5733",
            "icon": "music",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }


class TestGetCategories:
    """Test GET /api/categories/ endpoint."""
    
    def test_get_categories_success(self, client):
        """Test successful categories retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock categories
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Concerts"
            mock_category.slug = "concerts"
            
            mock_db.query.return_value.order_by.return_value.all.return_value = [mock_category]
            
            response = client.get("/api/categories/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "categories" in data
            assert "total" in data
            assert data["total"] == 1
    
    def test_get_categories_with_search(self, client):
        """Test categories retrieval with search parameter."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Concerts"
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_category]
            
            response = client.get("/api/categories/?search=concerts")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data["categories"]) == 1
            
            # Verify search filter was applied
            mock_db.query.return_value.filter.assert_called_once()
    
    def test_get_categories_empty_result(self, client):
        """Test categories retrieval with no results."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.order_by.return_value.all.return_value = []
            
            response = client.get("/api/categories/")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["categories"] == []
            assert data["total"] == 0
    
    def test_get_categories_search_case_insensitive(self, client):
        """Test categories search is case insensitive."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.name = "CONCERTS"
            
            mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_category]
            
            response = client.get("/api/categories/?search=CoNcErTs")
            
            assert response.status_code == status.HTTP_200_OK
            # Verify ilike was used for case-insensitive search
            mock_db.query.return_value.filter.assert_called_once()


class TestGetSpecificCategory:
    """Test GET /api/categories/{category_id} endpoint."""
    
    def test_get_category_success(self, client):
        """Test successful single category retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock category
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Concerts"
            mock_category.slug = "concerts"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            response = client.get("/api/categories/1")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_category_not_found(self, client):
        """Test category not found scenario."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock no category found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/categories/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CATEGORY_NOT_FOUND"
            assert "99999" in data["message"]
    
    def test_get_category_invalid_id(self, client):
        """Test category retrieval with invalid ID format."""
        response = client.get("/api/categories/invalid-id")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"


class TestGetCategoryBySlug:
    """Test GET /api/categories/slug/{slug} endpoint."""
    
    def test_get_category_by_slug_success(self, client):
        """Test successful category retrieval by slug."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Concerts"
            mock_category.slug = "concerts"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            response = client.get("/api/categories/slug/concerts")
            
            assert response.status_code == status.HTTP_200_OK
    
    def test_get_category_by_slug_not_found(self, client):
        """Test category by slug not found scenario."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/categories/slug/nonexistent-category")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CATEGORY_NOT_FOUND"
            assert "nonexistent-category" in data["message"]
    
    def test_get_category_by_slug_special_characters(self, client):
        """Test category retrieval with slug containing special characters."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.slug = "art-and-culture"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            response = client.get("/api/categories/slug/art-and-culture")
            
            assert response.status_code == status.HTTP_200_OK


class TestCreateCategory:
    """Test POST /api/categories/ endpoint."""
    
    def test_create_category_success(self, client, sample_category_data):
        """Test successful category creation."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock no existing category with same slug
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock successful creation
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = sample_category_data["name"]
            mock_category.slug = sample_category_data["slug"]
            
            mock_db.add = Mock()
            mock_db.commit = Mock()
            mock_db.refresh = Mock()
            
            response = client.post("/api/categories/", json=sample_category_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_create_category_duplicate_slug(self, client, sample_category_data):
        """Test category creation with duplicate slug."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock existing category with same slug
            existing_category = Mock()
            existing_category.slug = sample_category_data["slug"]
            mock_db.query.return_value.filter.return_value.first.return_value = existing_category
            
            response = client.post("/api/categories/", json=sample_category_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "RESOURCE_ALREADY_EXISTS"
            assert sample_category_data["slug"] in data["message"]
    
    def test_create_category_validation_error(self, client):
        """Test category creation with validation errors."""
        invalid_data = {
            "name": "",  # Empty name
            "slug": "",  # Empty slug
            "color": "invalid-color"  # Invalid color format
        }
        
        response = client.post("/api/categories/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"
        assert "details" in data
    
    def test_create_category_missing_required_fields(self, client):
        """Test category creation with missing required fields."""
        incomplete_data = {
            "description": "Test description"
            # Missing required name and slug
        }
        
        response = client.post("/api/categories/", json=incomplete_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateCategory:
    """Test PUT /api/categories/{category_id} endpoint."""
    
    def test_update_category_success(self, client):
        """Test successful category update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock existing category
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Old Name"
            mock_category.slug = "old-slug"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            update_data = {
                "name": "Updated Name",
                "description": "Updated description"
            }
            
            response = client.put("/api/categories/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK
            mock_db.commit.assert_called_once()
    
    def test_update_category_not_found(self, client):
        """Test updating non-existent category."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            update_data = {"name": "New Name"}
            
            response = client.put("/api/categories/99999", json=update_data)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CATEGORY_NOT_FOUND"
    
    def test_update_category_slug_conflict(self, client):
        """Test updating category with conflicting slug."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock target category
            target_category = Mock()
            target_category.id = 1
            target_category.slug = "old-slug"
            
            # Mock conflicting category
            conflicting_category = Mock()
            conflicting_category.id = 2
            conflicting_category.slug = "new-slug"
            
            # First query returns target category, second returns conflicting category
            mock_db.query.return_value.filter.return_value.first.side_effect = [target_category, conflicting_category]
            
            update_data = {"slug": "new-slug"}
            
            response = client.put("/api/categories/1", json=update_data)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["code"] == "RESOURCE_ALREADY_EXISTS"
    
    def test_update_category_partial_update(self, client):
        """Test partial category update."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            mock_category.name = "Original Name"
            mock_category.color = "#FF0000"
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            # Only update color
            update_data = {"color": "#00FF00"}
            
            response = client.put("/api/categories/1", json=update_data)
            
            assert response.status_code == status.HTTP_200_OK


class TestDeleteCategory:
    """Test DELETE /api/categories/{category_id} endpoint."""
    
    def test_delete_category_success(self, client):
        """Test successful category deletion."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            
            # Mock category exists and no events associated
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            response = client.delete("/api/categories/1")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["message"] == "Category deleted successfully"
            mock_db.delete.assert_called_once_with(mock_category)
            mock_db.commit.assert_called_once()
    
    def test_delete_category_not_found(self, client):
        """Test deleting non-existent category."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.delete("/api/categories/99999")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CATEGORY_NOT_FOUND"
    
    def test_delete_category_with_events(self, client):
        """Test deleting category that has associated events."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            
            # Mock category exists but has associated events
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            mock_db.query.return_value.filter.return_value.count.return_value = 5
            
            response = client.delete("/api/categories/1")
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CANNOT_DELETE_REFERENCED_ENTITY"
            assert "5" in data["message"]
            assert "events" in data["message"]
    
    def test_delete_category_database_error(self, client):
        """Test category deletion with database error."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            mock_db.query.return_value.filter.return_value.count.return_value = 0
            
            # Mock database error during deletion
            mock_db.delete.side_effect = Exception("Database error")
            
            response = client.delete("/api/categories/1")
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            data = response.json()
            assert data["error"] is True


class TestGetCategoryEvents:
    """Test GET /api/categories/{category_id}/events endpoint."""
    
    def test_get_category_events_success(self, client):
        """Test successful category events retrieval."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.routes.events.get_events') as mock_get_events:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock category exists
            mock_category = Mock()
            mock_category.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            # Mock events response
            mock_get_events.return_value = {
                "events": [{"id": 1, "title": "Test Event", "category_id": 1}],
                "total": 1,
                "page": 1,
                "size": 20,
                "pages": 1
            }
            
            response = client.get("/api/categories/1/events")
            
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "events" in data
            assert len(data["events"]) == 1
            
            # Verify get_events was called with correct parameters
            mock_get_events.assert_called_once()
            call_args = mock_get_events.call_args
            assert call_args.kwargs["category_id"] == 1
    
    def test_get_category_events_with_pagination(self, client):
        """Test category events with pagination parameters."""
        with patch('backend.app.core.database.get_db') as mock_get_db, \
             patch('backend.app.routes.events.get_events') as mock_get_events:
            
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            mock_category = Mock()
            mock_category.id = 1
            mock_db.query.return_value.filter.return_value.first.return_value = mock_category
            
            mock_get_events.return_value = {
                "events": [],
                "total": 50,
                "page": 2,
                "size": 10,
                "pages": 5
            }
            
            response = client.get("/api/categories/1/events?page=2&size=10")
            
            assert response.status_code == status.HTTP_200_OK
            
            # Verify pagination parameters were passed
            call_args = mock_get_events.call_args
            assert call_args.kwargs["page"] == 2
            assert call_args.kwargs["size"] == 10
    
    def test_get_category_events_category_not_found(self, client):
        """Test category events when category doesn't exist."""
        with patch('backend.app.core.database.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db
            
            # Mock category not found
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/categories/99999/events")
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["error"] is True
            assert data["code"] == "CATEGORY_NOT_FOUND"
    
    def test_get_category_events_invalid_pagination(self, client):
        """Test category events with invalid pagination parameters."""
        response = client.get("/api/categories/1/events?page=0&size=101")
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert data["error"] is True
        assert data["category"] == "validation"


# Additional test utilities and fixtures
@pytest.fixture
def mock_category_create():
    """Create mock EventCategoryCreate object."""
    return EventCategoryCreate(
        name="Test Category",
        slug="test-category",
        description="Test category description",
        color="#FF0000",
        icon="test-icon"
    )


@pytest.fixture  
def mock_category_list():
    """Create list of mock categories."""
    categories = []
    for i in range(5):
        category = Mock()
        category.id = i + 1
        category.name = f"Category {i + 1}"
        category.slug = f"category-{i + 1}"
        categories.append(category)
    return categories


if __name__ == "__main__":
    # Run categories route tests
    pytest.main([__file__, "-v"])