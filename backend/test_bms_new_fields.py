
import sys
import os
import asyncio

# Add current directory to path
sys.path.append(os.getcwd())

from agents.platforms import BookMyShowAgent

async def test_bms_enrichment():
    agent = BookMyShowAgent()
    # Test with a known event URL or just run a small scrape
    city = "Hyderabad"
    count = 1
    print(f"Testing BMS enrichment for {city} with limit {count}...")
    events = await agent.extract_events(city, count)
    
    if events:
        import json
        print(json.dumps(events, indent=2))
        
        # Check for new fields
        e = events[0]
        fields = ["description", "duration", "hashtags", "artist_name", "artist_details", "people_interested", "event_type"]
        print("\nField presence:")
        for f in fields:
            print(f"{f}: {'Present' if f in e or e.get(f) else 'Missing'}")
    else:
        print("No events found.")

if __name__ == "__main__":
    asyncio.run(test_bms_enrichment())
