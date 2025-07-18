"""
Comprehensive test suite for the scraper system.
Tests scraper functionality, database persistence, and error handling.
"""

import pytest
import asyncio
from datetime import datetime, date
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from ..core.scraper_registry import get_scraper_registry, ScraperInfo, ScraperResult
from ..core.scraper_service import get_scraper_service
from ..core.database_optimization import get_database_optimizer, BulkEventProcessor
from ..core.error_handling import get_error_handler, RetryConfig
from ..core.scraper_logging import get_scraping_logger
from ..models.schemas import EventCreate


class TestScraperRegistry:
    """Test the scraper registry functionality."""
    
    def test_scraper_registration(self):
        """Test scraper registration and retrieval."""
        registry = get_scraper_registry()
        
        # Check that default scrapers are registered
        assert len(registry.get_scraper_names()) > 0
        assert "entrio" in registry.get_scraper_names()
        assert "croatia" in registry.get_scraper_names()
        
        # Test get_scraper
        entrio_scraper = registry.get_scraper("entrio")
        assert entrio_scraper is not None
        assert entrio_scraper.name == "entrio"
        assert entrio_scraper.display_name == "Entrio.hr"
        
        # Test non-existent scraper
        assert registry.get_scraper("nonexistent") is None
    
    def test_scraper_info_properties(self):
        """Test scraper info properties."""
        registry = get_scraper_registry()
        scrapers = registry.list_scrapers()
        
        assert len(scrapers) > 0
        
        for scraper in scrapers:
            assert hasattr(scraper, 'name')
            assert hasattr(scraper, 'display_name')
            assert hasattr(scraper, 'description')
            assert hasattr(scraper, 'scraper_func')
            assert isinstance(scraper.max_pages_default, int)
            assert isinstance(scraper.quick_limit, int)
            assert isinstance(scraper.supports_months, bool)
    
    @pytest.mark.asyncio
    async def test_scraper_execution_mock(self):
        """Test scraper execution with mocked functions."""
        registry = get_scraper_registry()
        
        # Mock a scraper function
        async def mock_scraper(max_pages: int = 5):
            return {
                "status": "success",
                "message": "Mock scraping completed",
                "scraped_events": 10,
                "saved_events": 8,
                "errors": []
            }
        
        # Register mock scraper
        mock_scraper_info = ScraperInfo(
            name="mock_test",
            display_name="Mock Test Scraper",
            description="Test scraper for unit tests",
            scraper_func=mock_scraper
        )
        registry.register(mock_scraper_info)
        
        # Test execution
        result = await registry.execute_scraper("mock_test", max_pages=3)
        
        assert isinstance(result, ScraperResult)
        assert result.status == "success"
        assert result.source == "mock_test"
        assert result.scraped_events == 10
        assert result.saved_events == 8
        assert result.processing_time > 0


class TestScraperService:
    """Test the scraper service functionality."""
    
    def test_service_initialization(self):
        """Test service initialization."""
        service = get_scraper_service()
        
        assert service is not None
        assert service.background_threshold == 2
        assert service.registry is not None
        assert service.error_manager is not None
    
    def test_get_available_scrapers(self):
        """Test getting available scrapers."""
        service = get_scraper_service()
        scrapers = service.get_available_scrapers()
        
        assert isinstance(scrapers, list)
        assert len(scrapers) > 0
        
        for scraper in scrapers:
            assert "name" in scraper
            assert "display_name" in scraper
            assert "description" in scraper
            assert "supports_months" in scraper
    
    def test_get_scraper_status(self):
        """Test getting scraper status."""
        service = get_scraper_service()
        status = service.get_scraper_status()
        
        assert "status" in status
        assert "total_scrapers" in status
        assert "available_scrapers" in status
        assert "service_info" in status
        assert "performance_stats" in status
        
        assert status["status"] == "operational"
        assert isinstance(status["total_scrapers"], int)
        assert isinstance(status["available_scrapers"], list)


class TestDatabaseOptimization:
    """Test database optimization functionality."""
    
    def test_event_hash_calculation(self):
        """Test event hash calculation."""
        # Create mock database session
        mock_session = Mock()
        
        from ..core.database_optimization import DatabaseOptimizer
        optimizer = DatabaseOptimizer(mock_session)
        
        # Create test event
        event = EventCreate(
            title="Test Event",
            date=date(2024, 6, 15),
            time="20:00",
            location="Test Location",
            source="test"
        )
        
        # Calculate hash
        hash1 = optimizer._calculate_event_hash(event)
        hash2 = optimizer._calculate_event_hash(event)
        
        # Same event should produce same hash
        assert hash1 == hash2
        
        # Different event should produce different hash
        event2 = EventCreate(
            title="Different Event",
            date=date(2024, 6, 15),
            time="20:00",
            location="Test Location",
            source="test"
        )
        
        hash3 = optimizer._calculate_event_hash(event2)
        assert hash1 != hash3
    
    def test_bulk_event_processor_initialization(self):
        """Test bulk event processor initialization."""
        processor = BulkEventProcessor(batch_size=500)
        
        assert processor.batch_size == 500
        assert processor.processed_count == 0
        assert processor.error_count == 0


