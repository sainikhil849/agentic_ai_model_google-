import requests

response = requests.post(
    "http://localhost:8000/api/scrape",
    json={"location": "Hyderabad", "max_events": 3, "platforms": ["Skillbox"]},
    timeout=180
)

events = response.json()
print(f"Skillbox found: {len(events)} events\n")
for i, e in enumerate(events[:2], 1):
    print(f"Event {i}:")
    print(f"  Name: {e.get('event_name')}")
    print(f"  Date: {e.get('event_date')}")
    print(f"  Price: {e.get('price')}")
    print(f"  Venue: {e.get('venue')}")
    print(f"  URL: {e.get('event_url')[:60]}...\n")
