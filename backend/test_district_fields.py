"""
Test District Scraper - Check if all expected fields are present
Tests: event_name, price, description, event_url, venue_location, date, time
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.scrapers import scrape_district
import json

def display_events(events):
    """Display events in a formatted way showing all fields"""
    
    print("\n" + "="*100)
    print(f"DISTRICT SCRAPER - TESTING {len(events)} EVENTS")
    print("="*100)
    
    required_fields = [
        'event_name',
        'price',
        'description',
        'event_url',
        'venue_location',
        'event_date',
        'event_time'
    ]
    
    print(f"\nExpected Fields: {required_fields}\n")
    
    missing_fields_count = {field: 0 for field in required_fields}
    
    for idx, event in enumerate(events, 1):
        print(f"\n{'─'*100}")
        print(f"EVENT #{idx}")
        print(f"{'─'*100}")
        
        for field in required_fields:
            value = event.get(field, "❌ MISSING")
            status = "✓" if field in event and event[field] else "❌"
            
            if field not in event or not event[field]:
                missing_fields_count[field] += 1
            
            if field == 'description':
                # Truncate long descriptions
                if isinstance(value, str) and len(value) > 100:
                    value = value[:100] + "..."
            
            print(f"{status} {field.upper():<20}: {value}")
        
        # Show other fields if present
        other_fields = [k for k in event.keys() if k not in required_fields]
        if other_fields:
            print(f"\nOther fields present: {other_fields}")
    
    # Summary
    print(f"\n{'='*100}")
    print("FIELD COVERAGE SUMMARY")
    print(f"{'='*100}")
    
    for field in required_fields:
        count = len(events) - missing_fields_count[field]
        percentage = (count / len(events) * 100) if events else 0
        status = "✓" if missing_fields_count[field] == 0 else "⚠"
        print(f"{status} {field.upper():<20}: {count}/{len(events)} events ({percentage:.0f}%)")
    
    print(f"{'='*100}\n")

if __name__ == "__main__":
    print("Starting District Scraper Test with 10 events...\n")
    
    try:
        events = scrape_district("Hyderabad", max_events=10)
        
        if events:
            display_events(events)
            
            # Save to JSON for inspection
            with open("district_test_output.json", "w", encoding="utf-8") as f:
                json.dump(events, f, indent=2, ensure_ascii=False)
            print("✓ Full results saved to: district_test_output.json")
        else:
            print("❌ No events scraped. District scraper returned empty list.")
    
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        import traceback
        traceback.print_exc()
