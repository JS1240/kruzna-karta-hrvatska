import asyncio

from ..celery_app import celery_app
from ..scraping.croatia_scraper import scrape_croatia_events
from ..scraping.entrio_scraper import scrape_entrio_events


@celery_app.task(name="scrape_entrio")
def scrape_entrio_task(max_pages: int = 5):
    try:
        return asyncio.run(scrape_entrio_events(max_pages=max_pages))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="scrape_croatia")
def scrape_croatia_task(max_pages: int = 5):
    try:
        return asyncio.run(scrape_croatia_events(max_pages=max_pages))
    except Exception as e:
        return {"status": "error", "message": str(e)}


@celery_app.task(name="scrape_all_sites")
def scrape_all_sites_task(max_pages: int = 5):
    results = []
    try:
        entrio_result = asyncio.run(scrape_entrio_events(max_pages=max_pages))
        results.append(("Entrio.hr", entrio_result))
        croatia_result = asyncio.run(scrape_croatia_events(max_pages=max_pages))
        results.append(("Croatia.hr", croatia_result))
        total_scraped = sum(r[1].get("scraped_events", 0) for r in results)
        total_saved = sum(r[1].get("saved_events", 0) for r in results)
        return {
            "status": "success",
            "scraped_events": total_scraped,
            "saved_events": total_saved,
            "details": {site: r for site, r in results},
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "details": results}
