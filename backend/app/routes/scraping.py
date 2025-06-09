from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio

from ..scraping.entrio_scraper import scrape_entrio_events
from ..scraping.croatia_scraper import scrape_croatia_events
from ..scraping.enhanced_scraper import run_enhanced_scraping_pipeline, run_single_source_enhanced_scraping

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


class EnhancedScrapeRequest(BaseModel):
    max_pages_per_source: int = 5
    quality_threshold: float = 60.0
    enable_duplicate_detection: bool = True


class SingleSourceRequest(BaseModel):
    source: str  # "entrio" or "croatia"
    max_pages: int = 5
    quality_threshold: float = 60.0


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
    import os
    
    config = {
        "use_proxy": os.getenv("USE_PROXY", "0") == "1",
        "use_playwright": os.getenv("USE_PLAYWRIGHT", "1") == "1",
        "use_scraping_browser": os.getenv("USE_SCRAPING_BROWSER", "0") == "1",
        "brightdata_configured": bool(os.getenv("BRIGHTDATA_USER")) and bool(os.getenv("BRIGHTDATA_PASSWORD")),
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
            "POST /scraping/enhanced/pipeline": "Enhanced scraping pipeline with quality validation",
            "POST /scraping/enhanced/single": "Enhanced single source scraping",
            "GET /scraping/status": "System status"
        }
    }


# Enhanced Scraping Endpoints with Quality Validation

