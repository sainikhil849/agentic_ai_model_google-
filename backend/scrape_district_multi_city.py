"""
Multi-City District Scraper
Scrapes 100 events from Mumbai, Delhi, Chennai, and Pune
Outputs: event_name, event_url, price, description, venue_location, event_date, event_time
"""

import sys
import asyncio
import json
import logging
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add backend to path for imports
sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from utils.price_extractor import extract_price
from utils.date_extractor import extract_date

CITIES = {
    'mumbai': 'Mumbai',
    'delhi': 'Delhi',
    'chennai': 'Chennai',
    'pune': 'Pune'
}

def _get_browser_config():
    """Browser configuration for visible scraping"""
    return {
        "headless": False,
        "args": ["--disable-blink-features=AutomationControlled"]
    }

def _get_context_config():
    return {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "viewport": {"width": 1280, "height": 720}
    }

def extract_event_details(page, event_url: str, city: str) -> Optional[Dict]:
    """Extract detailed event information from event page"""
    try:
        page.goto(event_url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(1.5)
        
        # Extract basic info
        body_text = page.inner_text("body")
        
        # Extract event name (from h1 or title)
        event_name = ""
        h1 = page.query_selector("h1")
        if h1:
            event_name = h1.inner_text().strip()
        else:
            event_name = page.title()
        
        # Extract price
        price = 0
        price_pattern = r"(?:₹|INR|Rs\.?|Price[\s:]*)?(\d{1,5}(?:,\d{3})*(?:\.\d+)?)"
        price_matches = re.findall(price_pattern, body_text, re.IGNORECASE)
        if price_matches:
            price = extract_price(price_matches[0])
        
        # Extract description
        description = ""
        desc_selectors = [
            "div[class*='description']",
            "div[class*='about']",
            "p[class*='summary']",
            "meta[name='description']"
        ]
        for selector in desc_selectors:
            elem = page.query_selector(selector)
            if elem:
                desc = elem.inner_text() if "meta" not in selector else elem.get_attribute("content")
                if desc and len(desc.strip()) > 10:
                    description = desc.strip()[:300]
                    break
        
        if not description:
            description = body_text[:200].strip()
        
        # Extract venue location
        venue_location = ""
        venue_selectors = [
            "span[class*='location']",
            "span[class*='venue']",
            "div[class*='address']",
            "p:has-text('Address')",
            "p:has-text('Venue')"
        ]
        for selector in venue_selectors:
            try:
                elem = page.query_selector(selector)
                if elem:
                    venue = elem.inner_text().strip()
                    if venue and len(venue) > 3:
                        venue_location = venue[:100]
                        break
            except:
                continue
        
        if not venue_location:
            venue_location = city  # Default to city if not found
        
        # Extract date and time
        event_date = "2025-01-01"
        event_time = "TBD"
        
        date_pattern = r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})"
        time_pattern = r"(\d{1,2}:\d{2}\s?(?:AM|PM|am|pm)?)"
        
        date_matches = re.findall(date_pattern, body_text)
        if date_matches:
            event_date = date_matches[0]
        
        time_matches = re.findall(time_pattern, body_text)
        if time_matches:
            event_time = time_matches[0].strip()
        
        return {
            "event_name": event_name or "Event",
            "event_url": event_url,
            "price": max(price, 0),
            "description": description or "District Event",
            "venue_location": venue_location,
            "event_date": event_date,
            "event_time": event_time,
            "city": city,
            "platform": "District"
        }
    except Exception as e:
        logger.warning(f"Error extracting details from {event_url}: {e}")
        return None

def scrape_district_city(city: str, target_count: int = 100) -> List[Dict]:
    """Scrape District events for a specific city"""
    logger.info(f"\n{'='*80}")
    logger.info(f"STARTING DISTRICT SCRAPE FOR {city.upper()} (Target: {target_count} events)")
    logger.info(f"{'='*80}")
    
    events = []
    city_lower = city.lower()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(**_get_browser_config())
        context = browser.new_context(**_get_context_config())
        page = context.new_page()
        
        try:
            # Navigate to city events page
            url = f"https://www.district.in/events-in-{city_lower}/"
            logger.info(f"Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=45000)
            
            # Scroll to load more events
            for scroll_num in range(5):  # Scroll 5 times to load more
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                time.sleep(1.5)
                logger.info(f"Scroll #{scroll_num + 1}")
            
            # Extract event cards
            event_links = set()  # Use set to avoid duplicates
            cards = page.query_selector_all("a[href*='/event/'], a[class*='event']")
            logger.info(f"Found {len(cards)} event cards")
            
            for card in cards:
                try:
                    href = card.get_attribute("href")
                    if href and "event" in href.lower():
                        full_url = f"https://www.district.in{href}" if href.startswith("/") else href
                        event_links.add(full_url)
                except:
                    continue
            
            logger.info(f"Extracted {len(event_links)} unique event links")
            
            # Scrape details for each event
            for idx, event_url in enumerate(list(event_links)[:target_count], 1):
                if len(events) >= target_count:
                    break
                
                logger.info(f"[{idx}/{target_count}] Scraping: {event_url}")
                
                event_details = extract_event_details(page, event_url, city)
                if event_details:
                    events.append(event_details)
                    logger.info(f"✓ Added: {event_details['event_name']} - ₹{event_details['price']}")
                else:
                    logger.warning(f"✗ Failed to extract: {event_url}")
                
                time.sleep(0.5)  # Respectful delay
        
        except Exception as e:
            logger.error(f"Error scraping {city}: {e}")
        finally:
            browser.close()
    
    logger.info(f"\n{'─'*80}")
    logger.info(f"COMPLETED: {city.upper()} - Scraped {len(events)} events")
    logger.info(f"{'─'*80}\n")
    
    return events

def save_events_to_json(all_events: Dict[str, List[Dict]], output_file: str):
    """Save all events to JSON"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, indent=2, ensure_ascii=False)
    logger.info(f"✓ Saved to: {output_file}")

def main():
    """Main scraping orchestration"""
    start_time = time.time()
    
    all_events = {}
    
    # Scrape each city
    for city_lower, city_display in CITIES.items():
        events = scrape_district_city(city_display, target_count=100)
        all_events[city_display] = events
        logger.info(f"\n{city_display}: {len(events)} events collected\n")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("SCRAPING SUMMARY")
    logger.info("="*80)
    total_events = 0
    for city, events in all_events.items():
        logger.info(f"{city}: {len(events)} events")
        total_events += len(events)
    logger.info(f"TOTAL: {total_events} events")
    logger.info("="*80 + "\n")
    
    # Save to JSON
    json_file = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports\district_multi_city.json'
    save_events_to_json(all_events, json_file)
    
    # Print sample events
    logger.info("\nSAMPLE EVENTS:")
    for city, events in all_events.items():
        if events:
            logger.info(f"\n{city}:")
            for event in events[:3]:
                logger.info(f"  - {event['event_name']} | ₹{event['price']} | {event['venue_location']}")
    
    elapsed = time.time() - start_time
    logger.info(f"\n✓ Total time: {elapsed:.1f} seconds")

if __name__ == "__main__":
    main()
