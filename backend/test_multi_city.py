"""
MULTI-CITY TEST - BookMyShow, District, Meetup, Urbanaut
Test 5 events from each platform across multiple cities
Shows all required fields: event_name, price, description, event_url, venue, event_date, event_time
"""

import sys
import asyncio
import time
import gc

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import BookMyShowAgent, DistrictAgent, MeetupAgent, UrbanautAgent
import json

def test_platform(platform_name, agent_class, cities, events_per_city=5):
    """Test a platform across multiple cities"""
    
    print(f"\n{'='*120}")
    print(f"TESTING {platform_name.upper()}")
    print(f"{'='*120}")
    
    all_results = {}
    
    for city_idx, city in enumerate(cities):
        print(f"\n[{city}]")
        try:
            agent = agent_class()
            events = agent.run_sync_extraction(
                location=city,
                target_count=events_per_city,
                max_price=None
            )
            
            # Force garbage collection after each extraction to clean up browser resources
            del agent
            gc.collect()
            
            # Add delay between city extractions to let system recover
            if city_idx < len(cities) - 1:
                time.sleep(1.5)
            
            count = len(events)
            print(f"   OK: Got {count}/{events_per_city} events")
            
            # Check field coverage for this city
            if events:
                fields_present = {
                    'event_name': sum(1 for e in events if 'event_name' in e and e['event_name']),
                    'price': sum(1 for e in events if 'price' in e and e['price'] is not None),
                    'venue': sum(1 for e in events if 'venue' in e and e['venue']),
                    'event_date': sum(1 for e in events if 'event_date' in e and e['event_date']),
                    'event_time': sum(1 for e in events if 'event_time' in e and e['event_time']),
                    'event_url': sum(1 for e in events if 'event_url' in e and e['event_url']),
                    'description': sum(1 for e in events if 'description' in e and e['description']),
                }
                
                print(f"   Fields: ", end="")
                for field, cnt in fields_present.items():
                    if cnt == count:
                        print(f"[OK]{field.split('_')[0]}", end=" ")
                    elif cnt > 0:
                        print(f"[PARTIAL]{field.split('_')[0]}({cnt})", end=" ")
                print()
                
                all_results[city] = events
        
        except Exception as e:
            print(f"   ERROR: {str(e)[:60]}")
    
    return all_results

if __name__ == "__main__":
    cities = ["Hyderabad", "Bangalore", "Delhi"]
    
    print("\n" + "="*120)
    print("MULTI-CITY EVENT SCRAPER TEST")
    print(f"Cities: {', '.join(cities)} | Events per city: 5")
    print("="*120)
    
    results = {}
    
    # Test each platform
    results['bookmyshow'] = test_platform("BookMyShow", BookMyShowAgent, cities, 5)
    gc.collect()
    time.sleep(2)
    
    results['district'] = test_platform("District", DistrictAgent, cities, 5)
    gc.collect()
    time.sleep(2)
    
    results['meetup'] = test_platform("Meetup", MeetupAgent, cities, 5)
    gc.collect()
    time.sleep(2)
    
    results['urbanaut'] = test_platform("Urbanaut", UrbanautAgent, cities, 5)
    
    # Save results
    with open("multi_city_results.json", "w", encoding="utf-8") as f:
        # Convert to serializable format
        output = {}
        for platform, city_data in results.items():
            output[platform] = {}
            for city, events in city_data.items():
                output[platform][city] = events[:5]  # Keep only first 5
        
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*120}")
    print("RESULTS: saved to multi_city_results.json")
    print(f"{'='*120}\n")
