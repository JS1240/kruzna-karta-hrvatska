"""
Improved Entrio.hr scraper with better anti-detection
"""
import asyncio
import random
from typing import Dict, List
from playwright.async_api import async_playwright

class ImprovedEntrioScraper:
    """Improved scraper with better anti-detection techniques."""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]
    
    async def scrape_with_stealth(self, max_pages: int = 3) -> List[Dict]:
        """Scrape with anti-detection techniques."""
        events = []
        
        async with async_playwright() as p:
            # Launch browser with stealth options
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-features=VizDisplayCompositor',
                    '--user-agent=' + random.choice(self.user_agents)
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(self.user_agents),
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True,
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,hr;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            page = await context.new_page()
            
            # Add stealth scripts
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'hr'],
                });
                
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Cypress.env('NOTIFICATION_PERMISSION') || 'granted' }) :
                        originalQuery(parameters)
                );
            """)
            
            # Try different URL patterns
            urls_to_try = [
                "https://entrio.hr/",
                "https://www.entrio.hr/",
                "https://entrio.hr/hr",
                "https://entrio.hr/en"
            ]
            
            working_url = None
            for url in urls_to_try:
                try:
                    print(f"Trying: {url}")
                    
                    # Add random delay
                    await asyncio.sleep(random.uniform(2, 5))
                    
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    
                    if response and response.status == 200:
                        print(f"Success with: {url} (Status: {response.status})")
                        working_url = url
                        break
                    else:
                        print(f"Failed: {url} (Status: {response.status if response else 'No response'})")
                        
                except Exception as e:
                    print(f"Error with {url}: {e}")
                    continue
            
            if not working_url:
                print("Could not access Entrio.hr - all URLs blocked")
                await browser.close()
                return []
            
            # Wait for page to load completely
            await page.wait_for_timeout(3000)
            
            # Look for events on the main page or find events link
            print("Looking for events on the page...")
            
            # Try to find events section or link
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    
                    // Look for event-related elements
                    const selectors = [
                        'a[href*="event"]',
                        'a[href*="dogadaj"]',
                        '.event',
                        '[class*="event"]',
                        '[data-event]',
                        'article',
                        '.card'
                    ];
                    
                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            console.log(`Found ${elements.length} elements with selector: ${selector}`);
                            
                            Array.from(elements).forEach((element, index) => {
                                if (index < 10) { // Limit to first 10 for debugging
                                    const data = {};
                                    
                                    // Extract link
                                    const linkEl = element.querySelector('a') || element;
                                    if (linkEl && linkEl.href) {
                                        data.link = linkEl.href;
                                    }
                                    
                                    // Extract text content
                                    const textContent = element.textContent?.trim();
                                    if (textContent && textContent.length > 5) {
                                        data.text = textContent.substring(0, 200);
                                    }
                                    
                                    // Extract title from various elements
                                    const titleSelectors = ['h1', 'h2', 'h3', 'h4', '.title', '[class*="title"]'];
                                    for (const titleSel of titleSelectors) {
                                        const titleEl = element.querySelector(titleSel);
                                        if (titleEl && titleEl.textContent?.trim()) {
                                            data.title = titleEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    if (data.link || data.title) {
                                        events.push(data);
                                    }
                                }
                            });
                            
                            if (events.length > 0) break;
                        }
                    }
                    
                    return events;
                }
            """)
            
            print(f"Found {len(events_data)} potential events")
            
            # If we found events, process them
            for event_data in events_data:
                if 'event' in event_data.get('link', '').lower() or 'dogadaj' in event_data.get('link', '').lower():
                    events.append({
                        'title': event_data.get('title', 'Entrio Event'),
                        'link': event_data.get('link', ''),
                        'date': '2025-06-20',  # Default date for now
                        'venue': 'Zagreb, Croatia',  # Default venue
                        'description': event_data.get('text', '')[:200] if event_data.get('text') else ''
                    })
            
            await browser.close()
        
        print(f"Extracted {len(events)} events")
        return events

# Test function
async def test_improved_scraper():
    scraper = ImprovedEntrioScraper()
    events = await scraper.scrape_with_stealth()
    print(f"Final result: {len(events)} events")
    for i, event in enumerate(events[:3]):
        print(f"Event {i+1}: {event}")

if __name__ == "__main__":
    asyncio.run(test_improved_scraper())