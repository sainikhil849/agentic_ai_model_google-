"""
BOOKMYSHOW ONLY - Test with 10 events
Shows all expected fields: event_name, price, description, event_url, venue_location, date, time
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import BookMyShowAgent
import json

def display_events(events):
    """Display 10 BookMyShow events with all fields"""
    
    print("\n" + "="*130)
    print(f"BOOKMYSHOW - {len(events)} EVENTS TEST")
    print("="*130)
    
    expected_fields = {
        'event_name': 'Event Name',
        'price': 'Price',
        'description': 'Description',
        'event_url': 'Event URL',
        'venue': 'Venue Location',
        'event_date': 'Event Date',
        'event_time': 'Event Time',
    }
    
    print(f"\nExpected Fields: {list(expected_fields.values())}\n")
    
    missing_counts = {field: 0 for field in expected_fields.keys()}
    
    for idx, event in enumerate(events, 1):
        print(f"\n{'─'*130}")
        print(f"EVENT #{idx}")
        print(f"{'─'*130}")
        
        for field, label in expected_fields.items():
            value = event.get(field, "❌ MISSING")
            
            # Check if field is present and not empty
            if field not in event or not event[field]:
                missing_counts[field] += 1
                status = "❌"
            else:
                status = "✓"
            
            # Truncate long values
            if isinstance(value, str) and len(value) > 80:
                value = value[:77] + "..."
            
            print(f"{status} {label:<20}: {value}")
    
    # Summary
    print(f"\n{'='*130}")
    print("FIELD COVERAGE SUMMARY")
    print(f"{'='*130}")
    
    for field, label in expected_fields.items():
        count = len(events) - missing_counts[field]
        percentage = (count / len(events) * 100) if events else 0
        status = "✓" if missing_counts[field] == 0 else "⚠"
        print(f"{status} {label:<20}: {count}/{len(events)} events ({percentage:.0f}%)")
    
    print(f"{'='*130}\n")

if __name__ == "__main__":
    print("\n" + "="*130)
    print("TESTING BOOKMYSHOW - Field Coverage with 10 Events")
    print("="*130)
    
    try:
        agent = BookMyShowAgent()
        events = agent.run_sync_extraction(
            location="Hyderabad",
            target_count=10,
            max_price=None
        )
        
        if events:
            display_events(events)
            
            # Save results
            with open("bookmyshow_test_output.json", "w", encoding="utf-8") as f:
                json.dump(events[:10], f, indent=2, ensure_ascii=False)
            print("✓ Results saved to: bookmyshow_test_output.json")
        else:
            print("\n❌ BookMyShow returned 0 events")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
