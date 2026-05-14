import sys
import os
import asyncio
import logging
from playwright.sync_api import sync_playwright

# Add current directory to path to import agents
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.platforms import MeraEventsAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestMeraEvents")

def test_meraevents():
    agent = MeraEventsAgent()
    location = "Hyderabad"
    target_count = 5
    
    logger.info(f"Starting test for MeraEvents in {location}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        # Test specific virtual event
        logger.info("Testing specific virtual event...")
        virtual_cand = {"url": "https://www.meraevents.com/event/GAH-2026", "location": "Online"}
        enriched = agent._enrich_event_details(page, virtual_cand)
        formatted = agent._format_event(enriched)
        if formatted:
            logger.info(f"✓ Formatted Virtual Event: {formatted.get('event_name')}")
            logger.info(f"  Price: {formatted.get('price')}")
            logger.info(f"  Event ID: {formatted.get('event_id')}")
            logger.info(f"  Format: {formatted.get('event_format')}")
            logger.info(f"  Venue: {formatted.get('venue')}")
            logger.info(f"  Organizer: {formatted.get('organizer_name')}")
        
        # Test _perform_scraping_sync
        logger.info("Testing _perform_scraping_sync...")
        candidates = agent._perform_scraping_sync(page, location, target_count, None)
        logger.info(f"Found {len(candidates)} candidates.")
        
        for cand in candidates[:2]:
            logger.info(f"Enriching: {cand['url']}")
            enriched = agent._enrich_event_details(page, cand)
            formatted = agent._format_event(enriched)
            if formatted:
                logger.info(f"✓ Formatted Event: {formatted.get('event_name')}")
                logger.info(f"  Price: {formatted.get('price')}")
                logger.info(f"  Event ID: {formatted.get('event_id')}")
                logger.info(f"  Format: {formatted.get('event_format')}")
                logger.info(f"  Price Tiers: {formatted.get('price_tiers')}")
                logger.info(f"  Organizer: {formatted.get('organizer_name')}")
            else:
                logger.warning(f"✘ Failed to format event: {cand['url']}")
        
        browser.close()

if __name__ == "__main__":
    test_meraevents()
