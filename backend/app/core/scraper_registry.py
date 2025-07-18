"""
Scraper registry and service layer for unified scraper management.
This module provides a centralized registry for all scrapers and common scraping operations.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel

logger = logging.getLogger(__name__)


@dataclass
class ScraperInfo:
    """Information about a registered scraper."""
    name: str
    display_name: str
    description: str
    scraper_func: Callable
    max_pages_default: int = 5
    quick_limit: int = 3
    supports_months: bool = False  # For calendar-based scrapers like TzDubrovnik
    

class ScraperResult(BaseModel):
    """Standardized scraper result."""
    status: str
    message: str
    source: str
    scraped_events: int = 0
    saved_events: int = 0
    processing_time: float = 0.0
    errors: List[str] = []
    task_id: Optional[str] = None


class ScraperRegistry:
    """Registry for all Croatian event scrapers."""
    
    def __init__(self):
        self._scrapers: Dict[str, ScraperInfo] = {}
        self._active_tasks: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    def register(self, scraper_info: ScraperInfo) -> None:
        """Register a scraper."""
        self._scrapers[scraper_info.name] = scraper_info
        logger.info(f"Registered scraper: {scraper_info.name} ({scraper_info.display_name})")
    
    def get_scraper(self, name: str) -> Optional[ScraperInfo]:
        """Get scraper by name."""
        return self._scrapers.get(name.lower())
    
    def list_scrapers(self) -> List[ScraperInfo]:
        """List all registered scrapers."""
        return list(self._scrapers.values())
    
    def get_scraper_names(self) -> List[str]:
        """Get all registered scraper names."""
        return list(self._scrapers.keys())
    
    async def execute_scraper(
        self, 
        name: str, 
        max_pages: int = 5,
        months_ahead: Optional[int] = None,
        **kwargs
    ) -> ScraperResult:
        """Execute a scraper and return standardized result."""
        scraper = self.get_scraper(name)
        if not scraper:
            return ScraperResult(
                status="error",
                message=f"Scraper '{name}' not found",
                source=name,
                errors=[f"Unknown scraper: {name}"]
            )
        
        start_time = datetime.now()
        
        try:
            # Call the scraper function with appropriate parameters
            if scraper.supports_months and months_ahead is not None:
                result = await scraper.scraper_func(months_ahead=months_ahead)
            else:
                result = await scraper.scraper_func(max_pages=max_pages, **kwargs)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Standardize the result
            return ScraperResult(
                status=result.get("status", "success"),
                message=result.get("message", f"Successfully scraped {scraper.display_name}"),
                source=name,
                scraped_events=result.get("scraped_events", 0),
                saved_events=result.get("saved_events", 0),
                processing_time=processing_time,
                errors=result.get("errors", [])
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Scraper '{name}' execution failed: {e}")
            
            return ScraperResult(
                status="error",
                message=f"Scraper execution failed: {str(e)}",
                source=name,
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def execute_all_scrapers(
        self, 
        max_pages: int = 5,
        concurrent: bool = False
    ) -> List[ScraperResult]:
        """Execute all registered scrapers."""
        if concurrent:
            # Execute all scrapers concurrently
            tasks = []
            for name in self.get_scraper_names():
                scraper = self.get_scraper(name)
                if scraper.supports_months:
                    # For calendar-based scrapers, convert pages to months
                    months_ahead = min(max_pages * 2, 12)
                    task = self.execute_scraper(name, months_ahead=months_ahead)
                else:
                    task = self.execute_scraper(name, max_pages=max_pages)
                tasks.append(task)
            
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Execute scrapers sequentially
            results = []
            for name in self.get_scraper_names():
                scraper = self.get_scraper(name)
                if scraper.supports_months:
                    months_ahead = min(max_pages * 2, 12)
                    result = await self.execute_scraper(name, months_ahead=months_ahead)
                else:
                    result = await self.execute_scraper(name, max_pages=max_pages)
                results.append(result)
            
            return results
    
    def create_task_id(self) -> str:
        """Create a unique task ID."""
        return str(uuid.uuid4())
    
    def register_task(self, task_id: str, scraper_name: str, params: Dict[str, Any]) -> None:
        """Register a background task."""
        self._active_tasks[task_id] = {
            "scraper": scraper_name,
            "params": params,
            "created_at": datetime.now(),
            "status": "running"
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        return self._active_tasks.get(task_id)
    
    def complete_task(self, task_id: str, result: ScraperResult) -> None:
        """Mark task as completed."""
        if task_id in self._active_tasks:
            self._active_tasks[task_id]["status"] = "completed"
            self._active_tasks[task_id]["result"] = result
            self._active_tasks[task_id]["completed_at"] = datetime.now()
    
    def initialize_default_scrapers(self) -> None:
        """Initialize default Croatian event scrapers."""
        if self._initialized:
            return
            
        # Import scraper functions here to avoid circular imports
        from ..scraping.entrio_scraper import scrape_entrio_events
        from ..scraping.croatia_scraper import scrape_croatia_events
        from ..scraping.ulaznice_scraper import scrape_ulaznice_events
        from ..scraping.infozagreb_scraper import scrape_infozagreb_events
        from ..scraping.vukovar_scraper import scrape_vukovar_events
        from ..scraping.visitkarlovac_scraper import scrape_visitkarlovac_events
        from ..scraping.visitopatija_scraper import scrape_visitopatija_events
        from ..scraping.visitvarazdin_scraper import scrape_visitvarazdin_events
        from ..scraping.visitrijeka_scraper import scrape_visitrijeka_events
        from ..scraping.visitsplit_scraper import scrape_visitsplit_events
        from ..scraping.zadar_scraper import scrape_zadar_events
        from ..scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events
        
        # Register all scrapers
        scrapers = [
            ScraperInfo(
                name="entrio",
                display_name="Entrio.hr",
                description="Scrape events from Entrio.hr ticketing platform",
                scraper_func=scrape_entrio_events
            ),
            ScraperInfo(
                name="croatia",
                display_name="Croatia.hr",
                description="Scrape events from Croatia.hr official tourism site",
                scraper_func=scrape_croatia_events
            ),
            ScraperInfo(
                name="ulaznice",
                display_name="Ulaznice.hr",
                description="Scrape events from Ulaznice.hr ticketing platform",
                scraper_func=scrape_ulaznice_events
            ),
            ScraperInfo(
                name="infozagreb",
                display_name="InfoZagreb.hr",
                description="Scrape events from InfoZagreb.hr city portal",
                scraper_func=scrape_infozagreb_events
            ),
            ScraperInfo(
                name="vukovar",
                display_name="TurizamVukovar.hr",
                description="Scrape events from Vukovar tourism site",
                scraper_func=scrape_vukovar_events
            ),
            ScraperInfo(
                name="visitkarlovac",
                display_name="VisitKarlovac.hr",
                description="Scrape events from Karlovac tourism site",
                scraper_func=scrape_visitkarlovac_events
            ),
            ScraperInfo(
                name="visitopatija",
                display_name="VisitOpatija.com",
                description="Scrape events from Opatija tourism site",
                scraper_func=scrape_visitopatija_events
            ),
            ScraperInfo(
                name="visitvarazdin",
                display_name="VisitVarazdin.hr",
                description="Scrape events from Varazdin tourism site",
                scraper_func=scrape_visitvarazdin_events
            ),
            ScraperInfo(
                name="visitrijeka",
                display_name="VisitRijeka.hr",
                description="Scrape events from Rijeka tourism site",
                scraper_func=scrape_visitrijeka_events
            ),
            ScraperInfo(
                name="visitsplit",
                display_name="VisitSplit.com",
                description="Scrape events from Split tourism site",
                scraper_func=scrape_visitsplit_events
            ),
            ScraperInfo(
                name="zadar",
                display_name="Zadar Travel",
                description="Scrape events from Zadar travel site",
                scraper_func=scrape_zadar_events
            ),
            ScraperInfo(
                name="tzdubrovnik",
                display_name="TzDubrovnik.hr",
                description="Scrape events from Dubrovnik tourism site",
                scraper_func=scrape_tzdubrovnik_events,
                supports_months=True  # Calendar-based scraper
            ),
        ]
        
        for scraper in scrapers:
            self.register(scraper)
        
        self._initialized = True
        logger.info(f"Initialized {len(scrapers)} scrapers in registry")


# Global registry instance
_registry = ScraperRegistry()


def get_scraper_registry() -> ScraperRegistry:
    """Get the global scraper registry instance."""
    if not _registry._initialized:
        _registry.initialize_default_scrapers()
    return _registry