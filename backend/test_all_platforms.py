import requests
import json

# Request all platforms
response = requests.post(
    "http://localhost:8000/api/scrape",
    json={
        "location": "Hyderabad",
        "max_events": 20,
        "platforms": ["All Platforms"]
    },
    timeout=300
)

events = response.json()
print(f"\n{'='*70}")
print(f"TOTAL EVENTS COLLECTED: {len(events)}")
print(f"{'='*70}\n")

# Group by platform
by_platform = {}
for e in events:
    p = e.get("platform", "Unknown")
    if p not in by_platform:
        by_platform[p] = []
    by_platform[p].append(e)

print("Events by platform:")
for platform, items in sorted(by_platform.items()):
    print(f"  {platform}: {len(items)} events")

# Show all events with key details
print(f"\n{'='*70}")
print("All Events Details:")
print(f"{'='*70}\n")

for i, event in enumerate(events, 1):
    print(f"{i}. {event.get('event_name', 'N/A')}")
    print(f"   Date: {event.get('event_date', 'N/A')}")
    print(f"   Price: INR {event.get('price', 'N/A')}")
    print(f"   Venue: {event.get('venue', 'N/A')}")
    print(f"   Location: {event.get('city', 'N/A')}")
    print(f"   Platform: {event.get('platform', 'N/A')}")
    print(f"   URL: {event.get('event_url', 'N/A')[:70]}...")
    print()

# Check for duplicates
urls = [e.get('event_url') for e in events]
unique_urls = set(urls)
duplicates = len(urls) - len(unique_urls)
print(f"\nDuplicate check: {len(urls)} total URLs, {len(unique_urls)} unique")
if duplicates > 0:
    print(f"WARNING: {duplicates} duplicate URLs found!")
else:
    print("Good: No duplicate URLs")

print("\nDone! All events verified.")
