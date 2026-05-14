import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_platform(platform_name, max_events=3):
    """Test a single platform"""
    print(f"\n{'='*60}")
    print(f"Testing {platform_name}...")
    print('='*60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scrape",
            json={
                "location": "Hyderabad",
                "max_events": max_events,
                "platforms": [platform_name]
            },
            timeout=180
        )
        
        if response.status_code == 200:
            events = response.json()
            print(f"[OK] {platform_name}: Found {len(events)} events")
            
            for i, event in enumerate(events[:2], 1):
                print(f"\n  Event {i}:")
                print(f"    Name: {event.get('event_name', 'N/A')}")
                print(f"    Date: {event.get('event_date', 'N/A')}")
                print(f"    Price: {event.get('price', 'N/A')}")
                print(f"    Venue: {event.get('venue', 'N/A')}")
                print(f"    Location: {event.get('city', 'N/A')}")
                print(f"    URL: {event.get('event_url', 'N/A')[:80]}...")
                print(f"    Platform: {event.get('platform', 'N/A')}")
            
            return len(events)
        else:
            print(f"[ERROR] Status: {response.status_code}")
            print(response.text)
            return 0
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        return 0

if __name__ == "__main__":
    platforms = [
        "Mera Events",
        "District",
        "Skillbox",
        "Swiggy Scenes",
        "Sort My Scene",
        "Urbanaut"
    ]
    
    results = {}
    for platform in platforms:
        count = test_platform(platform)
        results[platform] = count
        time.sleep(2)  # Be nice to servers
    
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    for platform, count in results.items():
        status = "[OK]" if count > 0 else "[FAIL]"
        print(f"{status} {platform}: {count} events")
