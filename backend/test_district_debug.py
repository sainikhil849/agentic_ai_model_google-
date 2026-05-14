#!/usr/bin/env python3
"""
Debug script to test District scraping with Hyderabad location selection
"""
import sys
import logging
sys.path.insert(0, '/c/Users/saini/OneDrive/Desktop/codes/New folder/backend')

logging.basicConfig(level=logging.DEBUG)

from agents.platforms import DistrictAgent

print("\n" + "="*70)
print("DISTRICT DEBUG TEST - Hyderabad Location")
print("="*70 + "\n")

agent = DistrictAgent()

try:
    print("[1/2] Scraping District with Hyderabad location (target: 3 events)...")
    events = agent.scrape(location="Hyderabad", target_count=3, max_price=None)
    print(f"\n✓ Returned {len(events)} events\n")
    
    if events:
        print("Events returned:")
        for i, event in enumerate(events[:3], 1):
            print(f"\n  Event {i}:")
            print(f"    Name: {event.get('name', 'N/A')[:60]}")
            print(f"    Location: {event.get('location', 'N/A')}")
            print(f"    Venue: {event.get('venue', 'N/A')[:50]}")
            print(f"    Platform: {event.get('platform', 'N/A')}")
    else:
        print("⚠ No events returned - this is the problem!")
        print("  This means location validation is blocking all events.")
        
except Exception as e:
    print(f"\n✗ ERROR during scraping: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70 + "\n")
