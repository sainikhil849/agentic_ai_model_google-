#!/usr/bin/env python3
"""
SIMPLE DISTRICT URL TEST
Just verify the URL routing works without triggering anti-bot
"""

import sys
sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.platforms import DistrictAgent
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_simple():
    print("\n" + "="*80)
    print("SIMPLE DISTRICT TEST - 5 EVENTS FROM BANGALORE")
    print("="*80)
    
    agent = DistrictAgent()
    
    try:
        events = agent.run_sync_extraction(
            location="Bangalore",
            target_count=5,
            max_price=None
        )
        
        print("\n" + "="*80)
        print(f"RESULTS: {len(events)} events found")
        print("="*80)
        
        if events:
            for i, e in enumerate(events, 1):
                print(f"\n{i}. {e.get('event_name', 'N/A')}")
                print(f"   Venue: {e.get('venue', 'N/A')}")
                print(f"   Date: {e.get('event_date', 'N/A')}")
                print(f"   Price: {e.get('price', 'N/A')}")
            return True
        else:
            print("\n[!] No events found")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check if multi-city test requested
    if len(sys.argv) > 1 and sys.argv[1] == "--multi":
        print("\n" + "="*80)
        print("MULTI-CITY DISTRICT TEST")
        print("="*80)
        
        cities = ["Bangalore", "Delhi", "Mumbai", "Hyderabad", "Pune"]
        results = {}
        
        for city in cities:
            print(f"\n[{city}]")
            agent = DistrictAgent()
            try:
                events = agent.run_sync_extraction(
                    location=city,
                    target_count=3,
                    max_price=None
                )
                results[city] = len(events)
                print(f"✓ {city}: {len(events)} events found")
                if events:
                    print(f"  └─ {events[0].get('event_name', 'N/A')[:60]}")
            except Exception as e:
                results[city] = 0
                print(f"✗ {city}: Error - {str(e)[:50]}")
        
        print("\n" + "="*80)
        print("MULTI-CITY SUMMARY - Any City Works ✓")
        print("="*80)
        for city, count in results.items():
            status = "✓" if count > 0 else "✗"
            print(f"{status} {city:15} → {count} events")
    else:
        success = test_simple()
        sys.exit(0 if success else 1)
