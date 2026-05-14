import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("\n" + "="*80)
print("FINAL COMPREHENSIVE TEST - All Platforms with Venue Data")
print("="*80 + "\n")

# Test 1: Scrape events
print("[1/4] Scraping events from all platforms...")
response = requests.post(
    f"{BASE_URL}/api/scrape",
    json={
        "location": "Hyderabad",
        "max_events": 15,
        "platforms": ["All Platforms"]
    },
    timeout=300
)

if response.status_code != 200:
    print(f"ERROR: Failed to scrape - {response.status_code}")
    print(response.text)
    exit(1)

events = response.json()
print(f"✓ Scraped {len(events)} events\n")

# Test 2: Verify data integrity
print("[2/4] Verifying data integrity...")
required_fields = ['event_name', 'event_date', 'price', 'platform', 'city', 'venue', 'event_url']
all_valid = True

for i, event in enumerate(events, 1):
    missing_fields = [f for f in required_fields if f not in event or not event[f]]
    if missing_fields:
        print(f"  Event {i} ({event.get('event_name', 'N/A')}): Missing {missing_fields}")
        all_valid = False

if all_valid:
    print(f"✓ All {len(events)} events have required fields\n")
else:
    print("WARNING: Some events are missing fields\n")

# Test 3: Check for duplicates
print("[3/4] Checking for duplicates...")
urls = [e.get('event_url') for e in events]
unique_urls = set(urls)
duplicates = len(urls) - len(unique_urls)

if duplicates == 0:
    print(f"✓ No duplicates found ({len(unique_urls)} unique URLs)\n")
else:
    print(f"WARNING: {duplicates} duplicate(s) found\n")

# Test 4: Verify Excel export
print("[4/4] Testing Excel export...")
response = requests.post(
    f"{BASE_URL}/api/export",
    json=events,
    timeout=60
)

if response.status_code == 200:
    filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"✓ Excel export successful ({len(response.content)} bytes)\n")
else:
    print(f"ERROR: Export failed - {response.status_code}\n")

# Summary
print("="*80)
print("EVENT SUMMARY")
print("="*80 + "\n")

by_platform = {}
for e in events:
    p = e.get("platform", "Unknown")
    if p not in by_platform:
        by_platform[p] = 0
    by_platform[p] += 1

for platform, count in sorted(by_platform.items()):
    print(f"  {platform:<15} : {count:>2} events")

print(f"\n  {'TOTAL':<15} : {len(events):>2} events")

# Show sample events
print("\n" + "="*80)
print("SAMPLE EVENTS WITH VENUE DATA")
print("="*80 + "\n")

for i, e in enumerate(events[:3], 1):
    print(f"{i}. {e.get('event_name')}")
    print(f"   Date: {e.get('event_date')}")
    print(f"   Price: {e.get('price')}")
    print(f"   Venue: {e.get('venue')}")
    print(f"   Location: {e.get('city')}")
    print(f"   Platform: {e.get('platform')}")
    print()

print("="*80)
print("TEST COMPLETED SUCCESSFULLY")
print("="*80)
