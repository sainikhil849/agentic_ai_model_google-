import asyncio
import sys
import json

# Critical fix for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from pipeline_controller import PipelineController

async def main():
    pipeline = PipelineController()
    
    print("\n" + "="*80)
    print("TESTING BANGALORE SCRAPE")
    print("="*80 + "\n")
    
    results = await pipeline.run_pipeline(
        location="Bangalore, India",
        max_events=5,
        target_platforms=["BookMyShow", "District"],
        category=None,
        max_price=None
    )
    
    print(f"\n✓ Scrape completed. Found {len(results)} events.\n")
    
    # Check for Bangalore-specific URLs in District
    print("\nCHECKING FOR BANGALORE DISTRICT URL:")
    for event in results:
        if event.get('platform') == 'District':
            url = event.get('url', 'N/A')
            print(f"  District URL: {url}")
            if 'bengaluru' in url.lower():
                print("  ✓ URL contains 'bengaluru' for Bangalore location")
            else:
                print(f"  ✗ URL does NOT contain 'bengaluru': {url}")
    
    print("\nCHECKING BOOKMYSHOW EVENTS:")
    bms_events = [e for e in results if e.get('platform') == 'BookMyShow']
    print(f"  Found {len(bms_events)} BookMyShow events\n")
    
    for idx, event in enumerate(bms_events[:3], 1):
        print(f"  Event {idx}:")
        print(f"    Title: {event.get('title', 'N/A')}")
        venue = event.get('venue', 'N/A')
        if isinstance(venue, dict):
            venue_name = venue.get('name', 'Not specified')
        else:
            venue_name = venue if venue else 'Not specified'
        print(f"    Venue: {venue_name}")
        price = event.get('price', 0)
        if isinstance(price, dict):
            price = price.get('min', 0) or price.get('price', 0)
        print(f"    Price: {price}")
        print()
    
    # Full results in JSON
    print("\nFULL RESULTS (first 2 events):")
    print(json.dumps(results[:2], indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    asyncio.run(main())
