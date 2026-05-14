"""
QUICK STATUS CHECK - Show what each platform returns
Read existing JSON files and display field coverage
"""

import json
import os

def show_platform_status(json_file, platform_name):
    """Show what fields a platform returns"""
    
    if not os.path.exists(json_file):
        print(f"\n{platform_name}: No test file found")
        return
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            events = json.load(f)
        
        if not events:
            print(f"\n{platform_name}: 0 events in file")
            return
        
        # Get first event to check fields
        first = events[0]
        event_count = len(events)
        
        fields_in_data = {
            'event_name': 'event_name' in first and bool(first.get('event_name')),
            'price': 'price' in first and first.get('price') is not None,
            'venue': 'venue' in first and bool(first.get('venue')),
            'event_date': 'event_date' in first and bool(first.get('event_date')),
            'event_time': 'event_time' in first and bool(first.get('event_time')),
            'event_url': 'event_url' in first and bool(first.get('event_url')),
            'description': 'description' in first and bool(first.get('description')),
        }
        
        present_fields = [f for f, present in fields_in_data.items() if present]
        missing_fields = [f for f, present in fields_in_data.items() if not present]
        
        print(f"\n{platform_name}:")
        print(f"  Events: {event_count}")
        print(f"  Present: {', '.join(present_fields) if present_fields else 'NONE'}")
        if missing_fields:
            print(f"  Missing: {', '.join(missing_fields)}")
        
        # Show sample
        print(f"  Sample event:")
        print(f"    Name: {first.get('event_name', 'N/A')[:50]}")
        print(f"    Venue: {first.get('venue', 'N/A')[:50]}")
        print(f"    Date: {first.get('event_date', 'N/A')}")
        print(f"    Time: {first.get('event_time', 'N/A')}")
        print(f"    Price: {first.get('price', 'N/A')}")
        
    except Exception as e:
        print(f"\n{platform_name}: Error reading file - {str(e)[:50]}")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CURRENT PLATFORM STATUS - Fields check")
    print("="*80)
    
    # Check existing test files
    show_platform_status("bookmyshow_test_output.json", "BookMyShow")
    
    print("\n" + "="*80)
    print("Note: District, Meetup, Urbanaut need to be tested")
    print("="*80 + "\n")
