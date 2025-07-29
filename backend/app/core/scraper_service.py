"""
Unified scraper service layer for managing all scraping operations.
This service provides a high-level interface for scraping operations with proper error handling.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Union
from datetime import datetime

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel

from .scraper_registry import get_scraper_registry, ScraperResult
from .scraper_logging import scraping_context
from .error_handling import get_error_manager, RETRY_CONFIGS

logger = logging.getLogger(__name__)


class ScrapeRequest(BaseModel):
    """Request model for scraping operations."""
    max_pages: int = 5
    use_playwright: bool = True


class ScrapeResponse(BaseModel):
    """Response model for scraping operations."""
    status: str
    message: str
    scraped_events: Optional[int] = None
    saved_events: Optional[int] = None
    task_id: Optional[str] = None
    processing_time: Optional[float] = None
    source: Optional[str] = None
    errors: Optional[List[str]] = None


class MultiScrapeResponse(BaseModel):
    """Response model for multi-scraper operations."""
    status: str
    message: str
    total_scraped: int = 0
    total_saved: int = 0
    processing_time: Optional[float] = None
    task_id: Optional[str] = None
    results: List[ScrapeResponse] = []
    errors: List[str] = []


class ScraperService:
    """Unified service for all scraping operations."""
    
    def __init__(self):
        self.registry = get_scraper_registry()
        self.background_threshold = 2  # Pages above this run in background
        self.error_manager = get_error_manager()
        
        # Configure retry policies for scraping operations
        self._configure_retry_policies()
    
    def _configure_retry_policies(self) -> None:
        """Configure retry policies for all registered scrapers."""
        for scraper_name in self.registry.get_scraper_names():
            error_handler = self.error_manager.get_error_handler(scraper_name)
            
            # Add retry configurations for common operations
            for operation, config in RETRY_CONFIGS.items():
                error_handler.add_retry_config(operation, config)
    
    async def scrape_single_source(
        self,
        source: str,
        max_pages: int = 5,
        background_tasks: Optional[BackgroundTasks] = None,
        force_immediate: bool = False
    ) -> ScrapeResponse:
        """Scrape events from a single source with enhanced error handling."""
        scraper = self.registry.get_scraper(source)
        if not scraper:
            raise HTTPException(
                status_code=404,
                detail=f"Scraper '{source}' not found. Available scrapers: {', '.join(self.registry.get_scraper_names())}"
            )
        
        # Determine if we should run in background
        should_run_background = (
            not force_immediate and 
            max_pages > self.background_threshold and 
            background_tasks is not None
        )
        
        if should_run_background:
            # Run in background
            task_id = self.registry.create_task_id()
            
            async def background_scraping_task():
                async with scraping_context(source, max_pages) as scraping_logger:
                    try:
                        error_handler = self.error_manager.get_error_handler(source)
                        
                        # Execute with retry logic
                        if scraper.supports_months:
                            months_ahead = min(max_pages * 2, 12)
                            result = await error_handler.execute_with_retry(
                                self.registry.execute_scraper,
                                "scrape_source",
                                source,
                                months_ahead=months_ahead
                            )
                        else:
                            result = await error_handler.execute_with_retry(
                                self.registry.execute_scraper,
                                "scrape_source",
                                source,
                                max_pages=max_pages
                            )
                        
                        self.registry.complete_task(task_id, result)
                        self.error_manager.record_operation(success=True)
                        logger.info(f"Background scraping task {task_id} completed for {source}")
                        
                    except Exception as e:
                        error_result = ScraperResult(
                            status="error",
                            message=f"Background scraping failed: {str(e)}",
                            source=source,
                            errors=[str(e)]
                        )
                        self.registry.complete_task(task_id, error_result)
                        self.error_manager.record_operation(success=False)
                        logger.error(f"Background scraping task {task_id} failed for {source}: {e}")
            
            # Register and start background task
            self.registry.register_task(task_id, source, {"max_pages": max_pages})
            background_tasks.add_task(background_scraping_task)
            
            return ScrapeResponse(
                status="accepted",
                message=f"{scraper.display_name} scraping started in background for {max_pages} pages",
                task_id=task_id,
                source=source
            )
        else:
            # Run immediately with error handling
            async with scraping_context(source, max_pages) as scraping_logger:
                try:
                    error_handler = self.error_manager.get_error_handler(source)
                    
                    if scraper.supports_months:
                        months_ahead = min(max_pages * 2, 12)
                        result = await error_handler.execute_with_retry(
                            self.registry.execute_scraper,
                            "scrape_source",
                            source,
                            months_ahead=months_ahead
                        )
                    else:
                        result = await error_handler.execute_with_retry(
                            self.registry.execute_scraper,
                            "scrape_source",
                            source,
                            max_pages=max_pages
                        )
                    
                    self.error_manager.record_operation(success=True)
                    
                    return ScrapeResponse(
                        status=result.status,
                        message=result.message,
                        scraped_events=result.scraped_events,
                        saved_events=result.saved_events,
                        processing_time=result.processing_time,
                        source=result.source,
                        errors=result.errors if result.errors else None
                    )
                    
                except Exception as e:
                    self.error_manager.record_operation(success=False)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Scraping failed for {source}: {str(e)}"
                    ) from e
    
    async def scrape_quick(
        self,
        source: str,
        max_pages: int = 1
    ) -> ScrapeResponse:
        """Quick scraping for immediate results (always runs immediately)."""
        scraper = self.registry.get_scraper(source)
        if not scraper:
            raise HTTPException(
                status_code=404,
                detail=f"Scraper '{source}' not found"
            )
        
        # Ensure we don't exceed quick limits
        max_pages = min(max_pages, scraper.quick_limit)
        
        if scraper.supports_months:
            months_ahead = min(max_pages * 2, 6)  # Reduced for quick scraping
            result = await self.registry.execute_scraper(source, months_ahead=months_ahead)
        else:
            result = await self.registry.execute_scraper(source, max_pages=max_pages)
        
        return ScrapeResponse(
            status=result.status,
            message=result.message,
            scraped_events=result.scraped_events,
            saved_events=result.saved_events,
            processing_time=result.processing_time,
            source=result.source,
            errors=result.errors if result.errors else None
        )
    
    async def scrape_all_sources(
        self,
        max_pages: int = 5,
        background_tasks: Optional[BackgroundTasks] = None,
        concurrent: bool = False,
        force_immediate: bool = False
    ) -> MultiScrapeResponse:
        """Scrape events from all registered sources."""
        should_run_background = (
            not force_immediate and 
            max_pages > self.background_threshold and 
            background_tasks is not None
        )
        
        if should_run_background:
            # Run in background
            task_id = self.registry.create_task_id()
            
            async def background_all_scraping_task():
                try:
                    start_time = datetime.now()
                    results = await self.registry.execute_all_scrapers(max_pages=max_pages, concurrent=concurrent)
                    processing_time = (datetime.now() - start_time).total_seconds()
                    
                    # Process results
                    total_scraped = sum(r.scraped_events for r in results if isinstance(r, ScraperResult))
                    total_saved = sum(r.saved_events for r in results if isinstance(r, ScraperResult))
                    
                    logger.info(f"Background multi-source scraping task {task_id} completed")
                    
                except Exception as e:
                    logger.error(f"Background multi-source scraping task {task_id} failed: {e}")
            
            # Register and start background task
            self.registry.register_task(task_id, "all", {"max_pages": max_pages, "concurrent": concurrent})
            background_tasks.add_task(background_all_scraping_task)
            
            return MultiScrapeResponse(
                status="accepted",
                message=f"Multi-source scraping started in background for {max_pages} pages per source",
                task_id=task_id
            )
        else:
            # Run immediately
            start_time = datetime.now()
            results = await self.registry.execute_all_scrapers(max_pages=max_pages, concurrent=concurrent)
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Process results
            total_scraped = sum(r.scraped_events for r in results if isinstance(r, ScraperResult))
            total_saved = sum(r.saved_events for r in results if isinstance(r, ScraperResult))
            
            return MultiScrapeResponse(
                status="success",
                message=f"Multi-source scraping completed: {total_scraped} events scraped, {total_saved} saved",
                total_scraped=total_scraped,
                total_saved=total_saved,
                processing_time=processing_time,
                results=[self._convert_to_scrape_response(r) for r in results if isinstance(r, ScraperResult)],
                errors=[str(r) for r in results if isinstance(r, Exception)]
            )
    
    def get_available_scrapers(self) -> List[Dict[str, str]]:
        """Get list of available scrapers."""
        scrapers = self.registry.list_scrapers()
        return [
            {
                "name": s.name,
                "display_name": s.display_name,
                "description": s.description,
                "supports_months": s.supports_months
            }
            for s in scrapers
        ]
    
    def get_scraper_status(self) -> Dict[str, Union[str, List[str], Dict[str, str]]]:
        """Get comprehensive scraper service status."""
        global_stats = self.error_manager.get_global_stats()
        
        return {
            "status": "operational",
            "total_scrapers": len(self.registry.get_scraper_names()),
            "available_scrapers": self.registry.get_scraper_names(),
            "service_info": {
                "background_threshold": f"{self.background_threshold} pages",
                "quick_scraping_limit": "3 pages max",
                "concurrent_scraping": "supported"
            },
            "performance_stats": {
                "total_operations": global_stats["total_operations"],
                "success_rate": f"{global_stats['success_rate']:.1f}%",
                "total_errors": global_stats["failed_operations"],
                "retry_attempts": global_stats["retry_attempts"]
            },
            "error_handlers": {
                source: handler.get_error_stats()
                for source, handler in self.error_manager.error_handlers.items()
            }
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Union[str, Dict]]]:
        """Get background task status."""
        return self.registry.get_task_status(task_id)
    
    def _convert_to_scrape_response(self, result: ScraperResult) -> ScrapeResponse:
        """Convert ScraperResult to ScrapeResponse."""
        return ScrapeResponse(
            status=result.status,
            message=result.message,
            scraped_events=result.scraped_events,
            saved_events=result.saved_events,
            processing_time=result.processing_time,
            source=result.source,
            errors=result.errors if result.errors else None
        )


# Global service instance
_service = ScraperService()


def get_scraper_service() -> ScraperService:
    """Get the global scraper service instance."""
    return _service