#!/usr/bin/env python3
"""
Debug script to investigate Entrio website structure
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_entrio():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Try different URLs
        urls_to_try = [
            "https://entrio.hr/events",
            "https://entrio.hr/en/events", 
            "https://entrio.hr/hr/events",
            "https://entrio.hr/",
            "https://www.entrio.hr/",
            "https://www.entrio.hr/en/events",
            "https://www.entrio.hr/hr/events"
        ]
        
        for url in urls_to_try:
            try:
                print(f"\n=== Trying URL: {url} ===")
                response = await page.goto(url, timeout=30000)
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    # Get the page title
                    title = await page.title()
                    print(f"Title: {title}")
                    
                    # Check for event elements
                    selectors_to_check = [
                        'a[href*="/event/"]',
                        'a[href*="/dogadaj/"]', 
                        '.event-card',
                        '.event-item',
                        '.poster-image',
                        '[class*="event"]'
                    ]
                    
                    for selector in selectors_to_check:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"Found {len(elements)} elements with selector: {selector}")
                    
                    # Get some sample HTML
                    html_sample = await page.content()
                    print(f"HTML length: {len(html_sample)}")
                    
                    # Check if there are any links that look like events
                    event_links = await page.evaluate("""
                        () => {
                            const links = Array.from(document.querySelectorAll('a[href]'));
                            return links
                                .map(link => link.href)
                                .filter(href => href.includes('event') || href.includes('dogadaj'))
                                .slice(0, 5);
                        }
                    """)
                    
                    if event_links:
                        print(f"Sample event links found: {event_links}")
                    else:
                        print("No event links found")
                    
                    # Save a screenshot for manual inspection
                    await page.screenshot(path=f"/tmp/entrio_{url.replace('://', '_').replace('/', '_')}.png")
                    print(f"Screenshot saved to /tmp/entrio_{url.replace('://', '_').replace('/', '_')}.png")
                    
                    break  # If we found a working URL, stop trying
                    
            except Exception as e:
                print(f"Error with {url}: {e}")
                continue
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_entrio())