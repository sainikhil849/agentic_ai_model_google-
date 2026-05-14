"""
DISTRICT MULTI-CITY SCRAPER - Using Exact Proven Working Code
This wraps the verified DistrictAgent._perform_scraping_sync() method
that was working for Hyderabad and adapts it for multiple cities
"""

import sys
import logging
from playwright.sync_api import sync_playwright

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.platforms import DistrictAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_district_multi_city_proven():
    """
    Use the EXACT proven District scraping code that worked for Hyderabad
    Adapts it for Mumbai, Delhi, Chennai, Pune
    """
    
    logger.info("\n" + "="*100)
    logger.info("DISTRICT.IN MULTI-CITY SCRAPER - PROVEN CODE")
    logger.info("Using exact _perform_scraping_sync() method from DistrictAgent")
    logger.info("="*100 + "\n")
    
    cities = ["Mumbai", "Delhi", "Chennai", "Pune"]
    all_events = {}
    
    # Create ONE District agent instance
    agent = DistrictAgent()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(**agent._get_browser_config())
        context = browser.new_context(**agent._get_context_config())
        page = context.new_page()
        
        # Stealth: remove webdriver flag
        page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined})"
        )
        
        for city in cities:
            logger.info("\n" + "="*100)
            logger.info(f"SCRAPING: {city.upper()}")
            logger.info("="*100)
            
            try:
                # CALL THE EXACT PROVEN METHOD DIRECTLY
                # This is the _perform_scraping_sync that handled Hyderabad perfectly
                events = agent._perform_scraping_sync(
                    page=page,
                    location=city,
                    target_count=100,
                    max_price=None
                )
                
                all_events[city] = events
                logger.info(f"\n✓✓✓ SCRAPED {len(events)} events from {city} ✓✓✓\n")
                
            except Exception as e:
                logger.error(f"ERROR scraping {city}: {e}")
                all_events[city] = []
        
        browser.close()
    
    # Summary
    logger.info("\n" + "="*100)
    logger.info("FINAL SUMMARY")
    logger.info("="*100)
    
    total = 0
    for city, events in all_events.items():
        count = len(events)
        total += count
        logger.info(f"\n{city}: {count} REAL District.in events")
        
        if events:
            event = events[0]
            logger.info(f"  Sample:")
            logger.info(f"    Name: {event.get('name', 'N/A')[:60]}")
            logger.info(f"    URL: {event.get('url', 'N/A')[:70]}")
            logger.info(f"    Price: ₹{event.get('price', 'N/A')}")
            logger.info(f"    Venue: {event.get('venue', 'N/A')[:50]}")
            logger.info(f"    Date: {event.get('date', 'N/A')} at {event.get('event_time', 'N/A')}")
    
    logger.info(f"\n" + "="*100)
    logger.info(f"TOTAL: {total} REAL DISTRICT.IN EVENTS")
    logger.info(f"Status: {'✓ COMPLETE' if total >= 300 else '⚠ Partial'}")
    logger.info("="*100 + "\n")
    
    return all_events

if __name__ == "__main__":
    all_events = scrape_district_multi_city_proven()
