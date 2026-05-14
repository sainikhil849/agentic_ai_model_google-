#!/usr/bin/env python3
"""
Test script for District scraper - FIXED VERSION
Focus: Direct URL-based city routing + proper event details extraction
Features:
- URL routing to city-specific pages (not localStorage)
- Improved date/time extraction
- Better artist page rejection
- Proper venue filtering
"""

import asyncio
import sys
import logging
import time
from datetime import datetime

# Windows fix for Playwright
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.platforms import DistrictAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

def test_district_scraper():
    """Test District scraper with 5 events target"""
    
    print("\n" + "="*80)
    print("TESTING DISTRICT SCRAPER WITH FIX")
    print("="*80)
    print(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Target: Bangalore")
    print("Max Events: 5")
    print("Focus: URL-based city routing + proper event details")
    print("="*80 + "\n")
    
    agent = DistrictAgent()
    start_time = time.time()
    
    try:
        # Test with Bangalore and 5 events target
        events = agent.run_sync_extraction(
            location="Bangalore",
            target_count=5,
            max_price=None
        )
        
        elapsed_time = time.time() - start_time
        
        print("\n" + "="*80)
        print("TEST RESULTS")
        print("="*80)
        print(f"Total Events Found: {len(events)}")
        print(f"Time Taken: {elapsed:.1f} seconds")
        print(f"Status: SUCCESS" if len(events) > 0 else "NO EVENTS")
        print("="*80 + "\n")
        
        if events:
            print("Event Details:")
            print("-" * 80)
            for idx, event in enumerate(events, 1):
                print(f"\n{idx}. {event.get('event_name', 'N/A')}")
                print(f"   Date: {event.get('event_date', 'N/A')}")
                print(f"   Time: {event.get('event_time', 'N/A')}")
                print(f"   Price: ₹{event.get('price', 'N/A')}")
                print(f"   Venue: {event.get('venue', 'Not specified')}")
                print(f"   Platform: {event.get('platform', 'N/A')}")
                print(f"   Link: {event.get('event_link', 'N/A')[:60]}...")
            print("\n" + "-" * 80)
        else:
            print("[!] No events were found during scraping")
        
        print(f"\nTest Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return len(events) > 0
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"\n✗ TEST FAILED")
        print(f"Error: {e}")
        print(f"Time Taken: {elapsed_time:.2f} seconds")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_district_scraper()
    exit(0 if success else 1)

