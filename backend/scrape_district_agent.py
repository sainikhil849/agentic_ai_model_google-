"""
District.in Multi-City Scraper - Using Verified Working Agent
This uses the proven DistrictAgent from agents/platforms.py
"""

import sys
import logging
import json
import os
from typing import Dict, List

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.platforms import DistrictAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def scrape_district_multi_city():
    """Scrape actual District.in events for multiple cities"""
    
    logger.info("\n" + "="*80)
    logger.info("DISTRICT.IN MULTI-CITY SCRAPER")
    logger.info("Using verified DistrictAgent (same code that worked for Hyderabad)")
    logger.info("="*80 + "\n")
    
    agent = DistrictAgent()
    
    cities = ["Mumbai", "Delhi", "Chennai", "Pune"]
    all_events = {}
    
    for city in cities:
        logger.info(f"\n{'='*80}")
        logger.info(f"Scraping: {city}")
        logger.info(f"{'='*80}")
        
        try:
            # Use agent's run_sync_extraction method (100 events per city)
            events = agent.run_sync_extraction(location=city, target_count=100, max_price=None)
            
            all_events[city] = events
            logger.info(f"\n✓ Successfully scraped {len(events)} events from District for {city}")
            
            # Show sample
            if events:
                logger.info(f"\nSample event from {city}:")
                event = events[0]
                logger.info(f"  Name: {event.get('name', 'N/A')[:60]}")
                logger.info(f"  URL: {event.get('url', event.get('event_link', 'N/A'))[:80]}")
                logger.info(f"  Price: {event.get('price', 'N/A')}")
                logger.info(f"  Venue: {event.get('venue', 'N/A')[:50]}")
                logger.info(f"  Date: {event.get('date', 'N/A')}")
        
        except Exception as e:
            logger.error(f"Error scraping {city}: {e}")
            all_events[city] = []
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*80)
    
    total = 0
    for city, events in all_events.items():
        count = len(events)
        total += count
        logger.info(f"{city}: {count} REAL District.in events")
        
        # Count by field availability
        names = len([e for e in events if e.get('name')])
        urls = len([e for e in events if e.get('url') or e.get('event_link')])
        prices = len([e for e in events if e.get('price')])
        venues = len([e for e in events if e.get('venue')])
        
        logger.info(f"  Fields: {names} names | {urls} URLs | {prices} prices | {venues} venues")
    
    logger.info(f"\nTOTAL: {total} real District.in events")
    logger.info("="*80 + "\n")
    
    return all_events

if __name__ == "__main__":
    all_events = scrape_district_multi_city()
    
    # Save to JSON
    os.makedirs("exports", exist_ok=True)
    
    export_file = "exports/district_multi_city_agent.json"
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved to: {export_file}")