class TestErrorHandling:
    """Test error handling functionality."""
    
    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        error_handler = get_error_handler("test_source")
        
        assert error_handler is not None
        assert error_handler.source == "test_source"
        assert error_handler.circuit_breaker is not None
        assert error_handler.retry_configs is not None
    
    def test_retry_config_creation(self):
        """Test retry configuration creation."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            strategy="exponential_backoff"
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 2.0
        assert config.strategy.value == "exponential_backoff"
    
    def test_error_classification(self):
        """Test error classification."""
        error_handler = get_error_handler("test_source")
        
        # Test different error types
        network_error = ConnectionError("Network connection failed")
        timeout_error = TimeoutError("Request timed out")
        parsing_error = ValueError("Invalid HTML structure")
        
        network_type = error_handler._classify_error(network_error)
        timeout_type = error_handler._classify_error(timeout_error)
        parsing_type = error_handler._classify_error(parsing_error)
        
        assert network_type.value == "network_error"
        assert timeout_type.value == "timeout_error"
        assert parsing_type.value == "validation_error"  # ValueError maps to validation_error
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self):
        """Test retry mechanism with mock operations."""
        error_handler = get_error_handler("test_source")
        
        # Mock operation that fails once then succeeds
        call_count = 0
        
        async def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("First attempt fails")
            return "success"
        
        # Configure retry
        retry_config = RetryConfig(max_attempts=3, base_delay=0.1)
        error_handler.add_retry_config("test_operation", retry_config)
        
        # Execute with retry
        result = await error_handler.execute_with_retry(
            mock_operation, 
            "test_operation"
        )
        
        assert result == "success"
        assert call_count == 2  # Should retry once and succeed


class TestScrapingLogger:
    """Test scraping logger functionality."""
    
    def test_logger_initialization(self):
        """Test logger initialization."""
        logger = get_scraping_logger("test_source")
        
        assert logger is not None
        assert logger.source == "test_source"
        assert logger.metrics is not None
        assert logger.errors == []
    
    def test_metrics_tracking(self):
        """Test metrics tracking."""
        logger = get_scraping_logger("test_source")
        
        # Test initial state
        assert logger.metrics.events_scraped == 0
        assert logger.metrics.events_saved == 0
        assert logger.metrics.pages_processed == 0
        
        # Test logging operations
        logger.log_page_complete(1, 5)
        assert logger.metrics.pages_processed == 1
        assert logger.metrics.events_scraped == 5
        
        logger.log_event_saved("Test Event")
        assert logger.metrics.events_saved == 1
        
        # Test completion
        logger.log_completion(success=True)
        assert logger.metrics.end_time is not None
        assert logger.metrics.duration > 0
    
    def test_error_logging(self):
        """Test error logging."""
        logger = get_scraping_logger("test_source")
        
        # Test error logging
        test_error = ValueError("Test error")
        scraping_error = logger.log_error(test_error, {"context": "test"})
        
        assert len(logger.errors) == 1
        assert len(logger.metrics.errors) == 1
        assert scraping_error.message == "Test error"
        assert scraping_error.source == "test_source"
        assert scraping_error.context == {"context": "test"}


class TestIntegration:
    """Integration tests for the complete scraper system."""
    
    @pytest.mark.asyncio
    async def test_service_scraper_integration(self):
        """Test integration between service and registry."""
        service = get_scraper_service()
        
        # Test that service can access registry
        available_scrapers = service.get_available_scrapers()
        assert len(available_scrapers) > 0
        
        # Test that all scrapers from registry are available in service
        registry_scrapers = service.registry.get_scraper_names()
        service_scrapers = [s["name"] for s in available_scrapers]
        
        assert set(registry_scrapers) == set(service_scrapers)
    
    def test_error_handling_integration(self):
        """Test integration between error handling and logging."""
        error_handler = get_error_handler("test_source")
        logger = get_scraping_logger("test_source")
        
        # Both should be working with the same source
        assert error_handler.source == logger.source
        
        # Test error statistics
        stats = error_handler.get_error_stats()
        assert "total_errors" in stats
        assert "circuit_breaker_state" in stats
    
    @pytest.mark.asyncio
    async def test_full_scraping_workflow_mock(self):
        """Test a complete scraping workflow with mocked components."""
        # Mock the scraper function
        async def mock_scraper_func(max_pages: int = 5):
            return {
                "status": "success",
                "message": "Mock scraping completed",
                "scraped_events": 15,
                "saved_events": 12,
                "errors": []
            }
        
        # Register mock scraper
        registry = get_scraper_registry()
        mock_scraper = ScraperInfo(
            name="integration_test",
            display_name="Integration Test Scraper",
            description="Test scraper for integration tests",
            scraper_func=mock_scraper_func
        )
        registry.register(mock_scraper)
        
        # Execute through service
        service = get_scraper_service()
        
        # Test immediate execution
        response = await service.scrape_single_source(
            source="integration_test",
            max_pages=2,  # Small number for immediate execution
            force_immediate=True
        )
        
        assert response.status == "success"
        assert response.source == "integration_test"
        assert response.scraped_events == 15
        assert response.saved_events == 12


def create_test_events(count: int = 10) -> List[EventCreate]:
    """Create test events for testing purposes."""
    events = []
    for i in range(count):
        event = EventCreate(
            title=f"Test Event {i}",
            date=date(2024, 6, 15 + i),
            time="20:00",
            location=f"Test Location {i}",
            source="test",
            description=f"Test event description {i}",
            price=f"${10 + i}",
            organizer=f"Test Organizer {i}"
        )
        events.append(event)
    return events


# Test configuration
@pytest.fixture
def test_events():
    """Fixture providing test events."""
    return create_test_events(10)


@pytest.fixture
def mock_database_session():
    """Fixture providing mock database session."""
    return Mock()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])