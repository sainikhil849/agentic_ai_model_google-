"""
Debug District Scraper - Investigate why 0 events are being scraped
"""

import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())     

import time
from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_district():
    """Debug the district.in scraper step by step"""

    print("\n" + "="*100)
    print("DISTRICT SCRAPER DEBUG - Investigating 0 Events Issue")
    print("="*100 + "\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            url = "https://www.district.in/events-in-hyderabad/"
            print(f"Navigating to: {url}\n")

            page.goto(url, wait_until="networkidle", timeout=45000)
            print("Page loaded successfully\n")

            # Check page title
            title = page.title()
            print(f"Page Title: {title}\n")

            # Check for common event container selectors
            selectors_to_check = [
                "a:has(h3)",
                "a[class*='dds-h-full']",
                "a[class*='event']",
                ".event-card",
                "[class*='EventCard']",
                "div[class*='event']",
                "a.event",
                "article",
                "div[role='article']",
                ".card",
                ".listing-item"
            ]

            print("Checking selectors for event cards:\n")
            for selector in selectors_to_check:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"✓ {selector:<30} -> Found {len(elements)} elements")

                        # Show first element details
                        first = elements[0]
                        href = first.get_attribute("href") if first.tag_name == "a" else "N/A"
                        inner_text = first.inner_text()
                        text = inner_text[:100] if inner_text else "N/A"
                        print(f"  ├─ First element href: {href}")
                        print(f"  └─ Text preview: {text}\n")
                    else:
                        print(f"✗ {selector:<30} -> 0 elements\n")
                except Exception as e:
                    print(f"✗ {selector:<30} -> Error: {str(e)[:50]}\n")      

            # Try to find any links with "events" in href
            print("\nSearching for links with 'events' in href:\n")
            all_links = page.query_selector_all("a")
            event_links = [link for link in all_links if "events" in (link.get_attribute("href") or "").lower()]

            if event_links:
                print(f"✓ Found {len(event_links)} links with 'events' in href")
                for i, link in enumerate(event_links[:5]):
                    href = link.get_attribute("href")
                    text = link.inner_text()[:80]
                    print(f"  {i+1}. {text}")
                    print(f"     -> {href}\n")
            else:
                print("✗ No links with 'events' found\n")

            # Check page structure
            print("\nPage Structure Analysis:\n")

            # Count all event-like elements
            all_articles = page.query_selector_all("article")
            print(f"Articles found: {len(all_articles)}")

            all_divs_with_class = page.query_selector_all("div[class]")
            print(f"Divs with class: {len(all_divs_with_class)}")

            # Try to get page content sample
            body_text = page.locator("body").inner_text()
            if body_text:
                lines = body_text.split('\n')[:20]
                print(f"\nFirst 20 lines of page text:")
                for i, line in enumerate(lines, 1):
                    if line.strip():
                        print(f"  {i}. {line[:80]}")

            print("\n" + "="*100)
            print("DEBUG COMPLETE - Press Enter or type 'y' to close browser and exit")
            print("="*100)

        finally:
            input("Press Enter to close browser...")
            browser.close()

if __name__ == "__main__":
    debug_district()