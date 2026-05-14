#!/usr/bin/env python3
"""
QUICK TEST: District scraper for Bangalore - 5 events
Focus on SPEED and DEBUGGING city forcing
"""

import sys
import logging
import time
from datetime import datetime

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from agents.platforms import DistrictAgent

# Enhanced logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*80)
    print("DISTRICT SCRAPER - BANGALORE - 5 EVENTS TEST")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Focus: City forcing verification + Fast extraction")
    print("="*80 + "\n")
    
    agent = DistrictAgent()
    start_time = time.time()
    
    try:
        print("[*] Scraping District for Bangalore (max 5 events)...")
        
        events = agent.run_sync_extraction(
            location="Bangalore",
            target_count=5,
            max_price=None
        )
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        print(f"[OK] Completed in {elapsed:.1f} seconds")
        print(f"[OK] Events Found: {len(events)}")
        print("="*80)
        
        if events:
            print("\n[EVENTS EXTRACTED]:")
            print("-" * 80)
            for i, ev in enumerate(events, 1):
                print(f"\n{i}. {ev.get('event_name', 'N/A')}")
                print(f"   City: {ev.get('city', 'N/A')} | Venue: {ev.get('venue', 'N/A')}")
                print(f"   Date: {ev.get('event_date', 'N/A')} | Time: {ev.get('event_time', 'N/A')}")
                print(f"   Price: {ev.get('price', 'N/A')}")
                print(f"   Link: {ev.get('event_link', 'N/A')[:65]}...")
            print("\n" + "-" * 80)
            return True
        else:
            print("\n[!] NO EVENTS FOUND")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n[ERROR] Test failed")
        print(f"Error: {e}")
        print(f"Time: {elapsed:.1f} seconds")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
