import asyncio
import sys
import json
import logging

# Setup logging to see more details
logging.basicConfig(level=logging.INFO)

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from pipeline_controller import PipelineController

async def main():
    pipeline = PipelineController()
    
    print("\n" + "="*80)
    print("DIRECT BANGALORE TEST - Checking URL, Venue Names, and Prices")
    print("="*80 + "\n")
    
    results = await pipeline.run_pipeline(
        location="Bangalore, India",
        max_events=3,
        target_platforms=["BookMyShow", "District"],
        category=None,
        max_price=None
    )
    
    print("\n" + "="*80)
    print(f"✓ SCRAPE COMPLETED - Found {len(results)} events")
    print("="*80)
    
    # Test 1: District URL
    print("\n[TEST 1] DISTRICT URL FOR BANGALORE:")
    district_found = False
    for event in results:
        if event.get('platform') == 'District':
            district_found = True
            url = event.get('url', 'N/A')
            if 'bengaluru' in url.lower():
                print(f"✓ PASS - URL contains bengaluru: {url}")
            else:
                print(f"✗ FAIL - URL missing bengaluru: {url}")
    if not district_found:
        print("✗ FAIL - No District events found")
    
    # Test 2 & 3: BookMyShow venue and prices
    print("\n[TEST 2] BOOKMYSHOW VENUE NAMES:")
    print("[TEST 3] BOOKMYSHOW PRICES:")
    bms_events = [e for e in results if e.get('platform') == 'BookMyShow']
    
    if bms_events:
        for idx, event in enumerate(bms_events[:3], 1):
            venue = event.get('venue', {})
            if isinstance(venue, dict):
                venue_name = venue.get('name', 'Not specified')
            else:
                venue_name = venue if venue else 'Not specified'
            
            price = event.get('price', 0)
            if isinstance(price, dict):
                price_val = price.get('min', 0) or price.get('price', 0)
            else:
                price_val = price
            
            print(f"\n  Event {idx}: {event.get('title', 'N/A')}")
            if venue_name == 'Not specified':
                print(f"    ✗ Venue: 'Not specified'")
            else:
                print(f"    ✓ Venue: {venue_name}")
            
            if price_val == 0:
                print(f"    ✗ Price: {price_val} (should be actual price)")
            else:
                print(f"    ✓ Price: {price_val}")
    else:
        print("  ✗ FAIL - No BookMyShow events found")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())
