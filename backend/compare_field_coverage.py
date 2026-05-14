"""
Compare DISTRICT vs BOOKMYSHOW - Field coverage test with real agents
Tests all expected fields: event_name, price, description, event_url, venue_location, date, time
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import DistrictAgent, BookMyShowAgent
import json

def display_comparison(bms_events, district_events):
    """Display side-by-side comparison of field coverage"""
    
    print("\n" + "="*140)
    print("FIELD COVERAGE COMPARISON - BOOKMYSHOW vs DISTRICT")
    print("="*140)
    
    expected_fields = [
        'name',  # event_name
        'price',
        'description',
        'event_link',  # event_url
        'venue',  # venue_location
        'date',  # event_date
        'event_time',  # event_time
    ]
    
    print(f"\n{'FIELD':<20} {'BOOKMYSHOW':<60} {'DISTRICT':<60}")
    print("─"*140)
    
    for field in expected_fields:
        bms_count = sum(1 for e in bms_events if field in e and e[field])
        dist_count = sum(1 for e in district_events if field in e and e[field])
        
        bms_pct = (bms_count / len(bms_events) * 100) if bms_events else 0
        dist_pct = (dist_count / len(district_events) * 100) if district_events else 0
        
        bms_str = f"{bms_count}/{len(bms_events)} ({bms_pct:.0f}%)" if bms_events else "N/A"
        dist_str = f"{dist_count}/{len(district_events)} ({dist_pct:.0f}%)" if district_events else "N/A"
        
        print(f"{field:<20} {bms_str:<60} {dist_str:<60}")
    
    print("="*140 + "\n")

def display_sample_events(events, platform, count=3):
    """Display sample events"""
    
    print(f"\n{'─'*100}")
    print(f"SAMPLE {platform.upper()} EVENTS (showing first {count})")
    print(f"{'─'*100}\n")
    
    for idx, event in enumerate(events[:count], 1):
        print(f"EVENT #{idx}")
        print(f"  Name:        {event.get('name', 'N/A')[:60]}")
        print(f"  Price:       {event.get('price', 'N/A')}")
        print(f"  Venue:       {event.get('venue', 'N/A')[:60]}")
        print(f"  Date:        {event.get('date', 'N/A')}")
        print(f"  Time:        {event.get('event_time', 'N/A')}")
        print(f"  Description: {str(event.get('description', 'N/A'))[:50]}...")
        print(f"  URL:         {event.get('event_link', 'N/A')[:60]}")
        print()

if __name__ == "__main__":
    location = "Hyderabad"
    max_events = 10
    
    print(f"\n{'='*140}")
    print(f"TESTING DISTRICT vs BOOKMYSHOW - Field Coverage Analysis")
    print(f"Location: {location} | Max Events: {max_events}")
    print(f"{'='*140}\n")
    
    bms_events = []
    district_events = []
    
    # Test BookMyShow
    print("📍 Starting BookMyShow extraction...\n")
    try:
        bms_agent = BookMyShowAgent()
        bms_events = bms_agent.run_sync_extraction(
            location=location,
            target_count=max_events,
            max_price=None
        )
        print(f"\n✓ BookMyShow: Extracted {len(bms_events)} events\n")
    except Exception as e:
        print(f"\n❌ BookMyShow Error: {str(e)[:100]}\n")
    
    # Test District
    print("📍 Starting District extraction...\n")
    try:
        district_agent = DistrictAgent()
        district_events = district_agent.run_sync_extraction(
            location=location,
            target_count=max_events,
            max_price=None
        )
        print(f"\n✓ District: Extracted {len(district_events)} events\n")
    except Exception as e:
        print(f"\n❌ District Error: {str(e)[:100]}\n")
    
    # Display results
    if bms_events or district_events:
        display_comparison(bms_events, district_events)
        
        if bms_events:
            display_sample_events(bms_events, "bookmyshow", min(3, len(bms_events)))
        
        if district_events:
            display_sample_events(district_events, "district", min(3, len(district_events)))
        
        # Save full results
        results = {
            "bookmyshow": bms_events[:max_events],
            "district": district_events[:max_events],
            "summary": {
                "bookmyshow_count": len(bms_events),
                "district_count": len(district_events),
                "location": location
            }
        }
        
        with open("field_coverage_comparison.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("✓ Full results saved to: field_coverage_comparison.json")
    else:
        print("❌ No events extracted from either platform")