@router.post("/enhanced/pipeline")
async def enhanced_scraping_pipeline(
    request: EnhancedScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Enhanced scraping pipeline with comprehensive quality validation and duplicate detection.
    
    This endpoint runs the full enhanced pipeline that includes:
    - Multi-source scraping (Entrio.hr + Croatia.hr)
    - Data quality validation with configurable thresholds
    - Advanced duplicate detection (batch + database)
    - Comprehensive performance reporting
    - Smart data cleaning and normalization
    """
    try:
        import uuid
        task_id = str(uuid.uuid4())
        
        # For small requests, run immediately and return full results
        if request.max_pages_per_source <= 2:
            result = await run_enhanced_scraping_pipeline(
                max_pages_per_source=request.max_pages_per_source,
                quality_threshold=request.quality_threshold
            )
            
            # Extract summary for response
            summary = result.get("combined_results", {}).get("processing_summary", {})
            performance = result.get("performance_analysis", {}).get("performance_metrics", {})
            
            return {
                "status": "completed",
                "task_id": task_id,
                "message": "Enhanced scraping pipeline completed",
                "scraped_events": performance.get("total_events_scraped", 0),
                "saved_events": performance.get("total_events_saved", 0),
                "success_rate": summary.get("final_processable_count", 0) / summary.get("original_count", 1) * 100 if summary.get("original_count", 0) > 0 else 0,
                "quality_threshold": request.quality_threshold,
                "processing_time": result.get("total_processing_time", 0),
                "detailed_results": result
            }
        
        # For larger requests, run in background
        async def run_enhanced_background_task():
            try:
                result = await run_enhanced_scraping_pipeline(
                    max_pages_per_source=request.max_pages_per_source,
                    quality_threshold=request.quality_threshold
                )
                print(f"Enhanced scraping task {task_id} completed successfully")
                print(result.get("performance_report", "No performance report available"))
                return result
            except Exception as e:
                print(f"Enhanced scraping task {task_id} failed: {e}")
                return {"status": "error", "message": str(e), "task_id": task_id}
        
        background_tasks.add_task(run_enhanced_background_task)
        
        return {
            "status": "accepted",
            "task_id": task_id,
            "message": f"Enhanced scraping pipeline started in background for {request.max_pages_per_source} pages per source",
            "quality_threshold": request.quality_threshold,
            "duplicate_detection": request.enable_duplicate_detection,
            "estimated_time": f"{request.max_pages_per_source * 2 * 10}s"  # Rough estimate
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enhanced scraping pipeline: {str(e)}")


@router.post("/enhanced/single")
async def enhanced_single_source_scraping(
    request: SingleSourceRequest,
    background_tasks: BackgroundTasks
):
    """
    Enhanced single-source scraping with quality validation.
    
    Scrape from a single source (entrio or croatia) with full quality pipeline:
    - Advanced data validation and cleaning
    - Duplicate detection against existing database
    - Quality scoring and filtering
    - Detailed performance metrics
    """
    try:
        if request.source.lower() not in ["entrio", "croatia"]:
            raise HTTPException(status_code=400, detail="Source must be 'entrio' or 'croatia'")
        
        import uuid
        task_id = str(uuid.uuid4())
        
        # For small requests, run immediately
        if request.max_pages <= 3:
            result = await run_single_source_enhanced_scraping(
                source=request.source,
                max_pages=request.max_pages,
                quality_threshold=request.quality_threshold
            )
            
            # Extract key metrics for response
            scraping_results = result.get("scraping_results", {})
            summary = scraping_results.get("processing_summary", {})
            
            return {
                "status": result.get("status", "completed"),
                "task_id": task_id,
                "source": request.source,
                "message": f"Enhanced {request.source} scraping completed",
                "scraped_events": summary.get("original_count", 0),
                "saved_events": result.get("events_saved", 0),
                "quality_threshold": request.quality_threshold,
                "processing_time": result.get("total_duration", 0),
                "detailed_results": result
            }
        
        # For larger requests, run in background
        async def run_single_source_background_task():
            try:
                result = await run_single_source_enhanced_scraping(
                    source=request.source,
                    max_pages=request.max_pages,
                    quality_threshold=request.quality_threshold
                )
                print(f"Enhanced {request.source} scraping task {task_id} completed")
                return result
            except Exception as e:
                print(f"Enhanced {request.source} scraping task {task_id} failed: {e}")
                return {"status": "error", "message": str(e), "task_id": task_id}
        
        background_tasks.add_task(run_single_source_background_task)
        
        return {
            "status": "accepted",
            "task_id": task_id,
            "source": request.source,
            "message": f"Enhanced {request.source} scraping started in background for {request.max_pages} pages",
            "quality_threshold": request.quality_threshold,
            "estimated_time": f"{request.max_pages * 10}s"  # Rough estimate
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start enhanced {request.source} scraping: {str(e)}")


@router.get("/enhanced/demo")
async def enhanced_scraping_demo(
    source: str = Query("entrio", description="Source to demo (entrio or croatia)"),
    max_pages: int = Query(1, ge=1, le=2, description="Number of pages (1-2 for demo)")
):
    """
    Demo endpoint for enhanced scraping pipeline.
    
    This endpoint demonstrates the enhanced scraping capabilities with:
    - Real-time quality validation
    - Duplicate detection
    - Performance metrics
    - Detailed quality report
    """
    try:
        if source.lower() not in ["entrio", "croatia"]:
            raise HTTPException(status_code=400, detail="Source must be 'entrio' or 'croatia'")
        
        print(f"Starting enhanced scraping demo for {source} ({max_pages} pages)")
        
        result = await run_single_source_enhanced_scraping(
            source=source,
            max_pages=max_pages,
            quality_threshold=50.0  # Lower threshold for demo
        )
        
        # Extract comprehensive demo information
        scraping_results = result.get("scraping_results", {})
        quality_report = scraping_results.get("quality_report", {})
        
        demo_response = {
            "demo_info": {
                "source": source,
                "pages_scraped": max_pages,
                "quality_threshold": 50.0,
                "processing_time": result.get("total_duration", 0)
            },
            "scraping_summary": scraping_results.get("processing_summary", {}),
            "quality_metrics": quality_report.get("quality_metrics", {}),
            "duplicate_analysis": quality_report.get("duplicate_analysis", {}),
            "recommendations": quality_report.get("recommendations", []),
            "performance_insights": {
                "events_per_second": 0,
                "quality_score_avg": quality_report.get("quality_metrics", {}).get("average_quality_score", 0),
                "success_rate": quality_report.get("success_rate", 0)
            }
        }
        
        # Calculate events per second
        if result.get("total_duration", 0) > 0:
            original_count = scraping_results.get("processing_summary", {}).get("original_count", 0)
            demo_response["performance_insights"]["events_per_second"] = round(
                original_count / result["total_duration"], 2
            )
        
        return demo_response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced scraping demo failed: {str(e)}")