from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import asyncio

from ..scraping.entrio_scraper import scrape_entrio_events
from ..scraping.croatia_scraper import scrape_croatia_events

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


async def run_scraping_task(max_pages: int, task_id: str):
    """Background task to run scraping."""
    try:
        result = await scrape_entrio_events(max_pages=max_pages)
        # In a real implementation, you'd store this result somewhere
        # accessible by task_id (Redis, database, etc.)
        print(f"Scraping task {task_id} completed: {result}")
        return result
    except Exception as e:
        print(f"Scraping task {task_id} failed: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/entrio", response_model=ScrapeResponse)
async def scrape_entrio(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Entrio.hr event scraping.
    This will scrape events and save them to the database.
    """
    try:
        # For immediate execution (useful for testing)
        if request.max_pages <= 2:
            result = await scrape_entrio_events(max_pages=request.max_pages)
            return ScrapeResponse(**result)
        
        # For larger scraping jobs, run in background
        import uuid
        task_id = str(uuid.uuid4())
        
        background_tasks.add_task(
            run_scraping_task, 
            max_pages=request.max_pages,
            task_id=task_id
        )
        
        return ScrapeResponse(
            status="accepted",
            message=f"Scraping task started in background for {request.max_pages} pages",
            task_id=task_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")


@router.get("/entrio/quick", response_model=ScrapeResponse)
async def quick_scrape_entrio(
    max_pages: int = Query(1, ge=1, le=3, description="Number of pages to scrape (1-3 for quick scraping)")
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
async def scrape_croatia(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger Croatia.hr event scraping.
    This will scrape events from https://croatia.hr/hr-hr/dogadanja and save them to the database.
    """
    try:
        # For immediate execution (useful for testing)
        if request.max_pages <= 2:
            result = await scrape_croatia_events(max_pages=request.max_pages)
            return ScrapeResponse(**result)
        
        # For larger scraping jobs, run in background
        import uuid
        task_id = str(uuid.uuid4())
        
        async def run_croatia_scraping_task():
            return await scrape_croatia_events(max_pages=request.max_pages)
        
        background_tasks.add_task(run_croatia_scraping_task)
        
        return ScrapeResponse(
            status="accepted",
            message=f"Croatia.hr scraping task started in background for {request.max_pages} pages",
            task_id=task_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start Croatia.hr scraping: {str(e)}")


@router.get("/croatia/quick", response_model=ScrapeResponse)
async def quick_scrape_croatia(
    max_pages: int = Query(1, ge=1, le=3, description="Number of pages to scrape (1-3 for quick scraping)")
):
    """
    Quick Croatia.hr event scraping for immediate results.
    Limited to 3 pages maximum for fast response.
    """
    try:
        result = await scrape_croatia_events(max_pages=max_pages)
        return ScrapeResponse(**result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Croatia.hr scraping failed: {str(e)}")


@router.post("/all", response_model=ScrapeResponse)
async def scrape_all_sites(
    request: ScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger scraping from all supported sites (Entrio.hr and Croatia.hr).
    This will scrape events from both sites and save them to the database.
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())
        
        async def run_all_scraping_tasks():
            results = []
            try:
                # Scrape Entrio.hr
                entrio_result = await scrape_entrio_events(max_pages=request.max_pages)
                results.append(("Entrio.hr", entrio_result))
                
                # Scrape Croatia.hr
                croatia_result = await scrape_croatia_events(max_pages=request.max_pages)
                results.append(("Croatia.hr", croatia_result))
                
                # Combine results
                total_scraped = sum(result[1].get("scraped_events", 0) for result in results)
                total_saved = sum(result[1].get("saved_events", 0) for result in results)
                
                return {
                    "status": "success",
                    "scraped_events": total_scraped,
                    "saved_events": total_saved,
                    "message": f"Scraped from all sites: {total_scraped} events total, {total_saved} new events saved",
                    "details": {site: result for site, result in results}
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Multi-site scraping failed: {str(e)}",
                    "details": results
                }
        
        # For small requests, run immediately
        if request.max_pages <= 2:
            result = await run_all_scraping_tasks()
            return ScrapeResponse(**result)
        
        # For larger requests, run in background
        background_tasks.add_task(run_all_scraping_tasks)
        
        return ScrapeResponse(
            status="accepted",
            message=f"Multi-site scraping task started for {request.max_pages} pages per site",
            task_id=task_id
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start multi-site scraping: {str(e)}")


@router.get("/status")
async def scraping_status():
    """Get scraping system status and configuration."""

    from ..core.config import settings

    config = {
        "use_proxy": settings.use_proxy,
        "use_playwright": settings.use_playwright,
        "use_scraping_browser": settings.use_scraping_browser,
        "brightdata_configured": bool(settings.brightdata_user) and bool(settings.brightdata_password),
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
            "GET /scraping/status": "System status"
        }
    }