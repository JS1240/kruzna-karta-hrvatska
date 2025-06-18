#!/usr/bin/env python3
"""
Detailed debug script to see what's on the Entrio events page
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_entrio_detailed():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        page = await context.new_page()
        
        # Add stealth script
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        try:
            print("=== Accessing Entrio homepage ===")
            await page.goto("https://entrio.hr/", wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            
            title = await page.title()
            print(f"Homepage title: {title}")
            
            # Find events link
            events_links = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links
                        .map(link => ({ href: link.href, text: link.textContent?.trim() }))
                        .filter(link => link.href.includes('/events') && !link.href.includes('my_events'));
                }
            """)
            
            print(f"Found events links: {events_links}")
            
            if events_links:
                events_url = events_links[0]['href']
                print(f"\n=== Accessing events page: {events_url} ===")
                await page.goto(events_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(5000)  # Give more time for dynamic content
                
                events_title = await page.title()
                print(f"Events page title: {events_title}")
                
                # Check page content
                html_content = await page.content()
                print(f"Page HTML length: {len(html_content)}")
                
                # Look for any links with 'event' in them
                event_info = await page.evaluate("""
                    () => {
                        const info = {
                            allLinks: 0,
                            eventLinks: [],
                            allText: document.body.textContent?.substring(0, 500) || '',
                            hasSearch: false,
                            hasFilters: false
                        };
                        
                        // Count all links
                        const allLinks = document.querySelectorAll('a[href]');
                        info.allLinks = allLinks.length;
                        
                        // Find event links
                        const eventLinks = Array.from(allLinks)
                            .filter(link => link.href.includes('/event/') && !link.href.includes('my_event'))
                            .slice(0, 5)
                            .map(link => ({
                                href: link.href,
                                text: link.textContent?.trim()?.substring(0, 100) || '',
                                className: link.className || ''
                            }));
                        info.eventLinks = eventLinks;
                        
                        // Check for search and filters
                        info.hasSearch = document.querySelector('input[type="search"], input[placeholder*="search"], input[placeholder*="pretraži"]') !== null;
                        info.hasFilters = document.querySelector('.filter, .filters, [class*="filter"]') !== null;
                        
                        return info;
                    }
                """)
                
                print(f"\nPage analysis:")
                print(f"- Total links: {event_info['allLinks']}")
                print(f"- Event links found: {len(event_info['eventLinks'])}")
                print(f"- Has search: {event_info['hasSearch']}")
                print(f"- Has filters: {event_info['hasFilters']}")
                print(f"- Page text sample: {event_info['allText'][:200]}...")
                
                if event_info['eventLinks']:
                    print(f"\nSample event links:")
                    for i, link in enumerate(event_info['eventLinks']):
                        print(f"  {i+1}. {link['href']}")
                        print(f"     Text: {link['text']}")
                        print(f"     Class: {link['className']}")
                
                # Try scrolling down to load more content
                print(f"\n=== Trying to scroll and load more content ===")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)
                
                # Check again after scrolling
                event_info_after_scroll = await page.evaluate("""
                    () => {
                        const eventLinks = Array.from(document.querySelectorAll('a[href]'))
                            .filter(link => link.href.includes('/event/') && !link.href.includes('my_event'))
                            .slice(0, 10)
                            .map(link => ({
                                href: link.href,
                                text: link.textContent?.trim()?.substring(0, 100) || ''
                            }));
                        return eventLinks;
                    }
                """)
                
                print(f"Event links after scroll: {len(event_info_after_scroll)}")
                
                # Save screenshot for manual inspection
                await page.screenshot(path="/tmp/entrio_events_page.png")
                print(f"Screenshot saved to /tmp/entrio_events_page.png")
                
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_entrio_detailed())