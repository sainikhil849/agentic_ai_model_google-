"""
District Multi-City Scraper - REAL DATA WITH WORKING LINKS
Uses the original working scrape_district function with city parameters
"""

import sys
import json
import logging
import time
from typing import List, Dict

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.scrapers import scrape_district

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CITIES = ['mumbai', 'delhi', 'chennai', 'pune']

def scrape_all_cities(target_per_city: int = 100):
    """Scrape REAL events from District for all cities"""
    
    logger.info("\n" + "="*80)
    logger.info("DISTRICT REAL DATA SCRAPER - ALL CITIES")
    logger.info("="*80 + "\n")
    
    all_events = {}
    
    for city in CITIES:
        logger.info(f"\n{'='*80}")
        logger.info(f"SCRAPING: {city.upper()}")
        logger.info(f"{'='*80}")
        
        # Use the original working scrape_district function
        events = scrape_district(city, target_per_city)
        
        logger.info(f"\n✓ Scraped {len(events)} events from {city.upper()}")
        
        # Store events
        city_name = city.capitalize()
        all_events[city_name] = events
        
        if events:
            logger.info("\nSample events:")
            for event in events[:3]:
                logger.info(f"  - {event.get('event_name', 'N/A')}")
                logger.info(f"    Price: ₹{event.get('price', 'N/A')}")
                logger.info(f"    URL: {event.get('event_url', 'N/A')}")
        
        time.sleep(2)  # Respectful delay between cities
    
    # Save to JSON
    logger.info("\n" + "="*80)
    logger.info("SAVING DATA")
    logger.info("="*80)
    
    consolidated_file = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_real_consolidated.json'
    with open(consolidated_file, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved: {consolidated_file}")
    
    # Save individual city files
    for city_name, events in all_events.items():
        filename = rf'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_{city_name.lower()}_real.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({city_name: events}, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved: {filename}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*80)
    total = 0
    for city_name, events in all_events.items():
        count = len(events)
        total += count
        logger.info(f"{city_name}: {count} events (REAL with working links)")
    logger.info(f"TOTAL: {total} REAL events")
    logger.info("="*80 + "\n")
    
    return all_events

if __name__ == "__main__":
    all_events = scrape_all_cities(target_per_city=100)
