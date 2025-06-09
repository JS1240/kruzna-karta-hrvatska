import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..scraping.croatia_scraper import scrape_croatia_events
from ..scraping.entrio_scraper import scrape_entrio_events
from ..tasks.celery_tasks import (
    scrape_all_sites_task,
    scrape_croatia_task,
    scrape_entrio_task,
)

router = APIRouter(prefix="/scraping", tags=["scraping"])


class ScrapeResponse(BaseModel):
    status: str
    message: str
    scraped_events: Optional[int] = None
    saved_events: Optional[int] = None
    task_id: Optional[str] = None


class ScrapeRequest(BaseModel):
    max_pages: int = 5
    use_playwright: bool = True


@router.post("/entrio", response_model=ScrapeResponse)
async def scrape_entrio(request: ScrapeRequest):
    """
    Trigger Entrio.hr event scraping.
    This will scrape events and save them to the database.
    """
    try:
        # For immediate execution (useful for testing)
        if request.max_pages <= 2:
            result = await scrape_entrio_events(max_pages=request.max_pages)
            return ScrapeResponse(**result)

        # For larger scraping jobs, delegate to Celery
        task = scrape_entrio_task.delay(max_pages=request.max_pages)
        return ScrapeResponse(
            status="accepted",
            message=f"Scraping task queued for {request.max_pages} pages",
            task_id=task.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start scraping: {str(e)}"
        )


@router.get("/entrio/quick", response_model=ScrapeResponse)
async def quick_scrape_entrio(
    max_pages: int = Query(
        1, ge=1, le=3, description="Number of pages to scrape (1-3 for quick scraping)"
    )
):
    """
    Quick Entrio.hr event scraping for immediate results.
    Limited to 3 pages maximum for fast response.
    """
    try:
        result = await scrape_entrio_events(max_pages=max_pages)
        return ScrapeResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/croatia", response_model=ScrapeResponse)
async def scrape_croatia(request: ScrapeRequest):
    """
    Trigger Croatia.hr event scraping.
    This will scrape events from https://croatia.hr/hr-hr/dogadanja and save them to the database.
    """
    try:
        # For immediate execution (useful for testing)
        if request.max_pages <= 2:
            result = await scrape_croatia_events(max_pages=request.max_pages)
            return ScrapeResponse(**result)

        # For larger scraping jobs, delegate to Celery
        task = scrape_croatia_task.delay(max_pages=request.max_pages)
        return ScrapeResponse(
            status="accepted",
            message=f"Croatia.hr scraping task queued for {request.max_pages} pages",
            task_id=task.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start Croatia.hr scraping: {str(e)}"
        )


@router.get("/croatia/quick", response_model=ScrapeResponse)
async def quick_scrape_croatia(
    max_pages: int = Query(
        1, ge=1, le=3, description="Number of pages to scrape (1-3 for quick scraping)"
    )
):
    """
    Quick Croatia.hr event scraping for immediate results.
    Limited to 3 pages maximum for fast response.
    """
    try:
        result = await scrape_croatia_events(max_pages=max_pages)
        return ScrapeResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Croatia.hr scraping failed: {str(e)}"
        )


@router.post("/all", response_model=ScrapeResponse)
async def scrape_all_sites(request: ScrapeRequest):
    """
    Trigger scraping from all supported sites (Entrio.hr and Croatia.hr).
    This will scrape events from both sites and save them to the database.
    """
    try:
        # For small requests, run immediately
        if request.max_pages <= 2:
            results = await asyncio.gather(
                scrape_entrio_events(max_pages=request.max_pages),
                scrape_croatia_events(max_pages=request.max_pages),
            )
            total_scraped = sum(r.get("scraped_events", 0) for r in results)
            total_saved = sum(r.get("saved_events", 0) for r in results)
            return ScrapeResponse(
                status="success",
                message=f"Scraped from all sites: {total_scraped} events total, {total_saved} new events saved",
                scraped_events=total_scraped,
                saved_events=total_saved,
            )

        task = scrape_all_sites_task.delay(max_pages=request.max_pages)
        return ScrapeResponse(
            status="accepted",
            message=f"Multi-site scraping task queued for {request.max_pages} pages per site",
            task_id=task.id,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start multi-site scraping: {str(e)}"
        )


@router.get("/status")
async def scraping_status():
    """Get scraping system status and configuration."""
    import os

    config = {
        "use_proxy": os.getenv("USE_PROXY", "0") == "1",
        "use_playwright": os.getenv("USE_PLAYWRIGHT", "1") == "1",
        "use_scraping_browser": os.getenv("USE_SCRAPING_BROWSER", "0") == "1",
        "brightdata_configured": bool(os.getenv("BRIGHTDATA_USER"))
        and bool(os.getenv("BRIGHTDATA_PASSWORD")),
    }

    return {
        "status": "operational",
        "config": config,
        "supported_sites": ["entrio.hr", "croatia.hr"],
        "endpoints": {
            "POST /scraping/entrio": "Entrio.hr full scraping with background processing",
            "GET /scraping/entrio/quick": "Entrio.hr quick scraping (1-3 pages)",
            "POST /scraping/croatia": "Croatia.hr full scraping with background processing",
            "GET /scraping/croatia/quick": "Croatia.hr quick scraping (1-3 pages)",
            "POST /scraping/all": "Scrape all supported sites",
            "GET /scraping/status": "System status",
        },
    }
