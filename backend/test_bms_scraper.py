import asyncio
import sys
import os
from pathlib import Path

# Critical fix for Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Add current directory to path
sys.path.insert(0, str(Path.cwd()))

from pipeline_controller import PipelineController

async def main():
    pipeline = PipelineController()
    
    print("\n" + "="*80)
    print("BOOKMYSHOW ONLY - FOCUSED SCRAPER TEST")
    print("="*80 + "\n")
    
    print("📍 Location: Bangalore")
    print("🎯 Target: 10 events")
    print("⏳ Scraping started...\n")
    
    results = await pipeline.run_pipeline(
        location="Bangalore, India",
        max_events=10,
        target_platforms=["BookMyShow"],
        category=None,
        max_price=None
    )
    
    print(f"\n✓ Scrape completed. Found {len(results)} BookMyShow events.\n")
    
    # Show venue and price extraction results
    print("\n" + "="*80)
    print("VENUE & PRICE EXTRACTION RESULTS")
    print("="*80 + "\n")
    
    for idx, event in enumerate(results, 1):
        print(f"[{idx}] {event.get('title', 'N/A')}")
        
        # Venue extraction
        venue = event.get('venue', 'N/A')
        if isinstance(venue, dict):
            venue_name = venue.get('name', 'Not specified')
            print(f"    Venue: {venue_name}")
        else:
            venue_name = venue if venue else 'Not specified'
            print(f"    Venue: {venue_name}")
        
        # Price extraction
        price = event.get('price', 0)
        if isinstance(price, dict):
            price_val = price.get('min', 0) or price.get('price', 0)
        else:
            price_val = price if price else 0
        print(f"    Price: ₹{price_val}")
        print()
    
    # Check for Excel file
    excel_files = list(Path.cwd().glob("*.xlsx"))
    print("\n" + "="*80)
    print("EXCEL OUTPUT")
    print("="*80 + "\n")
    if excel_files:
        print(f"✓ Excel files found: {len(excel_files)}")
        for excel_file in excel_files:
            print(f"  - {excel_file.name}")
            print(f"    Size: {excel_file.stat().st_size} bytes")
            print(f"    Modified: {excel_file.stat().st_mtime}")
    else:
        print("✗ No Excel files found in current directory")
    
    print()

if __name__ == "__main__":
    asyncio.run(main())
