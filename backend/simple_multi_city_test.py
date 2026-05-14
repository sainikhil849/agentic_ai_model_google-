"""
SIMPLE MULTI-CITY TEST - BookMyShow, District, Meetup, Urbanaut
Test 5 events from each platform
"""

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import BookMyShowAgent, DistrictAgent, MeetupAgent, UrbanautAgent
import json

def test_platform_city(platform_name, agent_class, city):
    """Test a platform in one city"""
    
    print(f"[{platform_name}] Testing {city}...", end=" ", flush=True)
    try:
        agent = agent_class()
        events = agent.run_sync_extraction(
            location=city,
            target_count=5,
            max_price=None
        )
        
        # Check what fields are present
        if events:
            sample = events[0]
            has_name = 'event_name' in sample and sample['event_name']
            has_price = 'price' in sample and sample['price'] is not None
            has_venue = 'venue' in sample and sample['venue']
            has_date = 'event_date' in sample and sample['event_date']
            has_time = 'event_time' in sample and sample['event_time']
            has_url = 'event_url' in sample and sample['event_url']
            has_desc = 'description' in sample and sample['description']
            
            fields = []
            if has_name: fields.append("name")
            if has_price: fields.append("price")
            if has_venue: fields.append("venue")
            if has_date: fields.append("date")
            if has_time: fields.append("time")
            if has_url: fields.append("url")
            if has_desc: fields.append("desc")
            
            print(f"Got {len(events)} events | Fields: {','.join(fields) if fields else 'NONE'}")
            return {
                'platform': platform_name,
                'city': city,
                'count': len(events),
                'events': events[:5]
            }
        else:
            print(f"Got 0 events")
            return None
            
    except Exception as e:
        print(f"ERROR: {str(e)[:40]}")
        return None

if __name__ == "__main__":
    cities = ["Hyderabad", "Bangalore", "Delhi"]
    platforms = [
        ("BookMyShow", BookMyShowAgent),
        ("District", DistrictAgent),
        ("Meetup", MeetupAgent),
        ("Urbanaut", UrbanautAgent),
    ]
    
    print("\n" + "="*100)
    print("MULTI-CITY PLATFORM TEST - 5 events per platform per city")
    print("="*100 + "\n")
    
    results = []
    
    for platform_name, agent_class in platforms:
        print(f"\n{platform_name}:")
        for city in cities:
            result = test_platform_city(platform_name, agent_class, city)
            if result:
                results.append(result)
    
    # Save results
    with open("multi_city_test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*100}")
    print(f"Test complete. Results saved to multi_city_test_results.json")
    print(f"{'='*100}\n")
